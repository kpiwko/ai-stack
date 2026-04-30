# track plugin

Track decisions and work in external systems: Jira issues, Google Docs, Google Drive.

## Install

```
/plugin install track@kpiwko/ai-stack
```

## Requirements

MCP servers must be running and registered:
- `atlassian` plugin — for `/track:jira`
- `gdrive` — for `/track:gdrive-doc` and `/track:gdrive-organize`

Environment variables for Jira:
```
JIRA_URL=https://yourorg.atlassian.net
JIRA_PROJECT=MYPROJ
```

## Commands

| Command | Description |
|---|---|
| `/track:jira [type] [description]` | Create or update a Jira issue with full preview before submit |
| `/track:gdrive-doc [topic]` | Create or update a Google Doc with structured metadata header |
| `/track:gdrive-organize [drive] [focus]` | Snapshot, plan, and reorganize a Google Drive |
