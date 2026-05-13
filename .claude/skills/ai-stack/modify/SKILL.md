---
description: Add, update, or remove a plugin, skill, or MCP entry in the ai-stack registry, then bump the plugin version.
argument-hint: "[plugin|skill|mcp] [add|update|remove]"
---

# /ai-stack:modify

## Synopsis

```
/ai-stack:modify plugin add      ← add a plugin to the registry
/ai-stack:modify plugin update   ← update an existing plugin entry
/ai-stack:modify plugin remove   ← remove a plugin entry
/ai-stack:modify skill add|update|remove
/ai-stack:modify mcp add|update|remove
/ai-stack:modify                 ← interactive: ask type then operation
```

---

## Registry files

| Type | File |
|---|---|
| plugin — built-in | inline table below |
| plugin — external | `.claude/skills/ai-stack/reference/plugins.yaml` |
| skill | `.claude/skills/ai-stack/reference/skills.yaml` |
| mcp | `.claude/skills/ai-stack/reference/mcps.yaml` |

Version is tracked in `.claude-plugin/marketplace.json` (the `"version"` field of the `"ai-stack"` plugin entry).

---

## Built-in ai-stack plugins

These ship with the ai-stack marketplace and need no entry in `plugins.yaml`:

| Plugin | Description |
|---|---|
| `ai-stack` | Maintenance commands for ai-stack repos |
| `dev` | Coding agents (Go, Python, TypeScript) and code review |
| `track` | Jira and Google Drive commands |
| `quarterly` | Quarterly reflection and connection commands |

---

## Process

### Step 1: Determine type and operation

If not provided as arguments, ask:
1. "What type? plugin / skill / mcp"
2. "What operation? add / update / remove"

### Step 2: Gather fields

**For `add`:**

*plugin* — ask: built-in, official marketplace, or 3rd party?

- **built-in**: lives in this repo under `plugins/`
  - `name`: plugin identifier (kebab-case) — must match the directory under `plugins/`
  - `description`: one-line description for the built-in table above

- **official marketplace**: distributed via a named marketplace (e.g. Anthropic)
  - `name`: plugin identifier
  - `source`: marketplace identifier used in `claude plugin install <name>@<source>`
  - `version`: tag, branch, or commit (optional)

- **3rd party**: from a GitHub repo
  - `name`: plugin identifier
  - `source`: GitHub `owner/repo`
  - `version`: tag, branch, or commit (default: `main`)

*skill* — an external skill installed from GitHub:
- `name`: skill identifier (kebab-case)
- `source`: GitHub `owner/repo`
- `path`: path inside the repo (omit if skill is at repo root)
- `version`: tag, branch, or commit (default: `main`)
- `optional`: if `true`, bootstrap skips this skill by default (default: `false`)
- `scope`: `user` (~/.claude/skills/) or `project` (.claude/skills/ in repo root) (default: `user`)

*mcp* — an MCP server to register with Claude Code:
- `name`: server identifier (kebab-case)
- `transport`: `http`, `sse`, or `stdio`
- `url`: e.g. `http://localhost:PORT/mcp` (http/sse)
- `command` / `args`: (stdio only)
- `headers`: key/value map with `$VAR` references (optional; used for auth tokens)
- `scope`: `user`, `project`, or `local` (default: `user`)

**For `update`:**

Ask for the entry name.

- **built-in plugin**: find the row in the built-in table above; display it in full; ask which field to change (`name` or `description`); gather the new value.
- **external plugin / skill / mcp**: read the current entry from the target YAML and display the full entry block; ask which fields to change; gather new values only for those fields.

**For `remove`:**

Ask for the entry name.

### Step 3: Check entry existence

- **add**: check whether the entry already exists:
  - Built-in plugin: scan the inline table above by name.
  - External plugin / skill / mcp: scan `.claude/skills/ai-stack/reference/<type>s.yaml` by name.
  - If found: show it and ask — update it or cancel?
    - If update: treat as `update` from here, with patch version bump.
    - If cancel: exit.
- **update / remove**: find the entry by name:
  - Built-in plugin: scan the inline table above.
  - External: scan `.claude/skills/ai-stack/reference/<type>s.yaml`.
  - If not found: show error and exit.

### Step 4: Preview

Show what will change and the version bump. Do not modify any file until the user confirms.

**add / update:**
```
=== MODIFY PREVIEW ===
File:    .claude/skills/ai-stack/reference/<type>s.yaml
Action:  <add new entry | update existing entry>

  - name: <name>
    source: <source>
    version: <version>     # if applicable
    url: <url>             # mcp only
    scope: <scope>         # mcp only

Version: .claude-plugin/marketplace.json
  "version": "<current>" → "<bumped>"
======================
Proceed? (yes / cancel)
```

Omit fields that do not apply to this entry type (e.g. `url`/`scope` for plugins and skills;
`version` for MCPs if absent in the YAML).

**remove:**
```
=== MODIFY PREVIEW ===
File:    .claude/skills/ai-stack/reference/<type>s.yaml
Action:  remove entry

  - name: <name>
    ...

Version: .claude-plugin/marketplace.json
  "version": "<current>" → "<bumped>"
======================
Proceed? (yes / cancel)
```

For built-in plugins, show the table row change in this file instead of a YAML block.

### Step 5: Write

On confirmation:

1. **Built-in plugin add**: insert a new row into the built-in table in this file, preserving row order and formatting.
2. **Built-in plugin update**: modify the matching row in the built-in table, preserving formatting.
3. **Built-in plugin remove**: delete the matching row from the built-in table in this file.
4. **External plugin / skill / mcp add or update**: append or replace the entry in the target YAML file, preserving existing entries, comments, and formatting.
5. **External plugin / skill / mcp remove**: delete the matching entry block from the YAML file.
6. Read `.claude-plugin/marketplace.json` and bump the version of the `"ai-stack"` plugin entry:
   - New entry added → increment minor, reset patch (e.g. `0.5.0` → `0.6.0`)
   - Entry updated or removed → increment patch only (e.g. `0.5.0` → `0.5.1`)

### Step 6: Confirm and offer commit

Report what changed:
```
<Operation> <type> "<name>" in <file>
Bumped plugin version: <old> → <new>
```

Ask: "Commit these changes? (yes / no)"

If yes:
```bash
# Stage the file modified in step 5 plus marketplace.json:
# Built-in plugin changes: .claude/skills/ai-stack/modify/SKILL.md
# External changes: .claude/skills/ai-stack/reference/<type>s.yaml
git add <modified-file> .claude-plugin/marketplace.json
git commit -m "chore(ai-stack): <add|update|remove> <type> <name>"
```
