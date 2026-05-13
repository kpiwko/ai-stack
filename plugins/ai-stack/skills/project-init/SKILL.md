---
description: Initialise the current directory as an ai-stack project. Copies CLAUDE.md and AGENTS.md from the plugin reference and offers to install optional project-scoped skills.
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

| What | File |
|---|---|
| CLAUDE.md template | `<plugin-base>/reference/CLAUDE.md` |
| AGENTS.md template | `<plugin-base>/reference/AGENTS.md` |
| Optional skills | `<plugin-base>/reference/skills.yaml` |

Read all reference files before starting.

---

## Process

### Step 1 — Copy CLAUDE.md

Check if `CLAUDE.md` exists in CWD:

```bash
ls CLAUDE.md 2>/dev/null && echo "exists" || echo "missing"
```

If **exists** and `force` was **not** passed → record `CLAUDE.md: already present — skipped`.

If **exists** and `force` **was** passed → overwrite:

```bash
cp "<plugin-base>/reference/CLAUDE.md" CLAUDE.md
```

Record `CLAUDE.md: overwritten`.

If **missing** → copy from the plugin reference:

```bash
cp "<plugin-base>/reference/CLAUDE.md" CLAUDE.md
```

Record `CLAUDE.md: created`.

### Step 2 — Copy AGENTS.md

Check if `AGENTS.md` exists in CWD:

```bash
ls AGENTS.md 2>/dev/null && echo "exists" || echo "missing"
```

If **exists** and `force` was **not** passed → record `AGENTS.md: already present — skipped`.

If **exists** and `force` **was** passed → overwrite:

```bash
cp "<plugin-base>/reference/AGENTS.md" AGENTS.md
```

Record `AGENTS.md: overwritten`.

If **missing** → copy from the plugin reference:

```bash
cp "<plugin-base>/reference/AGENTS.md" AGENTS.md
```

Record `AGENTS.md: created`.

### Step 3 — Check optional skills

Read `<plugin-base>/reference/skills.yaml`. Collect all entries where `optional: true`.

For each optional skill, check if it is already installed in `.claude/skills/<name>`:

```bash
ls .claude/skills/<name> 2>/dev/null && echo "installed" || echo "missing"
```

Record each skill's status (`installed` or `missing`). Do not prompt or install anything yet.

### Step 4 — Summary

Print the full summary now — before any optional skills interaction:

```
=== project-init SUMMARY ===

CLAUDE.md     created
AGENTS.md     already present — skipped
Skills:
  template-slide-deck   missing
  n8n-skills            already installed

============================

Next steps:
  1. Edit CLAUDE.md and AGENTS.md to reflect this project's conventions.
  2. Run /ai-stack:up to start the service stack.
```

Use the statuses recorded in Steps 1–3 to fill in each row.

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
