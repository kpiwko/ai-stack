---
description: Install ai-stack plugins and any 3rd party plugins.
argument-hint: "[plugin-name|all]"
---

# /ai-stack:install-plugins

## Synopsis

```
/ai-stack:install-plugins                   ← interactive picker
/ai-stack:install-plugins dev               ← install specific plugin
/ai-stack:install-plugins all               ← install all plugins
```

---

## Available plugins

**ai-stack marketplace** (source: `@ai-stack`):

| Plugin | Description |
|---|---|
| `ai-stack` | Maintenance commands for ai-stack repos |
| `dev` | Coding agents (Go, Python, TypeScript) and code review |
| `track` | Jira and Google Drive commands |
| `quarterly` | Quarterly reflection and connection commands |

**3rd party** (source: `plugins/ai-stack/reference/plugins.yaml`):

Read `plugins/ai-stack/reference/plugins.yaml` to get the current list.

---

## Process

1. Check which plugins are already installed:
   ```bash
   claude plugin list
   ```

2. Read `plugins/ai-stack/reference/plugins.yaml` to get the 3rd party plugin list.

3. Present all plugins with status (built-in first, then 3rd party):

   ```
   Available plugins:
   1. ai-stack   [installed: user]    (@ai-stack)
   2. dev         [not installed]     (@ai-stack)
   3. track       [not installed]     (@ai-stack)
   4. quarterly   [not installed]     (@ai-stack)
   5. context7    [not installed]     (@claude-plugins-official)
   6. superpowers [not installed]     (@claude-plugins-official)
   ```

4. If an argument was provided, use it to select plugins; otherwise ask the user
   which to install (numbers comma-separated, or `all`).

4. Ask for scope:
   - **user** — available in all sessions (default)
   - **project** — available only in the current project
   - **local** — available only in the current directory (personal, not committed)

5. For each selected ai-stack plugin, run:

   ```bash
   claude plugin install <plugin>@ai-stack --scope <scope>
   ```

   For 3rd party plugins, use their `source` field:

   ```bash
   claude plugin install <plugin>@<source> --scope <scope>
   ```

6. Confirm each plugin installed successfully.
