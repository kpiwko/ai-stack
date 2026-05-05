# ai-stack:up Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an `ai-stack:up` skill that starts the container stack from wherever the user is, without requiring them to clone the repo.

**Architecture:** `compose.yaml` and `env.example` move into `plugins/ai-stack/reference/` (the canonical home), with symlinks at the repo root so local workflows are unaffected. The `ai-stack:up` skill copies those files from `${CLAUDE_PLUGIN_ROOT}/reference/` when they're missing in CWD, then runs `podman compose up -d`.

**Tech Stack:** Bash (skill steps), Claude Code skill markdown (SKILL.md), git symlinks.

---

## File Map

| Action | Path | Purpose |
|--------|------|---------|
| Create | `plugins/ai-stack/reference/compose.yaml` | Canonical compose file, shipped with the plugin |
| Create | `plugins/ai-stack/reference/env.example` | Updated env template, shipped with the plugin |
| Convert | `compose.yaml` | Root symlink → `plugins/ai-stack/reference/compose.yaml` |
| Convert | `env.example` | Root symlink → `plugins/ai-stack/reference/env.example` |
| Create | `plugins/ai-stack/skills/up/SKILL.md` | The new skill |
| Modify | `plugins/ai-stack/README.md` | Add `ai-stack:up` to commands table |
| Modify | `CLAUDE.md` | Add `ai-stack:up` to skills table |
| Modify | `plugins/ai-stack/.claude-plugin/plugin.json` | Minor version bump |

---

### Task 1: Move reference files into plugin, replace root files with symlinks

**Context:** `compose.yaml` (158 lines) and `env.example` live at the repo root today. `env.example` is stale — it still references `GMAIL_CLIENT_ID/SECRET` and `gdrive-mcp`, both replaced by `workspace-mcp`. This task moves both into `plugins/ai-stack/reference/` and replaces the originals with relative symlinks so all existing local workflows (`podman compose up`, editors, CI) keep working unchanged.

**Files:**
- Create: `plugins/ai-stack/reference/compose.yaml`
- Create: `plugins/ai-stack/reference/env.example`
- Convert: `compose.yaml` (regular file → symlink)
- Convert: `env.example` (regular file → symlink)

- [ ] **Step 1: Copy compose.yaml into the reference directory**

```bash
cp compose.yaml plugins/ai-stack/reference/compose.yaml
```

Verify:
```bash
diff compose.yaml plugins/ai-stack/reference/compose.yaml
```
Expected: no output (identical).

- [ ] **Step 2: Write the updated env.example into the reference directory**

The current `env.example` at the repo root references `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, and `gdrive-mcp` — all removed. Create the replacement at `plugins/ai-stack/reference/env.example` with this exact content:

```bash
cat > plugins/ai-stack/reference/env.example << 'EOF'
# ai-stack compose — environment variables template
# Copy to .env and fill in your secrets.  NEVER commit .env — it is gitignored.
#
# Generate random secret keys with:  openssl rand -hex 16

###############################################################################
# workspace-mcp  (Google Workspace — Gmail, Drive, Calendar, Docs, Sheets …)
# OAuth client from Google Cloud Console → APIs & Services → Credentials
# Redirect URI to register: http://localhost:17150/oauth2callback
###############################################################################
GOOGLE_OAUTH_CLIENT_ID=<your-client-id>.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=<your-client-secret>

###############################################################################
# AI Beacon  (session manager — port 17090)
###############################################################################
AI_BEACON_AUTH_PASSWORD=demo

###############################################################################
# mcp-atlassian  (Jira MCP — port 17000)
# JIRA_API_TOKEN: personal access token from Jira profile settings
###############################################################################
JIRA_URL=https://redhat.atlassian.net
JIRA_USERNAME=<your-email@example.com>
JIRA_API_TOKEN=<your-personal-access-token>

###############################################################################
# devlake-local-mysql-mcp  (local DevLake DB — port 17301)
# Connects to DevLake MySQL running on host port 3306
###############################################################################
DEVLAKE_MYSQL_USER=merico
DEVLAKE_MYSQL_PASSWORD=merico
DEVLAKE_MCP_SECRET_KEY=<openssl rand -hex 16>

###############################################################################
# devlake-prod-mysql-mcp  (remote Konflux RDS — port 17300)
###############################################################################
KONFLUX_MYSQL_HOST=<rds-endpoint.region.rds.amazonaws.com>
KONFLUX_MYSQL_PORT=3306
KONFLUX_MYSQL_USER=<db-user>
KONFLUX_MYSQL_PASS=<db-password>
KONFLUX_MYSQL_DB=lake
KONFLUX_MCP_SECRET_KEY=<openssl rand -hex 16>
EOF
```

- [ ] **Step 3: Replace root compose.yaml with a symlink**

```bash
rm compose.yaml
ln -s plugins/ai-stack/reference/compose.yaml compose.yaml
```

Verify the symlink resolves and the content is still readable:
```bash
ls -la compose.yaml
# expected: compose.yaml -> plugins/ai-stack/reference/compose.yaml

head -5 compose.yaml
# expected: first 5 lines of the compose file (not a path or error)
```

- [ ] **Step 4: Replace root env.example with a symlink**

```bash
rm env.example
ln -s plugins/ai-stack/reference/env.example env.example
```

Verify:
```bash
ls -la env.example
# expected: env.example -> plugins/ai-stack/reference/env.example

grep GOOGLE_OAUTH_CLIENT_ID env.example
# expected: GOOGLE_OAUTH_CLIENT_ID=<your-client-id>.apps.googleusercontent.com
```

- [ ] **Step 5: Stage and verify git sees symlinks, not file content**

```bash
git add compose.yaml env.example plugins/ai-stack/reference/compose.yaml plugins/ai-stack/reference/env.example
git status
```

Expected output should include:
```
new file:   plugins/ai-stack/reference/compose.yaml
new file:   plugins/ai-stack/reference/env.example
modified:   compose.yaml        ← was regular file, now symlink
modified:   env.example         ← was regular file, now symlink
```

If `git status` shows `compose.yaml` as deleted (not modified), the symlink didn't stage properly. Run:
```bash
git add --all compose.yaml env.example
git status
```

- [ ] **Step 6: Verify podman compose can still read the stack via symlink**

```bash
podman compose config --quiet 2>&1 | head -3
```

Expected: no error (returns compose configuration or exits 0).

- [ ] **Step 7: Commit**

```bash
git commit -m "refactor(ai-stack): move compose.yaml and env.example into plugin reference

compose.yaml and env.example are now canonical at
plugins/ai-stack/reference/ and symlinked from the repo root.
This allows the ai-stack:up skill to ship both files with the
plugin so users can start the stack without cloning the repo.

Also updates env.example: removes stale gmail/gdrive-mcp vars,
adds GOOGLE_OAUTH_CLIENT_ID/SECRET for workspace-mcp."
```

---

### Task 2: Create the ai-stack:up skill

**Context:** The skill lives at `plugins/ai-stack/skills/up/SKILL.md`. When invoked, Claude follows the steps in this file. It uses `${CLAUDE_PLUGIN_ROOT}` to locate the reference files — this variable is expanded by Claude Code to the plugin's installed directory regardless of whether the plugin was installed from a marketplace or from a local repo checkout. The skill is idempotent: it skips setup steps when the files already exist and just runs `podman compose up -d`.

**Files:**
- Create: `plugins/ai-stack/skills/up/SKILL.md`

- [ ] **Step 1: Create the skill file**

Create `plugins/ai-stack/skills/up/SKILL.md` with this exact content:

````markdown
---
description: Start the ai-stack container stack. Copies compose.yaml and env.example into CWD if missing, then runs podman compose up -d. Idempotent.
---

# /ai-stack:up

## Synopsis

```
/ai-stack:up   ← set up compose.yaml + .env in CWD, then start all services
```

Idempotent — running again updates services without overwriting existing config files.

---

## Reference files

| What | File |
|---|---|
| Stack definition | `${CLAUDE_PLUGIN_ROOT}/reference/compose.yaml` |
| Environment template | `${CLAUDE_PLUGIN_ROOT}/reference/env.example` |

Read both files before starting any step.

---

## Process

### Step 1 — Prerequisites check

Run:

```bash
command -v podman && podman compose version 2>/dev/null && echo "podman" \
  || command -v docker && docker compose version 2>/dev/null && echo "docker" \
  || echo "MISSING"
```

Record which tool is available (`podman` or `docker`). Use that tool for all compose
commands in subsequent steps.

If neither is found, stop and display:

```
✗ podman / docker compose: not found
  Install Podman Desktop: https://podman-desktop.io/
  or Docker Desktop:      https://www.docker.com/products/docker-desktop/
```

### Step 2 — Handle compose.yaml

Check if `compose.yaml` exists in the current directory:

```bash
ls compose.yaml 2>/dev/null && echo "exists" || echo "missing"
```

If **exists** → record `compose.yaml: found` and skip.

If **missing** → copy from the plugin:

```bash
cp "${CLAUDE_PLUGIN_ROOT}/reference/compose.yaml" compose.yaml
```

Record `compose.yaml: created`.

### Step 3 — Handle .env

Check if `.env` exists in the current directory:

```bash
ls .env 2>/dev/null && echo "exists" || echo "missing"
```

If **missing** → copy the template:

```bash
cp "${CLAUDE_PLUGIN_ROOT}/reference/env.example" .env
```

Record `.env: created from env.example`.

In both cases — scan `.env` for lines that still contain a placeholder value
(angle brackets indicate a value that was never filled in):

```bash
grep -E '^[A-Z_]+=.*<[^>]+>' .env || true
```

If any placeholder lines are found, display:

```
⚠ Fill in these variables in .env before the affected services will connect:

  GOOGLE_OAUTH_CLIENT_ID      workspace-mcp (Google OAuth)
  GOOGLE_OAUTH_CLIENT_SECRET  workspace-mcp (Google OAuth)
  JIRA_USERNAME               mcp-atlassian
  JIRA_API_TOKEN              mcp-atlassian
  DEVLAKE_MCP_SECRET_KEY      devlake-local-mysql-mcp
  KONFLUX_MYSQL_HOST          devlake-prod-mysql-mcp
  KONFLUX_MCP_SECRET_KEY      devlake-prod-mysql-mcp

  Edit .env and re-run /ai-stack:up when ready.
```

Only show the variables that actually appeared in the `grep` output — do not
show variables that are already set to real values.

Proceed to Step 4 regardless. Services with missing vars will start but not connect.

### Step 4 — Start services

Run:

```bash
podman compose up -d   # or: docker compose up -d
```

If compose exits non-zero, print the error and stop.

### Step 5 — Summary

Run:

```bash
podman compose ps   # or: docker compose ps
```

Print a formatted summary:

```
=== ai-stack UP ===

Service                   Status     Endpoint
───────────────────────────────────────────────────────────
ai-beacon                 running    http://localhost:17090
mcp-atlassian             running    http://localhost:17000/mcp
notebooklm-mcp            running    http://localhost:17200/mcp
                                     noVNC: http://localhost:17201/vnc.html
workspace-mcp             running    http://localhost:17150/mcp
devlake-local-mysql-mcp   running    http://localhost:17301/mcp
devlake-prod-mysql-mcp    running    http://localhost:17300/mcp

Config: <absolute path to CWD>/.env
====================================
```

For any service that shows `exited` or `error` in `compose ps`, add a line:

```
✗ <service-name>: exited — check its required variables in .env
```
````

- [ ] **Step 2: Verify the file was created correctly**

```bash
head -5 plugins/ai-stack/skills/up/SKILL.md
```

Expected:
```
---
description: Start the ai-stack container stack. Copies compose.yaml and env.example into CWD if missing, then runs podman compose up -d. Idempotent.
---

# /ai-stack:up
```

- [ ] **Step 3: Commit**

```bash
git add plugins/ai-stack/skills/up/SKILL.md
git commit -m "feat(ai-stack): add ai-stack:up skill

Copies compose.yaml and .env into CWD if missing (sourced from the
plugin's reference directory), then runs podman/docker compose up -d.
Idempotent — safe to run repeatedly."
```

---

### Task 3: Update docs and bump version

**Context:** The plugin README and repo CLAUDE.md both have a commands/skills table. Both need a row for `ai-stack:up`. The plugin version in `plugin.json` gets a minor bump (new skill = new feature).

**Files:**
- Modify: `plugins/ai-stack/README.md`
- Modify: `CLAUDE.md`
- Modify: `plugins/ai-stack/.claude-plugin/plugin.json`

- [ ] **Step 1: Add ai-stack:up to plugin README**

Current `plugins/ai-stack/README.md` commands table:

```markdown
| Command | Description |
|---|---|
| `/ai-stack:bootstrap` | Full machine setup (runtimes, LSPs, plugins, skills, MCPs) |
| `/ai-stack:modify [plugin\|skill\|mcp] [add\|update\|remove]` | Add, update, or remove a registry entry |
| `/ai-stack:sandbox` | Install or update the LINCE toolkit |
```

Replace with:

```markdown
| Command | Description |
|---|---|
| `/ai-stack:up` | Start the container stack (copies compose.yaml + .env if missing, then `podman compose up -d`) |
| `/ai-stack:bootstrap` | Full machine setup (runtimes, LSPs, plugins, skills, MCPs) |
| `/ai-stack:modify [plugin\|skill\|mcp] [add\|update\|remove]` | Add, update, or remove a registry entry |
| `/ai-stack:sandbox` | Install or update the LINCE toolkit |
```

- [ ] **Step 2: Add ai-stack:up to CLAUDE.md**

The skills table in `CLAUDE.md` currently has:

```markdown
| `/ai-stack:bootstrap` | Full machine setup (runtimes, LSPs, plugins, skills, MCPs) |
| `/ai-stack:modify` | Add, update, or remove a plugin/skill/MCP in the registry |
| `/ai-stack:sandbox` | Install or update the LINCE toolkit |
```

Add a row for `ai-stack:up` before `ai-stack:bootstrap`:

```markdown
| `/ai-stack:up` | Start the container stack (idempotent; copies compose.yaml + .env if missing) |
| `/ai-stack:bootstrap` | Full machine setup (runtimes, LSPs, plugins, skills, MCPs) |
| `/ai-stack:modify` | Add, update, or remove a plugin/skill/MCP in the registry |
| `/ai-stack:sandbox` | Install or update the LINCE toolkit |
```

- [ ] **Step 3: Bump plugin.json version**

Read `plugins/ai-stack/.claude-plugin/plugin.json`. Current version is `0.8.0`.

New version: `0.9.0` (minor bump — new skill added).

Edit the `"version"` field:

```json
{
  "name": "ai-stack",
  "description": "Maintenance commands for the ai-stack repo: scaffold services, workflows, and verify image references.",
  "version": "0.9.0",
  "author": {
    "name": "Karel Piwko"
  },
  "repository": "https://github.com/kpiwko/ai-stack"
}
```

- [ ] **Step 4: Verify all three files changed**

```bash
git diff --stat plugins/ai-stack/README.md CLAUDE.md plugins/ai-stack/.claude-plugin/plugin.json
```

Expected: all three files show changes.

- [ ] **Step 5: Commit**

```bash
git add plugins/ai-stack/README.md CLAUDE.md plugins/ai-stack/.claude-plugin/plugin.json
git commit -m "chore(ai-stack): add ai-stack:up to docs, bump version to 0.9.0"
```

- [ ] **Step 6: Push all three commits**

```bash
git push
```

Expected: `main -> main` with 3 new commits.

---

## Manual smoke test (after all tasks complete)

Run this from a temporary directory that does **not** have a `compose.yaml`:

```bash
mkdir /tmp/ai-stack-test && cd /tmp/ai-stack-test
```

Then invoke `/ai-stack:up` in Claude Code. Expected sequence:

1. Skill detects `podman` is available
2. `compose.yaml: created` (copied from plugin reference)
3. `.env: created from env.example` (copied from plugin reference)
4. Placeholder warning lists `GOOGLE_OAUTH_CLIENT_ID`, `JIRA_API_TOKEN`, etc.
5. `podman compose up -d` runs and services start
6. Summary table shows all services with their ports

Then run `/ai-stack:up` a second time from the same directory — expected: compose.yaml and .env are NOT re-created (files already exist), services are updated in place.

Clean up:
```bash
cd /tmp && rm -rf ai-stack-test
```
