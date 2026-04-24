# Jira Field Discovery

Jira field IDs are **instance-specific**. Never hardcode them — always discover for your instance.

## How to discover fields

Use `jira_search_fields` to list all available fields for your Jira instance:
```
jira_search_fields(query="epic")
jira_search_fields(query="story points")
jira_search_fields(query="parent")
```

## Common fields to discover

| Concept | What to search for | Notes |
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
| Story Points | `customfield_XXXXX` via `jira_update_issue` | Same |

Check project type before creating issues — team-managed and classic use different field semantics.
When in doubt, use `jira_search_fields` to confirm field availability and ID.

## Story points workaround

Story points cannot be set during issue creation. Always follow up:
```
jira_update_issue(
    issue_key="PROJ-123",
    fields={},
    additional_fields={"<story_points_field_id>": 3}
)
```

`fields` is required — pass `{}` when updating only via `additional_fields`.
Both must be dict objects, not JSON strings.

## Labels

Pass labels via `additional_fields` at creation:
```
jira_create_issue(
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
