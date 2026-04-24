---
description: Register MCP servers with Claude Code.
argument-hint: "[mcp-name|all]"
---

# /ai-stack:install-mcps

## Synopsis

```
/ai-stack:install-mcps                  ← interactive picker
/ai-stack:install-mcps gmail            ← register specific MCP
/ai-stack:install-mcps all             ← register all MCPs
```

---

## Available MCPs

Add entries to `plugins/ai-stack/reference/mcps.yaml` to extend this list.

| Name | Transport | URL | Default scope |
|---|---|---|---|
| `gmail` | http | `http://localhost:17633/mcp` | user |
| `mcp-atlassian` | http | `http://localhost:17000/mcp` | user |
| `gdrive` | http | `http://localhost:17100/mcp` | user |
| `devlake-prod-mysql-mcp` | http | `http://localhost:17300/mcp` | local |
| `devlake-local-mysql-mcp` | http | `http://localhost:17301/mcp` | local |

`devlake-prod-mysql-mcp` requires `$KONFLUX_MCP_SECRET_KEY` in the environment.
`devlake-local-mysql-mcp` requires `$DEVLAKE_MCP_SECRET_KEY` in the environment.

---

## Process

1. Check which MCPs are already registered:
   ```bash
   claude mcp list
   ```

2. Present MCPs with status:

   ```
   Available MCPs:
   1. gmail                   [not registered]
   2. mcp-atlassian           [registered: user]
   3. gdrive                  [not registered]
   4. devlake-prod-mysql-mcp  [not registered]
   5. devlake-local-mysql-mcp [not registered]
   ```

3. If an argument was provided, use it to select MCPs; otherwise ask the user
   which to register (numbers comma-separated, or `all`).

4. Ask for scope:
   - **user** — available in all sessions (default)
   - **project** — available only in the current project
   - **local** — available only in the current directory (personal, not committed)

   If the entry has a `scope` field, pre-select it but confirm with the user
   before proceeding (scope is always overridable at install time).

5. For each selected MCP, run:

   **http/sse** transport:
   ```bash
   claude mcp add --transport <transport> --scope <scope> \
     [--header "KEY: VALUE" ...] <name> <url>
   ```

   **stdio** transport:
   ```bash
   claude mcp add --scope <scope> [-e KEY=VALUE ...] <name> <command> [args...]
   ```

   Expand `$VAR` references in `headers` and `env` values from the current shell
   environment before passing them to the CLI. If a required env var is unset,
   warn and skip that MCP rather than registering it with an empty value.

6. Confirm each MCP registered successfully.
