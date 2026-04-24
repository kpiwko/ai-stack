---
description: Add a new plugin, skill, or MCP entry to the ai-stack registry, then bump the plugin version.
argument-hint: "[plugin|skill|mcp]"
---

# /ai-stack:add-entry

## Synopsis

```
/ai-stack:add-entry plugin   ← add a plugin (built-in, official marketplace, or 3rd party)
/ai-stack:add-entry skill    ← add an external skill to skills.yaml
/ai-stack:add-entry mcp      ← add an MCP server to mcps.yaml
/ai-stack:add-entry          ← interactive: ask which type first
```

---

## Registry files

| Type | File |
|---|---|
| plugin — built-in | `plugins/ai-stack/skills/install-plugins/SKILL.md` (hardcoded table) |
| plugin — external | `plugins/ai-stack/reference/plugins.yaml` |
| skill | `plugins/ai-stack/reference/skills.yaml` |
| mcp | `plugins/ai-stack/reference/mcps.yaml` |

Version is tracked in `plugins/ai-stack/.claude-plugin/plugin.json`.

---

## Process

### Step 1: Determine type

If not provided as an argument, ask: "What are you adding — plugin, skill, or mcp?"

### Step 2: Gather fields

**plugin** — ask: built-in, official marketplace, or 3rd party?

- **built-in**: a new plugin living in this repo under `plugins/`
  - `name`: plugin identifier (kebab-case) — must match the directory under `plugins/`
  - `description`: one-line description shown in the picker table

- **official marketplace**: a plugin distributed via an official named marketplace (e.g. Anthropic)
  - `name`: plugin identifier
  - `source`: marketplace identifier used in `claude plugin install <name>@<source>`
  - `version`: tag, branch, or commit (optional)

- **3rd party**: a plugin from a GitHub repo
  - `name`: plugin identifier
  - `source`: GitHub `owner/repo`
  - `version`: tag, branch, or commit (default: `main`)

**skill** — an external skill installed from GitHub:
- `name`: skill identifier (kebab-case)
- `source`: GitHub `owner/repo`
- `path`: path inside the repo (omit if skill is at repo root)
- `version`: tag, branch, or commit (default: `main`)

**mcp** — an MCP server to register with Claude Code (http/sse only):
- `name`: server identifier (kebab-case)
- `transport`: `http` or `sse`
- `url`: e.g. `http://localhost:PORT/mcp`
- `headers`: key/value map with `$VAR` references (optional; used for auth tokens)
- `scope`: `user`, `project`, or `local` (default: `user`)

### Step 3: Check for duplicates

**Built-in plugin**: check whether `name` already appears in the `install-plugins/SKILL.md` table.

**External plugin / skill / mcp**: read the target YAML and check whether an entry with
the same `name` already exists.

If a duplicate is found, show the existing entry and ask: **update it or cancel?**
- Updating an existing entry → patch version bump (Step 5)
- Adding a new entry → minor version bump (Step 5)

### Step 4: Preview

Show exactly what will change, plus the version bump:

**Built-in plugin** — shows the new table row:
```
=== ADD ENTRY PREVIEW ===
File:    plugins/ai-stack/skills/install-plugins/SKILL.md
Action:  add row to ai-stack marketplace table

  | `<name>` | <description> |

Version: plugins/ai-stack/.claude-plugin/plugin.json
  "version": "<current>" → "<minor-bump>"
=========================
Proceed? (yes / cancel)
```

**External plugin / skill / mcp** — shows the YAML block:
```
=== ADD ENTRY PREVIEW ===
File:    plugins/ai-stack/reference/<type>s.yaml
Action:  append [or: update existing entry]

  - name: <name>
    source: <source>
    version: <version>       # if applicable
    url: <url>               # mcp only
    scope: <scope>           # mcp only

Version: plugins/ai-stack/.claude-plugin/plugin.json
  "version": "<current>" → "<bumped>"
=========================
Proceed? (yes / cancel)
```

Do not modify any file until the user confirms.

### Step 5: Write

On confirmation:

1. **Built-in plugin**: insert a new row into the `| ai-stack marketplace |` table in
   `install-plugins/SKILL.md`, preserving the existing row order and formatting.

2. **External plugin / skill / mcp**: append (or replace) the entry in the target YAML file,
   preserving existing entries, comments, and formatting.

3. Read `plugin.json` and bump the version:
   - New entry → increment minor, reset patch (e.g. `0.2.1` → `0.3.0`)
   - Update to existing entry → increment patch only (e.g. `0.2.1` → `0.2.2`)

### Step 6: Confirm and offer commit

Report what changed:
```
Added <type> "<name>" to <file>
Bumped plugin version: <old> → <new>
```

Ask: "Commit these changes? (yes / no)"

If yes:
```bash
git add <changed-file> plugins/ai-stack/.claude-plugin/plugin.json
git commit -m "chore(ai-stack): add <type> <name> to registry"
```
