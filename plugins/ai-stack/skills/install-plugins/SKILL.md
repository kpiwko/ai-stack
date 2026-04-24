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

**3rd party** (source: `reference/plugins.yaml` in the plugin root):

The 3rd party list is read at runtime from `reference/plugins.yaml`, located two
directories above the skill base directory shown at invocation time.

---

## Process

1. Check which plugins are already installed:
   ```bash
   claude plugin list
   ```

2. Read `reference/plugins.yaml` from the plugin root (two levels above the skill
   base directory) to get the 3rd party plugin list.

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
   which to install (numbers comma-separated, `all`, or `none` to exit).

5. **Always ask for scope before installing** — even if only one plugin is selected.
   Present this exact prompt to the user:

   ```
   Install scope:
     u) user    — available in all sessions (default)
     p) project — available only in the current project
     l) local   — available only in the current directory (personal, not committed)

   Scope [u/p/l, default: u]:
   ```

   Map input: `u`/`user` → `user`, `p`/`project` → `project`, `l`/`local` → `local`.
   Empty input defaults to `user`.

6. For each selected ai-stack plugin, run:

   ```bash
   claude plugin install <plugin>@ai-stack --scope <scope>
   ```

   For 3rd party plugins, use their `source` field:

   ```bash
   claude plugin install <plugin>@<source> --scope <scope>
   ```

7. Confirm each plugin installed successfully.
