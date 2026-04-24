---
description: Install ai-stack plugins and any 3rd party plugins from ai-stack.yaml.
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

## Process

1. The following ai-stack plugins are always available:

   | Plugin | Description |
   |---|---|
   | `dev` | Coding agents (Go, Python, TypeScript) and code review command |
   | `track` | Jira and Google Drive commands |
   | `quarterly` | Quarterly reflection and connection commands |
   | `ai-stack` | This plugin — maintenance commands for ai-stack repos |

2. Fetch `ai-stack.yaml` from
   `https://raw.githubusercontent.com/kpiwko/ai-stack/main/ai-stack.yaml`
   and append any additional plugins listed under `plugins:`.

3. Check which plugins are already installed by running:
   ```bash
   claude plugin list
   ```

4. Present plugins with status:

   ```
   Available plugins:
   1. dev        [not installed]
   2. track      [installed: user]
   3. quarterly  [not installed]
   4. ai-stack   [not installed]
   ```

5. If an argument was provided, use it to select plugins; otherwise ask the user
   which to install (numbers comma-separated, or `all`).

6. Ask for scope:
   - **user** — available in all sessions (default)
   - **project** — available only in the current project
   - **local** — available only in the current directory (personal, not committed)

7. For each selected plugin, run:

   ```bash
   claude plugin install <plugin>@kpiwko/ai-stack --scope <scope>
   ```

   For 3rd party plugins from `ai-stack.yaml`, use their `source` field:

   ```bash
   claude plugin install <plugin>@<source> --scope <scope>
   ```

8. Confirm each plugin installed successfully.
