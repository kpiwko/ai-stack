---
description: Initialise the current directory as an ai-stack project. Copies CLAUDE.md and AGENTS.md from the plugin reference, offers to install optional project-scoped skills, and registers local MCP servers.
---

# /ai-stack:project-init

## Synopsis

```
/ai-stack:project-init          ← initialise the current directory as an ai-stack project
/ai-stack:project-init force    ← overwrite existing CLAUDE.md and AGENTS.md from the template
```

Idempotent by default — skips files that already exist. Pass `force` to overwrite them. Run from the root of the project you want to initialise.

---

## Reference files

> **Path resolution:** `../reference/X` is relative to this skill's base directory.
> Use the absolute path from the `Base directory for this skill:` header: `<base-dir>/../reference/X`.

| What | File |
|---|---|
| CLAUDE.md template | `../reference/CLAUDE.md` |
| AGENTS.md template | `../reference/AGENTS.md` |
| Optional skills | `../reference/skills.yaml` |
| Local MCP servers | `../reference/mcps.yaml` |

Read all reference files before starting.

---

## Process

### Step 1 — Copy CLAUDE.md

Check if `CLAUDE.md` exists in CWD:

```bash
ls CLAUDE.md 2>/dev/null && echo "exists" || echo "missing"
```

If **exists** and `force` was **not** passed → record `CLAUDE.md: already present — skipped`.

If **exists** and `force` **was** passed → overwrite: use the Write tool to create `CLAUDE.md`
in CWD with the content of `../reference/CLAUDE.md` from the repo.
Record `CLAUDE.md: overwritten`.

If **missing** → use the Write tool to create `CLAUDE.md` in CWD with the content of
`../reference/CLAUDE.md` from the repo.
Record `CLAUDE.md: created`.

### Step 2 — Copy AGENTS.md

Check if `AGENTS.md` exists in CWD:

```bash
ls AGENTS.md 2>/dev/null && echo "exists" || echo "missing"
```

If **exists** and `force` was **not** passed → record `AGENTS.md: already present — skipped`.

If **exists** and `force` **was** passed → overwrite: use the Write tool to create `AGENTS.md`
in CWD with the content of `../reference/AGENTS.md` from the repo.
Record `AGENTS.md: overwritten`.

If **missing** → use the Write tool to create `AGENTS.md` in CWD with the content of
`../reference/AGENTS.md` from the repo.
Record `AGENTS.md: created`.

### Step 3 — Check optional skills

Read `../reference/skills.yaml`. Collect all entries where `optional: true`.

For each optional skill, check if it is already installed in `.claude/skills/<name>`:

```bash
ls .claude/skills/<name> 2>/dev/null && echo "installed" || echo "missing"
```

Record each skill's status (`installed` or `missing`). Do not prompt or install anything yet.

### Step 3.5 — Check local MCP servers

Read `../reference/mcps.yaml`. Collect all entries where `scope: local`.

Check which are already registered:

```bash
claude mcp list
```

For each local MCP, record status: `registered` or `missing`. Do not prompt or register anything yet.

### Step 4 — Summary

Print the full summary now — before any optional skills or MCP interaction:

```
=== project-init SUMMARY ===

CLAUDE.md     created
AGENTS.md     already present — skipped
Skills:
  n8n-skills            already installed
MCPs:
  devlake-prod-mysql-mcp    missing
  devlake-local-mysql-mcp   already registered

============================

Next steps:
  1. Edit CLAUDE.md and AGENTS.md to reflect this project's conventions.
  2. Run /ai-stack:up to start the service stack.
```

Use the statuses recorded in Steps 1–3.5 to fill in each row.

### Step 5 — Optional skills offer

If all optional skills are already installed → print `All optional skills already installed.` and stop.

If any optional skills are missing, use the **AskUserQuestion tool** to offer them:

- `question`: `"Which optional skills would you like to install?"`
- `header`: `"Optional skills"`
- `multiSelect`: `true`
- `options`: one entry per **missing** optional skill, with `label` = skill name and `description` = source

If the user selects nothing (or the tool is unavailable) → print `No optional skills installed.` and stop.

For each selected skill, install via sparse git checkout into `.claude/skills/<name>`:

```bash
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
git clone --depth 1 --filter=blob:none --sparse --branch <version> \
    https://github.com/<source> "$tmpdir"
# if path field is set in skills.yaml:
git -C "$tmpdir" sparse-checkout set <path>
mkdir -p .claude/skills/<name>
cp -r "$tmpdir/<path>/." .claude/skills/<name>/
```

Print confirmation for each installed skill:

```
template-slide-deck   installed → .claude/skills/template-slide-deck
```

### Step 6 — Local MCP servers offer

If all local MCPs are already registered → print `All local MCP servers already registered.` and stop.

If any are missing, use the **AskUserQuestion tool** to offer them:

- `question`: `"Which local MCP servers would you like to register?"`
- `header`: `"Local MCPs"`
- `multiSelect`: `true`
- `options`: one entry per **missing** MCP, with `label` = name and `description` = url

If the user selects nothing (or the tool is unavailable) → print `No MCP servers registered.` and stop.

For each selected MCP:

1. Source `.env` if present to expand `$VAR` references:

   ```bash
   set -a; [ -f .env ] && . ./.env; set +a
   ```

2. For each `$VAR` reference in the entry's fields (url, headers):
   - If the var is set after sourcing → use its value.
   - If still unset → use **AskUserQuestion** (single select, free-text via Other) to prompt:
     `"Enter value for <VAR> (required by <name>):"`
   - After the user provides a value, ask whether to save it to `.env`:
     `"Save <VAR> to .env for future use?"`
     If yes → append `<VAR>=<value>` to `.env`.

3. Register:

   ```bash
   claude mcp add <name> <url> --transport <transport> --scope local \
     [--header "KEY: VALUE" ...]
   ```

   Record `registered` or `FAILED`.

Print confirmation for each:

```
devlake-prod-mysql-mcp   registered → http://localhost:17300/mcp
```
