# ai-stack Plugin Restructure Implementation Plan

> **STATUS: COMPLETED (2026-05-13)**
>
> **What shipped vs. original design:**
> - All tasks completed as specified (justfile renames, skills added/removed, CLAUDE.md/AGENTS.md moved)
> - Skills were initially moved to `.claude/skills/ai-stack/` (plugin-local path) but this broke Claude Code's discovery mechanism — `<source>/skills/<name>/SKILL.md` is required
> - Final structure: skills live in `plugins/ai-stack/skills/<name>/SKILL.md` (the plugin source directory), reference files in `plugins/ai-stack/reference/`
> - Plugin bumped to `0.12.0` (not `0.10.0` as planned — version was updated again during the evals work)
> - The two-metadata-file design: `marketplace.json` (root, used by `/plugin` update checker) and `plugins/ai-stack/.claude-plugin/plugin.json` (plugin manifest) must be kept in sync; both show `0.12.0`

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the ai-stack plugin and justfile so commands form a coherent machine → project → session lifecycle, eliminating naming collisions between OpenShell and LINCE "sandbox" concepts.

**Architecture:** Remove the `sandbox` skill (LINCE installation moves to justfile), rename OpenShell justfile commands to `openshell-*`, add LINCE justfile commands as `lince-*`, add a `/ai-stack:down` skill, add `/ai-stack:project-init` for per-project setup, and remove Step 8 (optional skills offer) from bootstrap so it lives in project-init instead.

**Tech Stack:** Bash (justfile recipes), Markdown (skill files), JSON (plugin.json), YAML (skills.yaml)

---

## Lifecycle after this change

| Command | Scope | When |
|---|---|---|
| `/ai-stack:bootstrap` | machine — global skills, MCPs, runtimes | once per machine |
| `just lince-bootstrap` | machine — LINCE toolkit | once per machine |
| `just openshell-bootstrap` | machine — OpenShell gateway + Vertex provider | once per machine |
| `/ai-stack:project-init` | project — local CLAUDE.md, AGENTS.md, optional skills | once per project |
| `/ai-stack:up` | session — start compose stack | each session |
| `/ai-stack:down` | session — stop compose stack | each session |
| `just openshell` | session — launch Claude in OpenShell sandbox | on demand |
| `just lince` | session — launch LINCE dashboard | on demand |

---

## File Map

| Action | File |
|---|---|
| Modify | `justfile` |
| Delete | `plugins/ai-stack/skills/sandbox` |
| Modify | `plugins/ai-stack/skills/bootstrap` (remove Step 8) |
| Create | `plugins/ai-stack/skills/down` |
| Create | `plugins/ai-stack/skills/project-init` |
| Move+symlink | `CLAUDE.md` → `plugins/ai-stack/reference/CLAUDE.md`, repo root becomes symlink |
| Move+symlink | `AGENTS.md` → `plugins/ai-stack/reference/AGENTS.md`, repo root becomes symlink |
| Modify | `plugins/ai-stack/reference/skills.yaml` (add `scope: project` to optional skills) |
| Modify | `plugins/ai-stack/.claude-plugin/plugin.json` (bump version to `0.10.0`) |

---

## Task 1: Rename OpenShell justfile commands

**Files:**
- Modify: `justfile`

- [ ] **Step 1: Rename the three OpenShell recipes**

Replace the existing `sandbox-bootstrap`, `sandbox`, and `sandbox-teardown` recipes with the names below. Content is unchanged — only the recipe name and any internal comments change.

```just
# Build OpenShell binaries + sideload image, restart the gateway, and register the vertex-claude provider.
# Pass rebuild=true to rebuild even when binaries/image already exist.
# Requires env: OPENSHELL_DIR, ANTHROPIC_VERTEX_PROJECT_ID, CLAUDE_CODE_USE_VERTEX, CLOUD_ML_REGION
openshell-bootstrap rebuild='':
    # ... (identical body to former sandbox-bootstrap)

# Delete all sandboxes, stop the OpenShell gateway, and clean up sandbox staging files.
openshell-teardown:
    # ... (identical body to former sandbox-teardown)

# Launch Claude Code in an OpenShell sandbox with Vertex AI credentials.
# Requires env: OPENSHELL_DIR, ANTHROPIC_VERTEX_PROJECT_ID, CLAUDE_CODE_USE_VERTEX,
#               CLOUD_ML_REGION, GOOGLE_APPLICATION_CREDENTIALS
openshell:
    # ... (identical body to former sandbox)
```

- [ ] **Step 2: Remove `up`, `down`, and `status` recipes**

Delete these three recipes from the justfile entirely. They are replaced by the `/ai-stack:up` and `/ai-stack:down` skills.

- [ ] **Step 3: Verify justfile parses**

```bash
just --list
```

Expected output includes `openshell`, `openshell-bootstrap`, `openshell-teardown`, `lince`, `lince-bootstrap` — and does NOT include `sandbox`, `sandbox-bootstrap`, `sandbox-teardown`, `up`, `down`, `status`.

(Note: `lince` and `lince-bootstrap` are added in Task 2. Run this check after Task 2.)

- [ ] **Step 4: Commit**

```bash
git add justfile
git commit -m "chore(justfile): rename sandbox→openshell, remove up/down/status"
```

---

## Task 2: Add LINCE justfile commands

**Files:**
- Modify: `justfile`

- [ ] **Step 1: Add `lince-bootstrap` recipe**

Insert after the `openshell-teardown` recipe:

```just
# Install or update the LINCE toolkit (agent-sandbox + lince-dashboard).
# Runs the interactive TUI quickstart installer from the lince/ submodule.
lince-bootstrap:
    cd lince && bash quickstart.sh
```

- [ ] **Step 2: Add `lince` recipe**

Insert after `lince-bootstrap`:

```just
# Launch the LINCE dashboard (Zellij + lince-dashboard plugin).
lince:
    zd
```

- [ ] **Step 3: Verify justfile parses**

```bash
just --list
```

Expected: `lince`, `lince-bootstrap`, `openshell`, `openshell-bootstrap`, `openshell-teardown` all present. No `sandbox*`, `up`, `down`, or `status`.

- [ ] **Step 4: Commit**

```bash
git add justfile
git commit -m "chore(justfile): add lince-bootstrap and lince recipes"
```

---

## Task 3: Delete the sandbox skill

**Files:**
- Delete: `plugins/ai-stack/skills/sandbox`

- [ ] **Step 1: Delete the file**

```bash
rm plugins/ai-stack/skills/sandbox
```

- [ ] **Step 2: Verify it is gone**

```bash
ls plugins/ai-stack/skills/
```

Expected: `bootstrap  modify  up` (no `sandbox`).

- [ ] **Step 3: Commit**

```bash
git add plugins/ai-stack/skills/sandbox
git commit -m "feat(ai-stack): remove sandbox skill — LINCE install moves to justfile"
```

---

## Task 4: Create `/ai-stack:down` skill

**Files:**
- Create: `plugins/ai-stack/skills/down`

- [ ] **Step 1: Write the skill file**

```markdown
# /ai-stack:down

## Synopsis

```
/ai-stack:down   ← stop all compose services in the current directory
```

Idempotent — safe to run even if services are already stopped.

---

## Process

### Step 1 — Prerequisites check

Run:

```bash
(command -v podman >/dev/null 2>&1 && podman compose version >/dev/null 2>&1 && echo "podman") \
  || (command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1 && echo "docker") \
  || echo "MISSING"
```

Record which tool is available (`podman` or `docker`). Use that tool for all compose
commands below.

If neither is found, stop and display:

```
✗ podman / docker compose: not found
  Install Podman Desktop: https://podman-desktop.io/
  or Docker Desktop:      https://www.docker.com/products/docker-desktop/
```

### Step 2 — Check compose.yaml present

```bash
ls compose.yaml 2>/dev/null && echo "exists" || echo "missing"
```

If missing, stop and display:

```
✗ compose.yaml not found in current directory.
  Run /ai-stack:up first to initialise the stack here.
```

### Step 3 — Stop services

Run:

```bash
podman compose down   # or: docker compose down
```

If compose exits non-zero, print the error and stop.

### Step 4 — Summary

```
=== ai-stack DOWN ===
All services stopped.
=====================
```
```

- [ ] **Step 2: Verify the file exists**

```bash
ls plugins/ai-stack/skills/down
```

- [ ] **Step 3: Commit**

```bash
git add plugins/ai-stack/skills/down
git commit -m "feat(ai-stack): add /ai-stack:down skill"
```

---

## Task 5: Remove Step 8 from the bootstrap skill

**Files:**
- Modify: `plugins/ai-stack/skills/bootstrap`

- [ ] **Step 1: Read the current file**

```bash
cat plugins/ai-stack/skills/bootstrap
```

- [ ] **Step 2: Delete Step 8 entirely**

Remove the entire `### Step 8 — Optional skills offer` section from the skill file. This includes the heading, the conditional logic, the prompt text, and all sub-bullets below it.

The file should end after the closing of the Step 7 summary block.

- [ ] **Step 3: Update the Step 7 summary table**

In the Skills section of the summary table, update the row for optional skills. Change:

```
<skill-name>   skipped (optional)
```

to:

```
<skill-name>   skipped (install via /ai-stack:project-init)
```

Update the descriptive comment above the summary section to remove any mention of Step 8.

- [ ] **Step 4: Verify the file ends cleanly after Step 7**

```bash
tail -20 plugins/ai-stack/skills/bootstrap
```

Expected: no `Step 8`, no `Optional skills` heading.

- [ ] **Step 5: Commit**

```bash
git add plugins/ai-stack/skills/bootstrap
git commit -m "feat(ai-stack): move optional skills offer from bootstrap to project-init"
```

---

## Task 6: Move CLAUDE.md and AGENTS.md into the plugin reference directory

**Files:**
- Move: `CLAUDE.md` → `plugins/ai-stack/reference/CLAUDE.md`
- Move: `AGENTS.md` → `plugins/ai-stack/reference/AGENTS.md`
- Create symlink: `CLAUDE.md` → `plugins/ai-stack/reference/CLAUDE.md`
- Create symlink: `AGENTS.md` → `plugins/ai-stack/reference/AGENTS.md`

The pattern matches `compose.yaml` and `env.example`: canonical files live in `plugins/ai-stack/reference/`, repo root files are symlinks. This makes the files distributable with the plugin while keeping them editable in the repo.

- [ ] **Step 1: Move CLAUDE.md into reference and replace with symlink**

```bash
cp CLAUDE.md plugins/ai-stack/reference/CLAUDE.md
rm CLAUDE.md
ln -s plugins/ai-stack/reference/CLAUDE.md CLAUDE.md
```

- [ ] **Step 2: Move AGENTS.md into reference and replace with symlink**

```bash
cp AGENTS.md plugins/ai-stack/reference/AGENTS.md
rm AGENTS.md
ln -s plugins/ai-stack/reference/AGENTS.md AGENTS.md
```

- [ ] **Step 3: Verify symlinks resolve correctly**

```bash
ls -la CLAUDE.md AGENTS.md
cat CLAUDE.md | head -5
cat AGENTS.md | head -5
```

Expected: both show as symlinks (`->`) pointing to `plugins/ai-stack/reference/`, and `cat` outputs the original file content.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md AGENTS.md plugins/ai-stack/reference/CLAUDE.md plugins/ai-stack/reference/AGENTS.md
git commit -m "feat(ai-stack): move CLAUDE.md + AGENTS.md into plugin reference, symlink from root"
```

---

## Task 7: Update skills.yaml for project scope

**Files:**
- Modify: `plugins/ai-stack/reference/skills.yaml`

- [ ] **Step 1: Add `scope: project` to both optional skills**

```yaml
skills:
  - name: template-slide-deck
    source: toddward/claude-skills-playground
    path: template-slide-deck
    version: main
    optional: true
    scope: project

  - name: n8n-skills
    source: czlonkowski/n8n-skills
    version: main
    optional: true
    scope: project
```

- [ ] **Step 2: Commit**

```bash
git add plugins/ai-stack/reference/skills.yaml
git commit -m "chore(ai-stack): mark optional skills as project-scoped"
```

---

## Task 8: Create `/ai-stack:project-init` skill

**Files:**
- Create: `plugins/ai-stack/skills/project-init`

- [ ] **Step 1: Write the skill file**

```markdown
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
| CLAUDE.md template | `plugins/ai-stack/reference/CLAUDE.md` |
| AGENTS.md template | `plugins/ai-stack/reference/AGENTS.md` |
| Optional skills | `plugins/ai-stack/reference/skills.yaml` |

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

Read `plugins/ai-stack/reference/skills.yaml`. Collect all entries where `optional: true`.

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
# if path is set:
git -C "$tmpdir" sparse-checkout set <path>
mkdir -p .claude/skills/<name>
cp -r "$tmpdir/<path>/." .claude/skills/<name>/
```

If no `path` field, omit `sparse-checkout set` and copy from `$tmpdir` directly.

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
```

- [ ] **Step 2: Verify the file exists**

```bash
ls plugins/ai-stack/skills/project-init
```

- [ ] **Step 3: Commit**

```bash
git add plugins/ai-stack/skills/project-init
git commit -m "feat(ai-stack): add /ai-stack:project-init skill"
```

---

## Task 9: Bump plugin version

**Files:**
- Modify: `plugins/ai-stack/.claude-plugin/plugin.json`

- [ ] **Step 1: Update version field**

Change `"version": "0.9.0"` to `"version": "0.10.0"`.

- [ ] **Step 2: Verify**

```bash
cat plugins/ai-stack/.claude-plugin/plugin.json
```

Expected: `"version": "0.10.0"`.

- [ ] **Step 3: Commit**

```bash
git add plugins/ai-stack/.claude-plugin/plugin.json
git commit -m "chore(ai-stack): bump plugin version to 0.10.0"
```

---

## Self-review

**Spec coverage:**

| Requirement | Task |
|---|---|
| bootstrap stays as-is | Task 5 only removes Step 8 |
| sandbox skill removed | Task 3 |
| LINCE moves to justfile | Task 2 |
| openshell-* rename | Task 1 |
| lince-bootstrap + lince added | Task 2 |
| just up/down/status removed | Task 1 |
| /ai-stack:up remains | unchanged |
| /ai-stack:down added | Task 4 |
| /ai-stack:project-init added | Task 8 |
| optional skills move to project-init | Tasks 5, 7, 8 |

**All design questions resolved before execution:**

- `just lince` = `zd` ✓
- `just lince-bootstrap` = `cd lince && bash quickstart.sh` ✓
- CLAUDE.md + AGENTS.md = full files moved into plugin reference, symlinked from repo root (same pattern as compose.yaml / env.example) ✓
- `/ai-stack:down` = stop services only, no file cleanup ✓
