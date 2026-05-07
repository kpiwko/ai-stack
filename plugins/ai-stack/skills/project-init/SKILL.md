---
description: Initialise the current directory as an ai-stack project. Copies CLAUDE.md and AGENTS.md from the plugin reference and offers to install optional project-scoped skills.
---

# /ai-stack:project-init

## Synopsis

```
/ai-stack:project-init   ← initialise the current directory as an ai-stack project
```

Idempotent — skips files that already exist. Run from the root of the project you want to initialise.

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

If **exists** → record `CLAUDE.md: already present — skipped`.

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

If **exists** → record `AGENTS.md: already present — skipped`.

If **missing** → copy from the plugin reference:

```bash
cp "<plugin-base>/reference/AGENTS.md" AGENTS.md
```

Record `AGENTS.md: created`.

### Step 3 — Optional skills

Read `<plugin-base>/reference/skills.yaml`. Collect all entries where `optional: true`.

For each optional skill, check if it is already installed in `.claude/skills/<name>`:

```bash
ls .claude/skills/<name> 2>/dev/null && echo "installed" || echo "missing"
```

Print status table:

```
Optional skills available:
  template-slide-deck   missing
  n8n-skills            already installed
```

If all are already installed → print `All optional skills already installed.` and skip to Step 4.

Otherwise print:

```
Install any? Enter name(s) separated by spaces, or press Enter to skip:
```

Wait for input. If the user enters one or more names:

- Validate each name against the optional skills list; warn and skip unrecognised names.
- For each valid name, install via sparse git checkout into `.claude/skills/<name>`:

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

If no `path` field, omit the `sparse-checkout set` step and copy from `$tmpdir` directly.

Print confirmation for each:

```
template-slide-deck   installed → .claude/skills/template-slide-deck
```

If the user presses Enter with no input → print `No optional skills installed.`

### Step 4 — Summary

```
=== project-init SUMMARY ===

CLAUDE.md     created
AGENTS.md     already present — skipped
Skills:
  template-slide-deck   installed → .claude/skills/template-slide-deck
  n8n-skills            already installed

============================

Next steps:
  1. Edit CLAUDE.md and AGENTS.md to reflect this project's conventions.
  2. Run /ai-stack:up to start the service stack.
```
