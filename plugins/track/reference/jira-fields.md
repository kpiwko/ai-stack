# Jira Field Discovery

Jira field IDs are **instance-specific**. Never hardcode them — always discover for your instance.

## How to discover fields

Use `getJiraProjectIssueTypesMetadata` to list issue types and `getJiraIssueTypeMetaWithFields` to inspect fields for a specific type:

```
getJiraProjectIssueTypesMetadata(cloudId=..., projectIdOrKey="PROJ")
getJiraIssueTypeMetaWithFields(cloudId=..., projectIdOrKey="PROJ", issueTypeId="10014")
```

## Common fields to discover

| Concept | What to look for | Notes |
|---|---|---|
| Epic label | `"epic name"` or `"epic label"` | Classic projects only; gives epic a short display name |
| Epic Link | `"epic link"` | Classic: links Story/Task/Spike to an Epic |
| Story Points | `"story points"` or `"points"` | Cannot be set at creation — update after |
| Git PR / URL | `"pull request"` or `"development"` | Plain text or URL field |

## Classic vs team-managed projects

| Feature | Classic project | Team-managed project |
|---|---|---|
| Link issue to Epic | `customfield_XXXXX` (Epic Link) | `parent: "PROJ-123"` (plain string) |
| Epic display name | `customfield_XXXXX` (Epic Name) | Not needed — use summary |
| Story Points | `customfield_XXXXX` via `editJiraIssue` | Same |

Check project type before creating issues — team-managed and classic use different field semantics.
When in doubt, use `getJiraIssueTypeMetaWithFields` to confirm field availability and ID.

## Story points workaround

Story points cannot be set during issue creation. Always follow up:
```
editJiraIssue(
    cloudId="yourorg.atlassian.net",
    issueIdOrKey="PROJ-123",
    fields={"customfield_XXXXX": 3}
)
```

## Labels

Pass labels via `additional_fields` at creation:
```
createJiraIssue(
    cloudId="yourorg.atlassian.net",
    ...,
    additional_fields={"labels": ["ai-generated", "topic-label"]}
)
```

## Issue types

| Type | When to use |
|---|---|
| Epic | Large feature or initiative |
| Story | User-facing functionality |
| Task | Technical / implementation work |
| Spike | Research, discovery, PoC with uncertain outcome |
| Sub-task | Breakdown of Story/Task (requires parent key) |
