#!/usr/bin/env python3
"""
Generate Cucumber automation skeletons from Jira test cases.

Required environment variables:
  JIRA_BASE_URL   Example: https://your-domain.atlassian.net
  JIRA_EMAIL      Jira user email
  JIRA_API_TOKEN  Jira API token or PAT
  JIRA_TEST_TYPE_FIELD  Optional Jira custom field id/name for Test Type
  JIRA_GHERKIN_FIELD    Optional Jira custom field id/name for Cucumber/Gherkin steps

Example:
  python tools/jira_automation_agent.py --project-key QA --dry-run
  python tools/jira_automation_agent.py --jql "project = QA AND labels = AutomationCandidate AND status = New"
"""

from __future__ import annotations

import argparse
import base64
from datetime import datetime
import json
import os
import re
import sys
import textwrap
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_LABEL = "AutomationCandidate"
DEFAULT_STATUS = "New"


@dataclass(frozen=True)
class JiraIssue:
    key: str
    summary: str
    description: str
    test_type: str
    gherkin: str


@dataclass(frozen=True)
class PlannedChange:
    issue_key: str
    action: str
    path: Path
    content: str
    reason: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def java_identifier(value: str, suffix: str = "") -> str:
    words = re.findall(r"[A-Za-z0-9]+", value)
    if not words:
        words = ["Generated"]
    first, *rest = words
    identifier = first[:1].lower() + first[1:] + "".join(word.capitalize() for word in rest)
    if identifier[:1].isdigit():
        identifier = f"test{identifier}"
    return f"{identifier}{suffix}"


def pascal_identifier(value: str, suffix: str = "") -> str:
    words = re.findall(r"[A-Za-z0-9]+", value)
    if not words:
        words = ["Generated"]
    identifier = "".join(word.capitalize() for word in words)
    if identifier[:1].isdigit():
        identifier = f"Test{identifier}"
    return f"{identifier}{suffix}"


def feature_filename(issue: JiraIssue) -> str:
    summary = re.sub(r"[^a-zA-Z0-9]+", "_", issue.summary.lower()).strip("_")
    summary = re.sub(r"_+", "_", summary)[:60] or "generated_test"
    return f"{issue.key.lower()}_{summary}.feature"


def step_class_name(issue: JiraIssue) -> str:
    return pascal_identifier(issue.key.replace("-", " ") + " " + issue.summary, "Steps")


def scenario_name(issue: JiraIssue) -> str:
    clean = re.sub(r"\s+", " ", issue.summary).strip()
    return clean or issue.key


def jira_auth_header(email: str, token: str) -> str:
    raw = f"{email}:{token}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def jira_search(
    base_url: str,
    email: str,
    token: str,
    jql: str,
    max_results: int,
    test_type_field: str | None,
    gherkin_field: str | None,
) -> list[JiraIssue]:
    fields = ["summary", "description"]
    fields.extend(field for field in [test_type_field, gherkin_field] if field)
    encoded_jql = urllib.parse.urlencode(
        {
            "jql": jql,
            "maxResults": str(max_results),
            "fields": ",".join(fields),
        }
    )
    url = f"{base_url.rstrip('/')}/rest/api/3/search?{encoded_jql}"
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": jira_auth_header(email, token),
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    return [
        JiraIssue(
            key=issue["key"],
            summary=issue.get("fields", {}).get("summary") or issue["key"],
            description=extract_description(issue.get("fields", {}).get("description")),
            test_type=extract_field_text(issue.get("fields", {}).get(test_type_field)) if test_type_field else "",
            gherkin=extract_field_text(issue.get("fields", {}).get(gherkin_field)) if gherkin_field else "",
        )
        for issue in payload.get("issues", [])
    ]


def extract_field_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return "\n".join(extract_field_text(item) for item in value if extract_field_text(item))
    if isinstance(value, dict):
        for key in ["value", "name", "displayName", "text"]:
            if value.get(key):
                return extract_field_text(value[key])
        return extract_description(value)
    return str(value)


def extract_description(description: object) -> str:
    if isinstance(description, str):
        return description
    if not isinstance(description, dict):
        return ""

    parts: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if node.get("type") == "text" and node.get("text"):
                parts.append(str(node["text"]))
            for child in node.get("content", []):
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(description)
    return " ".join(parts)


def load_sample_issue(path: Path) -> JiraIssue:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return JiraIssue(
        key=payload["key"],
        summary=payload["summary"],
        description=payload.get("description", ""),
        test_type=payload.get("testType", payload.get("test_type", "")),
        gherkin=payload.get("gherkin", ""),
    )


def build_jql(project_key: str | None, label: str, status: str, custom_jql: str | None) -> str:
    if custom_jql:
        return custom_jql

    clauses = [f'labels = "{label}"', f'status = "{status}"']
    if project_key:
        clauses.insert(0, f"project = {project_key}")
    return " AND ".join(clauses) + " ORDER BY updated DESC"


def gherkin_source(issue: JiraIssue) -> str:
    return (issue.gherkin or issue.description).strip()


def normalize_gherkin(issue: JiraIssue) -> str:
    source = gherkin_source(issue)
    if not source:
        source = textwrap.dedent(
            f"""\
            Scenario: {scenario_name(issue)}
              Given I launch the browser
              When I open the page for Jira test "{issue.key}"
              And I perform the test actions for "{issue.key}"
              Then I verify the expected result for "{issue.key}"
            """
        ).strip()

    has_feature = re.search(r"^\s*Feature\s*:", source, flags=re.IGNORECASE | re.MULTILINE)
    has_scenario = re.search(
        r"^\s*(Scenario|Scenario Outline|Example)\s*:",
        source,
        flags=re.IGNORECASE | re.MULTILINE,
    )

    if has_feature:
        return source.strip() + "\n"
    if has_scenario:
        return f"Feature: {scenario_name(issue)}\n\n{indent_gherkin_body(source.strip())}\n"
    return f"Feature: {scenario_name(issue)}\n\n  Scenario: {scenario_name(issue)}\n{indent_gherkin_body(source.strip())}\n"


def indent_gherkin_body(source: str) -> str:
    lines = []
    for line in source.splitlines():
        stripped = line.rstrip()
        if not stripped:
            lines.append("")
        elif re.match(r"^\s*(Given|When|Then|And|But|\*|Examples\s*:|\|)", stripped, flags=re.IGNORECASE):
            lines.append(f"    {stripped.lstrip()}")
        elif re.match(r"^\s*(Scenario|Scenario Outline|Example|Background|Rule)\s*:", stripped, flags=re.IGNORECASE):
            lines.append(f"  {stripped.lstrip()}")
        else:
            lines.append(f"    {stripped.lstrip()}")
    return "\n".join(lines)


def feature_content(issue: JiraIssue) -> str:
    header = [
        f"# Generated from Jira issue: {issue.key}",
        "# Generated by Jira Automation Agent. Re-run the agent to sync Jira Gherkin changes.",
        f"@AutomationCandidate @{issue.key}",
    ]
    return "\n".join(header) + "\n" + normalize_gherkin(issue)


def parse_gherkin_steps(issue: JiraIssue) -> list[tuple[str, str]]:
    steps: list[tuple[str, str]] = []
    keyword = "Given"
    for line in normalize_gherkin(issue).splitlines():
        match = re.match(r"^\s*(Given|When|Then|And|But)\s+(.+?)\s*$", line, flags=re.IGNORECASE)
        if not match:
            continue
        raw_keyword = match.group(1).capitalize()
        if raw_keyword in ["Given", "When", "Then"]:
            keyword = raw_keyword
        steps.append((keyword, match.group(2)))
    return steps


def java_step_pattern(step_text: str) -> str:
    return step_text.replace("\\", "\\\\").replace('"', '\\"')


def java_method_name(step_text: str, fallback: str) -> str:
    name = java_identifier(step_text)
    return name if name else fallback


def existing_step_patterns(root: Path) -> set[str]:
    patterns: set[str] = set()
    step_dir = root / "src" / "test" / "java" / "stepdefinitions"
    for path in step_dir.glob("*.java"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        patterns.update(re.findall(r"@(?:Given|When|Then|And|But)\(\"((?:\\.|[^\"])*)\"\)", text))
    return patterns


def java_string_unescape(value: str) -> str:
    return value.replace('\\"', '"').replace("\\\\", "\\")


def cucumber_expression_matches(expression: str, step_text: str) -> bool:
    expression = java_string_unescape(expression)
    pattern = re.escape(expression)
    replacements = {
        r"\{string\}": r'"[^"]*"',
        r"\{int\}": r"-?\d+",
        r"\{float\}": r"-?\d+(?:\.\d+)?",
        r"\{double\}": r"-?\d+(?:\.\d+)?",
        r"\{word\}": r"\S+",
    }
    for cucumber_type, regex in replacements.items():
        pattern = pattern.replace(cucumber_type, regex)
    return re.fullmatch(pattern, step_text) is not None


def has_existing_step(existing_patterns: set[str], step_text: str) -> bool:
    escaped_step = java_step_pattern(step_text)
    return any(
        pattern == escaped_step or cucumber_expression_matches(pattern, step_text)
        for pattern in existing_patterns
    )


def step_definition_content(issue: JiraIssue, root: Path, reuse_existing_steps: bool) -> str:
    class_name = step_class_name(issue)
    existing_patterns = existing_step_patterns(root)
    methods: list[str] = []
    imports: set[str] = set()
    used_methods: set[str] = set()

    for index, (keyword, step_text) in enumerate(parse_gherkin_steps(issue), start=1):
        pattern = java_step_pattern(step_text)
        if reuse_existing_steps and has_existing_step(existing_patterns, step_text):
            continue
        method_name = java_method_name(step_text, f"generatedStep{index}")
        while method_name in used_methods:
            method_name = f"{method_name}{index}"
        used_methods.add(method_name)
        imports.add(keyword)
        methods.append(
            textwrap.dedent(
                f"""\
                @{keyword}("{pattern}")
                public void {method_name}() {{
                    throw new io.cucumber.java.PendingException("Implement step from {issue.key}");
                }}
                """
            ).rstrip()
        )

    import_lines = "\n".join(f"import io.cucumber.java.en.{keyword};" for keyword in sorted(imports))
    method_block = textwrap.indent("\n\n".join(methods).rstrip(), "    ")
    if not method_block:
        method_block = "    // All Gherkin steps for this Jira test already have step definitions."

    return (
        f"package stepdefinitions;\n\n"
        f"// Generated from Jira issue: {issue.key}\n"
        f"// Generated by Jira Automation Agent. Re-run the agent to sync Jira Gherkin changes.\n"
        f"{import_lines}\n\n"
        f"public class {class_name} {{\n\n"
        f"{method_block}\n"
        f"}}\n"
    )


def is_generated_jira_file(path: Path, issue: JiraIssue) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    generated_markers = [
        f"Generated from Jira issue: {issue.key}",
        "Generated by Jira Automation Agent",
        f"Implement step from {issue.key}",
        "All Gherkin steps for this Jira test already have step definitions.",
    ]
    return any(marker in text for marker in generated_markers)


def plan_generated_file(issue: JiraIssue, path: Path, content: str, create_reason: str, update_reason: str) -> PlannedChange:
    if path.exists():
        existing = path.read_text(encoding="utf-8", errors="ignore")
        if existing == content:
            return PlannedChange(issue.key, "exists", path, content, "File already matches the latest generated content.")
        if is_generated_jira_file(path, issue):
            return PlannedChange(issue.key, "update", path, content, update_reason)
        return PlannedChange(issue.key, "exists", path, content, "File exists but does not look generated by the agent; no overwrite planned.")
    return PlannedChange(issue.key, "create", path, content, create_reason)


def plan_changes(issue: JiraIssue, root: Path, reuse_existing_steps: bool) -> list[PlannedChange]:
    feature_path = root / "src" / "test" / "resources" / "features" / feature_filename(issue)
    step_path = root / "src" / "test" / "java" / "stepdefinitions" / f"{step_class_name(issue)}.java"
    return [
        plan_generated_file(
            issue,
            feature_path,
            feature_content(issue),
            "Create Cucumber feature from Jira Gherkin.",
            "Sync generated Cucumber feature with the latest Jira Gherkin.",
        ),
        plan_generated_file(
            issue,
            step_path,
            step_definition_content(issue, root, reuse_existing_steps),
            "Create Java step definitions for the Jira Gherkin steps.",
            "Sync generated Java step definitions with the latest Jira Gherkin.",
        ),
    ]


def relative_path(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def print_change_plan(root: Path, jql: str, changes: list[PlannedChange], dry_run: bool) -> None:
    mode = "DRY RUN - no files will be changed" if dry_run else "Pending framework changes"
    print(f"\n{mode}")
    print(f"JQL: {jql}")
    for change in changes:
        print(f"- {change.action}: {relative_path(root, change.path)}")
        print(f"  Jira: {change.issue_key}")
        print(f"  Reason: {change.reason}")


def prompt_for_approval(changes: list[PlannedChange]) -> bool:
    print("\nThe agent will make the framework changes listed above and write an audit log under AIAudit.")
    answer = input("Proceed? Type yes to apply these changes: ").strip().lower()
    return answer in {"yes", "y"}


def apply_changes(changes: list[PlannedChange]) -> list[str]:
    results: list[str] = []
    for change in changes:
        if change.action == "exists":
            results.append(f"exists: {change.path}")
            continue
        change.path.parent.mkdir(parents=True, exist_ok=True)
        change.path.write_text(change.content, encoding="utf-8")
        results.append(f"{change.action}d: {change.path}")
    return results


def write_audit_log(root: Path, jql: str, changes: list[PlannedChange], results: list[str], dry_run: bool) -> Path:
    audit_dir = root / "AIAudit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audit_path = audit_dir / f"jira_automation_agent_{timestamp}.log"
    lines = [
        "Jira Automation Agent Audit",
        f"Timestamp: {datetime.now().isoformat(timespec='seconds')}",
        f"Mode: {'dry-run' if dry_run else 'applied'}",
        f"JQL: {jql}",
        "",
        "Planned changes:",
    ]
    for change in changes:
        lines.extend(
            [
                f"- Action: {change.action}",
                f"  Jira: {change.issue_key}",
                f"  Path: {relative_path(root, change.path)}",
                f"  Reason: {change.reason}",
            ]
        )
    lines.extend(["", "Results:"])
    lines.extend(f"- {result}" for result in results)
    audit_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return audit_path


def resolve_issues(args: argparse.Namespace, jql: str) -> Iterable[JiraIssue]:
    if args.sample_issue:
        return [load_sample_issue(Path(args.sample_issue))]

    base_url = os.environ.get("JIRA_BASE_URL")
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_API_TOKEN")

    missing = [name for name, value in {
        "JIRA_BASE_URL": base_url,
        "JIRA_EMAIL": email,
        "JIRA_API_TOKEN": token,
    }.items() if not value]
    if missing:
        raise SystemExit(f"Missing Jira environment variable(s): {', '.join(missing)}")

    return jira_search(
        base_url,
        email,
        token,
        jql,
        args.max_results,
        args.test_type_field or os.environ.get("JIRA_TEST_TYPE_FIELD"),
        args.gherkin_field or os.environ.get("JIRA_GHERKIN_FIELD"),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create Cucumber automation skeletons from Jira issues.")
    parser.add_argument("--project-key", help="Jira project key, for example QA")
    parser.add_argument("--label", default=DEFAULT_LABEL, help=f"Jira label to search. Default: {DEFAULT_LABEL}")
    parser.add_argument("--status", default=DEFAULT_STATUS, help=f"Jira status to search. Default: {DEFAULT_STATUS}")
    parser.add_argument("--jql", help="Full JQL override")
    parser.add_argument("--test-type-field", help="Jira field id/name that stores Test Type, for example customfield_12345")
    parser.add_argument("--gherkin-field", help="Jira field id/name that stores the Cucumber/Gherkin scenario")
    parser.add_argument(
        "--reuse-existing-steps",
        action="store_true",
        help="Do not create pending methods for Gherkin steps already defined in the framework",
    )
    parser.add_argument("--max-results", type=int, default=25)
    parser.add_argument("--sample-issue", help="Local JSON file with key, summary, description for offline testing")
    parser.add_argument("--dry-run", action="store_true", help="Print planned files without writing them")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    jql = build_jql(args.project_key, args.label, args.status, args.jql)
    print(f"JQL: {jql}")

    issues = list(resolve_issues(args, jql))
    if not issues:
        print("No matching Jira issues found.")
        return 0

    all_changes: list[PlannedChange] = []
    for issue in issues:
        if issue.test_type and issue.test_type.lower() != "cucumber":
            print(f"\n{issue.key}: skipped because test type is {issue.test_type!r}")
            continue
        print(f"\n{issue.key}: {issue.summary}")
        all_changes.extend(plan_changes(issue, root, args.reuse_existing_steps))

    if not all_changes:
        print("No framework changes were planned.")
        return 0

    print_change_plan(root, jql, all_changes, args.dry_run)
    if args.dry_run:
        print("\nDry run complete. No framework files or audit logs were changed.")
        return 0
    if not any(change.action in {"create", "update"} for change in all_changes):
        print("\nNo framework file changes are planned. No audit log was written.")
        return 0

    if not prompt_for_approval(all_changes):
        print("Aborted. No framework files or audit logs were changed.")
        return 1

    results = apply_changes(all_changes)
    for result in results:
        print(f"  {result}")

    audit_path = write_audit_log(root, jql, all_changes, results, args.dry_run)
    print(f"  audit: {audit_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
