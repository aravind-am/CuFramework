# CuFramework

Automation framework built with Java, Selenium, TestNG, and Cucumber.

The main framework lives under:

```text
automation-hybrid-framework/
```

## Project Layout

```text
automation-hybrid-framework/
  src/test/java/
    pages/
    stepdefinitions/
    testrunners/
    utilities/
  src/test/resources/
    features/
    config/
  tools/
    jira_automation_agent.py
  docs/
    jira-automation-agent.md
  AIAudit/
```

## Jira Automation Agent

This project includes a repo-local Python agent that reads Jira Cucumber test cases marked with the `AutomationCandidate` label and creates or updates Cucumber scripts in the framework.

The agent:

- Reads Jira issues with label `AutomationCandidate` and status `New`.
- Uses Jira test cases with test type `Cucumber`.
- Syncs Jira Gherkin into `.feature` files.
- Generates matching Java step-definition skeletons.
- Prompts before changing framework files.
- Writes approved-run audit logs under `automation-hybrid-framework/AIAudit`.

Full setup and usage details are here:

```text
automation-hybrid-framework/docs/jira-automation-agent.md
```

## Quick Start

From the framework folder:

```powershell
cd automation-hybrid-framework
python tools\jira_automation_agent.py --sample-issue tools\sample_jira_issue.json --dry-run
```

To run against Jira, configure Jira environment variables first:

```powershell
$env:JIRA_BASE_URL = "https://your-domain.atlassian.net"
$env:JIRA_EMAIL = "your.email@example.com"
$env:JIRA_API_TOKEN = "your-token"
$env:JIRA_TEST_TYPE_FIELD = "customfield_12345"
$env:JIRA_GHERKIN_FIELD = "customfield_67890"

python tools\jira_automation_agent.py --project-key QA --dry-run
```

Remove `--dry-run` to apply changes. The agent will show the proposed framework changes and wait for confirmation before writing files.
