# quarterly plugin

Quarterly review workflow: gather activity from Gmail, Jira, and Drive, then generate
a structured quarterly reflection aligned to company values.

## Install

```
/plugin install quarterly@kpiwko/ai-stack
```

## Requirements

MCP servers: `gmail`, `mcp-atlassian`, `gdrive`

Environment:
```
JIRA_URL=https://yourorg.atlassian.net
```

## Workflow

```
/quarterly:prep Q1 2026     # gather data → reports/quarterly-data-Q1-2026.md
/quarterly:connect reports/quarterly-data-Q1-2026.md  # guided reflection → summary
```

## Commands

| Command | Description |
|---|---|
| `/quarterly:prep [Q] [year]` | Gather Gmail, Jira, Drive activity for the quarter |
| `/quarterly:connect [data-file]` | Guide structured quarterly reflection and produce formatted output |

## Output format

See `reference/template.md` for the default output structure.
Add company-specific format files to `reference/` to override (e.g. `reference/mycompany-format.md`
and reference it in `connect.md`).
