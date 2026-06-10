# DevLake MCP Rename, Staging Addition, and Scope Migration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename all DevLake MySQL MCP services to a consistent `devlake-mysql-{local,staging,prod}` naming pattern, add a staging environment, reassign ports to 17300/17310/17320, rename all env vars to `DEVLAKE_{LOCAL,STAGING,PROD}_*`, and migrate MCP registration scope from `local` (→ `.claude.json`) to `project` (→ `.mcp.json`).

**Architecture:** Three identical MCP proxy containers (same image, different env vars) behind consecutive port blocks. Each connects to a different MySQL instance — local DevLake on host:3306, staging RDS, and prod RDS. Project-scoped MCP registration keeps bearer tokens in `.mcp.json` (gitignored) rather than the shared `.claude.json`.

**Tech Stack:** Podman Compose, `ghcr.io/kpiwko/mcp-mysql:latest` image, Claude Code CLI (`claude mcp add/remove`), YAML/Markdown skill files.

---

## Motivation

The original setup had two MCP services with inconsistent naming and confusing env var prefixes:

| Before | Port | Env prefix |
|---|---|---|
| `devlake-local-mysql-mcp` | 17301 | `DEVLAKE_MYSQL_*` |
| `devlake-prod-mysql-mcp` | 17300 | `KONFLUX_MYSQL_*` |

Problems:
1. **No staging environment** — we need read-only access to the Konflux staging RDS for cross-environment DevLake analysis.
2. **Inconsistent naming** — service names mixed word order (`local-mysql-mcp` vs `prod-mysql-mcp`), and the `KONFLUX_*` env prefix was confusing since both local and prod are DevLake instances.
3. **Port assignment was backwards** — prod had the "base" port 17300 and local had 17301, which is counterintuitive.
4. **`scope: local` wrote to `.claude.json`** — this file is shared and not gitignored. Project-scoped MCPs should go to `.mcp.json` (gitignored), since the expanded bearer tokens are secrets.

## Design Decisions

1. **Naming convention:** `devlake-mysql-{environment}` — entity first, then qualifier. Consistent with how compose services, env vars, MCP names, and OpenShell policies all reference the same logical service.

2. **Port scheme:** 17300 (local), 17310 (staging), 17320 (prod) — 10-port gaps allow room for future sidecar services per environment without collisions.

3. **Env var convention:** `DEVLAKE_{LOCAL,STAGING,PROD}_{MYSQL_HOST,MYSQL_PORT,MYSQL_USER,MYSQL_PASS,MYSQL_DB,MCP_SECRET_KEY}` — uniform prefix makes it obvious which service each var feeds.

4. **Scope migration:** `scope: project` writes to `.mcp.json` via `claude mcp add --scope project`. This file is per-project and gitignored. The old `scope: local` wrote to `.claude.json` which is a user-level config — wrong place for project-specific secrets.

5. **Bootstrap → project-init handoff:** Bootstrap skips `scope: project` MCPs and optional skills with a single closing line: `Run /ai-stack:project-init in your project to install optional skills and register project-scoped MCPs.` This replaces the previous per-item `(scope: local — run /ai-stack:project-init)` hints.

6. **No `scope: local` anywhere:** The `local` scope value is removed from all documentation and registry comments. Only `user` and `project` are valid scopes. All skills in `skills.yaml` are `optional: true` + `scope: project` — there are no user-scoped or non-optional external skills.

---

### Task 1: Rename services and env vars in compose.yaml

**Files:**
- Modify: `plugins/ai-stack/reference/compose.yaml` (canonical)
- Modify: `compose.yaml` (root copy — regular file, not symlink)

- [ ] **Step 1: Rename `devlake-local-mysql-mcp` → `devlake-mysql-local`**

Change the service name, comments, and env vars:
- Service key: `devlake-mysql-local`
- Port: `17301:3000` → `17300:3000`
- `MYSQL_USER`: `${DEVLAKE_MYSQL_USER:-merico}` → `${DEVLAKE_LOCAL_MYSQL_USER:-merico}`
- `MYSQL_PASS`: `${DEVLAKE_MYSQL_PASSWORD:-merico}` → `${DEVLAKE_LOCAL_MYSQL_PASS:-merico}`
- `REMOTE_SECRET_KEY`: `${DEVLAKE_MCP_SECRET_KEY}` → `${DEVLAKE_LOCAL_MCP_SECRET_KEY}`

- [ ] **Step 2: Rename `devlake-prod-mysql-mcp` → `devlake-mysql-prod`**

Change the service name, comments, and env vars:
- Service key: `devlake-mysql-prod`
- Port: `17300:3000` → `17320:3000`
- All `KONFLUX_*` env refs → `DEVLAKE_PROD_*`

- [ ] **Step 3: Add `devlake-mysql-staging` service**

Clone the prod service block with staging-specific values:
- Port: `17310:3000`
- All env refs: `DEVLAKE_STAGING_*`

- [ ] **Step 4: Apply identical changes to root `compose.yaml`**

The root `compose.yaml` is a regular file (not a symlink to the reference). Apply the same three changes.

- [ ] **Step 5: Verify compose parses**

```bash
podman compose -f compose.yaml config --quiet && echo "ok"
```
Expected: `ok` (no parse errors)

- [ ] **Step 6: Commit**

```bash
git add plugins/ai-stack/reference/compose.yaml compose.yaml
git commit -m "refactor: rename devlake MCP services, add staging, reassign ports"
```

---

### Task 2: Update env.example

**Files:**
- Modify: `plugins/ai-stack/reference/env.example`

- [ ] **Step 1: Rename local section**

Change heading to `devlake-mysql-local (local DevLake DB — port 17300)`.
Rename vars: `DEVLAKE_LOCAL_MYSQL_USER`, `DEVLAKE_LOCAL_MYSQL_PASS`, `DEVLAKE_LOCAL_MCP_SECRET_KEY`.

- [ ] **Step 2: Rename prod section**

Change heading to `devlake-mysql-prod (Konflux prod RDS — port 17320)`.
Rename all `KONFLUX_*` vars to `DEVLAKE_PROD_*`.

- [ ] **Step 3: Add staging section**

Insert between local and prod with heading `devlake-mysql-staging (Konflux staging RDS — port 17310)`.
Vars: `DEVLAKE_STAGING_MYSQL_HOST`, `DEVLAKE_STAGING_MYSQL_PORT`, `DEVLAKE_STAGING_MYSQL_USER`, `DEVLAKE_STAGING_MYSQL_PASS`, `DEVLAKE_STAGING_MYSQL_DB`, `DEVLAKE_STAGING_MCP_SECRET_KEY`.

- [ ] **Step 4: Commit**

```bash
git add plugins/ai-stack/reference/env.example
git commit -m "refactor: rename env vars to DEVLAKE_{LOCAL,STAGING,PROD}_* pattern"
```

---

### Task 3: Update .env with real credentials

**Files:**
- Modify: `.env` (gitignored, contains secrets)

- [ ] **Step 1: Rename existing local vars**

`DEVLAKE_MYSQL_USER` → `DEVLAKE_LOCAL_MYSQL_USER`, etc.

- [ ] **Step 2: Rename existing prod vars**

`KONFLUX_*` → `DEVLAKE_PROD_*`.

- [ ] **Step 3: Add staging placeholders**

Add `DEVLAKE_STAGING_*` vars. User fills in real values manually.

- [ ] **Step 4: Recreate containers to pick up new env vars**

```bash
podman compose down --remove-orphans
podman compose up -d
```

The `--remove-orphans` flag is required because the old service names leave orphan containers.

**Do not commit** — `.env` is gitignored.

---

### Task 4: Update mcps.yaml — rename entries and change scope

**Files:**
- Modify: `plugins/ai-stack/reference/mcps.yaml`

- [ ] **Step 1: Rename entries and update URLs/headers**

- `devlake-prod-mysql-mcp` → `devlake-mysql-prod` (url: port 17320, header: `$DEVLAKE_PROD_MCP_SECRET_KEY`)
- `devlake-local-mysql-mcp` → `devlake-mysql-local` (url: port 17300, header: `$DEVLAKE_LOCAL_MCP_SECRET_KEY`)
- Add `devlake-mysql-staging` (url: port 17310, header: `$DEVLAKE_STAGING_MCP_SECRET_KEY`)

- [ ] **Step 2: Change scope from `local` to `project`**

All three devlake entries: `scope: local` → `scope: project`.

- [ ] **Step 3: Update the header comment**

Change `scope: user | project | local` → `scope: user | project` in the format documentation comment.

- [ ] **Step 4: Commit**

```bash
git add plugins/ai-stack/reference/mcps.yaml
git commit -m "refactor: rename devlake MCPs, change scope local→project"
```

---

### Task 5: Update project-init skill

**Files:**
- Modify: `plugins/ai-stack/skills/project-init/SKILL.md`

- [ ] **Step 1: Update description frontmatter**

`registers local MCP servers` → `registers project-scoped MCP servers`

- [ ] **Step 2: Update reference table**

`Local MCP servers` → `Project MCP servers`

- [ ] **Step 3: Update Step 3.5 — filter and terminology**

- Heading: `Check local MCP servers` → `Check project MCP servers`
- Filter: `scope: local` → `scope: project`
- Body text: `local MCP` → `project MCP`

- [ ] **Step 4: Add Step 3.6 — Ensure .mcp.json is in .gitignore**

Project-scoped MCPs write to `.mcp.json` which contains expanded bearer tokens. Add a step that checks `.gitignore` for `.mcp.json` and appends it if missing:

```bash
grep -qxF '.mcp.json' .gitignore 2>/dev/null && echo "present" || echo "missing"
```

- [ ] **Step 5: Update Step 6 — registration scope**

- Heading: `Local MCP servers offer` → `Project MCP servers offer`
- AskUserQuestion header: `Local MCPs` → `Project MCPs`
- Registration command: `--scope local` → `--scope project`
- All body text: `local` → `project` where referring to scope

- [ ] **Step 6: Update example output**

Update service names in Step 4 summary and Step 6 confirmation examples to `devlake-mysql-{local,staging,prod}`.

- [ ] **Step 7: Commit**

```bash
git add plugins/ai-stack/skills/project-init/SKILL.md
git commit -m "refactor: project-init uses scope:project, adds .mcp.json to .gitignore"
```

---

### Task 6: Update bootstrap skill

**Files:**
- Modify: `plugins/ai-stack/skills/bootstrap/SKILL.md`

- [ ] **Step 1: Update Step 6 filter description**

`Entries with scope: local are skipped` → `Entries with scope: project are skipped`

- [ ] **Step 2: Update summary example**

- Skill rows: `skipped (install via /ai-stack:project-init)` → `skipped (optional)`
  (This matches the actual Step 5 logic which records `skipped (optional)` for `optional: true` entries.)
- MCP rows: update service names to `devlake-mysql-{local,staging,prod}`, status to `skipped (scope: project)`
- Add closing line after the summary fence: `Run /ai-stack:project-init in your project to install optional skills and register project-scoped MCPs.`

- [ ] **Step 3: Commit**

```bash
git add plugins/ai-stack/skills/bootstrap/SKILL.md
git commit -m "refactor: bootstrap summary uses scope:project, consolidated project-init hint"
```

---

### Task 7: Update remaining skills and docs

**Files:**
- Modify: `plugins/ai-stack/skills/up/SKILL.md`
- Modify: `plugins/ai-stack/skills/status/SKILL.md`
- Modify: `plugins/ai-stack/skills/modify/SKILL.md`
- Modify: `README.md`
- Modify: `openshell/policy.yaml`
- Modify: `plugins/ai-stack/evals/promptfooconfig-bootstrap.yaml`
- Modify: `.gitignore`

- [ ] **Step 1: Update up skill**

- Env var warning table: rename all vars from `DEVLAKE_MCP_SECRET_KEY`/`KONFLUX_*` to `DEVLAKE_{LOCAL,STAGING,PROD}_*`
- Add staging vars to the warning table
- Update summary example: new service names, ports 17300/17310/17320

- [ ] **Step 2: Update status skill**

- Update example output: new service names, ports

- [ ] **Step 3: Update modify skill**

- MCP scope field documentation: `user`, `project`, or `local` → `user` or `project`

- [ ] **Step 4: Update README.md**

- Service table: new names, ports, descriptions (add staging row)
- `devlake-local-mysql-mcp` section heading → `devlake-mysql-local`
- Env var references: `$DEVLAKE_MCP_SECRET_KEY` → `$DEVLAKE_LOCAL_MCP_SECRET_KEY`
- Registration command: `via /ai-stack:bootstrap` → `via /ai-stack:project-init`

- [ ] **Step 5: Update OpenShell network policies**

- Rename policy keys and names: `devlake-local-mcp` → `devlake-mysql-local`, `devlake-prod-mcp` → `devlake-mysql-prod`
- Update ports: local=17300, prod=17320
- Add `devlake-mysql-staging` policy on port 17310

- [ ] **Step 6: Update bootstrap evals**

- `DEVLAKE_MCP_SECRET_KEY` → `DEVLAKE_LOCAL_MCP_SECRET_KEY` in the unset-env-var test

- [ ] **Step 7: Add `.mcp.json` to `.gitignore`**

Append `.mcp.json` to `.gitignore` so project-scoped MCP registrations (which contain expanded bearer tokens) are not committed.

- [ ] **Step 8: Commit**

```bash
git add plugins/ai-stack/skills/up/SKILL.md plugins/ai-stack/skills/status/SKILL.md \
  plugins/ai-stack/skills/modify/SKILL.md README.md openshell/policy.yaml \
  plugins/ai-stack/evals/promptfooconfig-bootstrap.yaml .gitignore
git commit -m "refactor: update all docs and policies for devlake-mysql-* rename"
```

---

### Task 8: Re-register MCPs with project scope

**Files:**
- Side effect: `.claude.json` (removes old entries)
- Side effect: `.mcp.json` (creates with new entries, gitignored)

- [ ] **Step 1: Remove old local-scope registrations**

```bash
claude mcp remove devlake-mysql-local --scope local
claude mcp remove devlake-mysql-staging --scope local
claude mcp remove devlake-mysql-prod --scope local
```

Note: use `--scope local` for removal because the old registrations were created with that scope.

- [ ] **Step 2: Re-register with project scope**

Source `.env` first to expand bearer token vars:

```bash
set -a && . ./.env && set +a
claude mcp add devlake-mysql-local http://localhost:17300/mcp \
  --transport http --scope project \
  -H "Authorization: Bearer $DEVLAKE_LOCAL_MCP_SECRET_KEY"

claude mcp add devlake-mysql-staging http://localhost:17310/mcp \
  --transport http --scope project \
  -H "Authorization: Bearer $DEVLAKE_STAGING_MCP_SECRET_KEY"

claude mcp add devlake-mysql-prod http://localhost:17320/mcp \
  --transport http --scope project \
  -H "Authorization: Bearer $DEVLAKE_PROD_MCP_SECRET_KEY"
```

- [ ] **Step 3: Verify registration**

```bash
claude mcp list
```

Expected: all three devlake MCPs show as connected (or pending approval on first session).

- [ ] **Step 4: Update `.claude/settings.local.json` permissions**

Update the MCP tool permission allowlist to match new names:
- `mcp__devlake-mysql-local__mysql_query`
- `mcp__devlake-mysql-staging__mysql_query`
- `mcp__devlake-mysql-prod__mysql_query`

**Do not commit** — `.mcp.json` is gitignored, settings.local.json is user-specific.

---

### Task 9: Verify end-to-end

- [ ] **Step 1: Verify compose services are running**

```bash
podman compose ps
```

Expected: all three `devlake-mysql-*` services running on ports 17300, 17310, 17320.

- [ ] **Step 2: Test MCP connectivity**

```bash
claude mcp list
```

Expected: `devlake-mysql-local`, `devlake-mysql-staging`, `devlake-mysql-prod` all connected.

- [ ] **Step 3: Run a test query against each**

In a Claude session, verify each MCP responds to a simple query:

```sql
SELECT 1 AS test;
```

- [ ] **Step 4: Verify `.mcp.json` is gitignored**

```bash
git status .mcp.json
```

Expected: not listed (ignored).

---

## Files Changed Summary

| File | Change |
|---|---|
| `compose.yaml` | Rename services, add staging, reassign ports |
| `plugins/ai-stack/reference/compose.yaml` | Same (canonical copy) |
| `plugins/ai-stack/reference/env.example` | Rename vars, add staging section |
| `.env` | Rename vars, add staging placeholders (gitignored) |
| `plugins/ai-stack/reference/mcps.yaml` | Rename entries, add staging, scope local→project |
| `plugins/ai-stack/skills/project-init/SKILL.md` | Filter scope:project, register --scope project, add .gitignore step |
| `plugins/ai-stack/skills/bootstrap/SKILL.md` | Skip scope:project, consolidated project-init hint |
| `plugins/ai-stack/skills/up/SKILL.md` | New service names, ports, env vars in warning table |
| `plugins/ai-stack/skills/status/SKILL.md` | New service names, ports in example |
| `plugins/ai-stack/skills/modify/SKILL.md` | Remove `local` from valid scope values |
| `README.md` | Service table, env var refs, section heading |
| `openshell/policy.yaml` | Rename policies, update ports, add staging |
| `plugins/ai-stack/evals/promptfooconfig-bootstrap.yaml` | Env var name in test assertion |
| `.gitignore` | Add `.mcp.json` |
| `.mcp.json` | Created by `claude mcp add --scope project` (gitignored) |
| `.claude/settings.local.json` | MCP tool permissions (user-specific) |

## Historical docs NOT updated

Files in `docs/superpowers/plans/` are point-in-time snapshots of previous work. They reference the old naming and scope conventions intentionally — updating them would misrepresent what was planned at that time.
