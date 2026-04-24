---
description: Register MCP servers from ai-stack.yaml with Claude Code.
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

## Process

1. Fetch `ai-stack.yaml` from
   `https://raw.githubusercontent.com/kpiwko/ai-stack/main/ai-stack.yaml`

2. Check which MCPs are already registered by running:
   ```bash
   claude mcp list
   ```

3. Present MCPs with status:

   ```
   Available MCPs:
   1. gmail   [not registered]
   2. mysql   [registered: user]
   ```

4. If an argument was provided, use it to select MCPs; otherwise ask the user
   which to register (numbers comma-separated, or `all`).

5. Ask for scope:
   - **user** — available in all sessions (default)
   - **project** — available only in the current project
   - **local** — available only in the current directory (personal, not committed)

6. For each selected MCP, run the appropriate `claude mcp add` command based
   on the `transport` field:

   **stdio** transport:
   ```bash
   claude mcp add --scope <scope> [-e KEY=VALUE ...] <name> <command> [args...]
   ```

   **sse** or **http** transport:
   ```bash
   claude mcp add --transport <transport> --scope <scope> \
     [--header "KEY: VALUE" ...] <name> <url>
   ```

   For both transports, expand `$VAR` references in `env` and `headers` values
   from the current shell environment before passing them to the CLI.
   If a required env var is unset, warn and skip that MCP rather than registering
   it with an empty value.

   If the entry has a `scope` field, pre-select it but confirm with the user
   before proceeding (scope is always overridable at install time).

7. Confirm each MCP registered successfully.
