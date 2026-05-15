# Jira Automation Agent

This repo includes a small generator that reads Jira test cases marked as automation candidates and creates matching Cucumber scripts in the existing test automation framework.

## What It Reads

By default it searches Jira with:

```jql
labels = "AutomationCandidate" AND status = "New" ORDER BY updated DESC
```

If your Jira project exposes test type in JQL, include it in the query:

```powershell
python tools\jira_automation_agent.py --jql "project = QA AND labels = AutomationCandidate AND status = New AND 'Test Type' = Cucumber"
```

You can also pass a project key:

```powershell
python tools\jira_automation_agent.py --project-key QA
```

Or pass the exact JQL:

```powershell
python tools\jira_automation_agent.py --jql "project = QA AND labels = AutomationCandidate AND status = New"
```

## Jira Credentials

Set these environment variables before running:

```powershell
$env:JIRA_BASE_URL = "https://your-domain.atlassian.net"
$env:JIRA_EMAIL = "your.email@example.com"
$env:JIRA_API_TOKEN = "your-token"
```

Set the Jira custom field IDs for Cucumber test type and Gherkin content:

```powershell
$env:JIRA_TEST_TYPE_FIELD = "customfield_12345"
$env:JIRA_GHERKIN_FIELD = "customfield_67890"
```

When `JIRA_TEST_TYPE_FIELD` is configured, the agent only generates scripts for issues whose test type field is `Cucumber`. If you do not configure that field, include the Cucumber filter in the JQL. The agent writes the Jira Gherkin content directly into the generated `.feature` file.

## Generated Files

For each matching Jira issue, the agent creates:

- `src/test/resources/features/<jira-key>_<summary>.feature`
- `src/test/java/stepdefinitions/<JiraKeySummary>Steps.java`

Existing files are left untouched, so rerunning the agent will not overwrite scripts you have already implemented. The generated Java step file contains pending methods only for Gherkin steps that are not already defined in `src/test/java/stepdefinitions`.

## Dry Run

Preview what would be created:

```powershell
python tools\jira_automation_agent.py --project-key QA --dry-run
```

## Offline Test

Use the sample issue without connecting to Jira:

```powershell
python tools\jira_automation_agent.py --sample-issue tools\sample_jira_issue.json --dry-run
```
