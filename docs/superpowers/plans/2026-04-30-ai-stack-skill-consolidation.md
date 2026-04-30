# ai-stack Skill Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate from `mcp-atlassian` to the `atlassian` Claude plugin, consolidate `install-*` skills into `bootstrap`, replace `add-entry` with `modify` (add/update/remove), and delete obsolete skills.

**Architecture:** Registry YAMLs are updated first (source of truth), then obsolete skill directories deleted, then skill files rewritten to match the new design. Track and quarterly plugin updates are independent and can be done in any order relative to tasks 1–8.

**Tech Stack:** Markdown skill files, YAML registry files, bash verification.

---

## File Map

**Modify:**
- `plugins/ai-stack/reference/plugins.yaml` — add 5 entries (4 LSPs + atlassian)
- `plugins/ai-stack/reference/mcps.yaml` — remove mcp-atlassian
- `plugins/ai-stack/reference/bootstrap.yaml` — remove LSP install commands, add lsp_plugins + registry pointers
- `plugins/ai-stack/skills/bootstrap/SKILL.md` — full rewrite (absorbs install-*)
- `plugins/ai-stack/.claude-plugin/plugin.json` — version bump 0.5.0 → 0.6.0
- `CLAUDE.md` — update skill table
- `plugins/track/skills/jira/SKILL.md` — update tool names + cloudId convention
- `plugins/track/README.md` — update mcp-atlassian reference
- `plugins/quarterly/skills/prep/SKILL.md` — update tool names + references
- `plugins/quarterly/README.md` — update mcp-atlassian reference

**Create:**
- `plugins/ai-stack/skills/modify/SKILL.md` — new skill (replaces add-entry)

**Delete:**
- `plugins/ai-stack/skills/add-entry/` — replaced by modify
- `plugins/ai-stack/skills/add-service/` — dropped
- `plugins/ai-stack/skills/add-workflow/` — dropped
- `plugins/ai-stack/skills/install-mcps/` — absorbed into bootstrap
- `plugins/ai-stack/skills/install-plugins/` — absorbed into bootstrap
- `plugins/ai-stack/skills/install-skills/` — absorbed into bootstrap

---

## Task 1: Update plugins.yaml

**Files:**
- Modify: `plugins/ai-stack/reference/plugins.yaml`

- [ ] **Step 1: Add 5 new entries to plugins.yaml**

Append to the end of `plugins/ai-stack/reference/plugins.yaml`:

```yaml
  - name: gopls-lsp
    source: claude-plugins-official

  - name: pyright-lsp
    source: claude-plugins-official

  - name: typescript-lsp
    source: claude-plugins-official

  - name: rust-analyzer-lsp
    source: claude-plugins-official

  - name: atlassian
    source: claude-plugins-official
```

- [ ] **Step 2: Verify**

```bash
grep -c "name:" plugins/ai-stack/reference/plugins.yaml
```
Expected: `7` (context7, superpowers + 5 new)

- [ ] **Step 3: Commit**

```bash
git add plugins/ai-stack/reference/plugins.yaml
git commit -m "chore(ai-stack): add LSP plugins and atlassian to plugins.yaml"
```

---

## Task 2: Update mcps.yaml

**Files:**
- Modify: `plugins/ai-stack/reference/mcps.yaml`

- [ ] **Step 1: Remove the mcp-atlassian block**

Delete these lines from `plugins/ai-stack/reference/mcps.yaml`:

```yaml
  - name: mcp-atlassian
    transport: http
    url: http://localhost:17000/mcp
    scope: user
```

- [ ] **Step 2: Verify**

```bash
grep "mcp-atlassian" plugins/ai-stack/reference/mcps.yaml
```
Expected: no output.

```bash
grep -c "name:" plugins/ai-stack/reference/mcps.yaml
```
Expected: `4` (gmail, gdrive, devlake-prod, devlake-local)

- [ ] **Step 3: Commit**

```bash
git add plugins/ai-stack/reference/mcps.yaml
git commit -m "chore(ai-stack): remove mcp-atlassian from mcps.yaml"
```

---

## Task 3: Update bootstrap.yaml

**Files:**
- Modify: `plugins/ai-stack/reference/bootstrap.yaml`

- [ ] **Step 1: Replace the full file content**

Write `plugins/ai-stack/reference/bootstrap.yaml`:

```yaml
# Source of truth for /ai-stack:bootstrap — what gets checked and installed.
#
# required: true  → prerequisite; skill fails fast if missing (no install command)
# required: false → managed tool; skill installs it if absent

languages:
  go:
    runtime:
      name: go
      check: go version
      required: true
      reason: "Install from https://go.dev/dl/"

  python:
    runtime:
      name: uv
      check: uv --version
      required: false
      install: "curl -LsSf https://astral.sh/uv/install.sh | sh"

  typescript:
    runtime:
      name: node
      check: node --version
      required: true
      reason: "Install from https://nodejs.org/ or via brew"
    package_manager:
      name: pnpm
      check: pnpm --version
      required: false
      install: "npm install -g pnpm"

  rust:
    runtime:
      name: rustup
      check: rustup --version
      required: false
      install: "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y"

# LSP servers are now installed as official Claude plugins
lsp_plugins:
  - gopls-lsp@claude-plugins-official
  - pyright-lsp@claude-plugins-official
  - typescript-lsp@claude-plugins-official
  - rust-analyzer-lsp@claude-plugins-official

# Additional registry files read by bootstrap
plugins: plugins/ai-stack/reference/plugins.yaml
skills:  plugins/ai-stack/reference/skills.yaml
mcps:    plugins/ai-stack/reference/mcps.yaml
```

- [ ] **Step 2: Verify**

```bash
grep "lsp_plugins" plugins/ai-stack/reference/bootstrap.yaml
grep "install:.*gopls\|install:.*pyright\|install:.*typescript-language\|install:.*rust-analyzer" plugins/ai-stack/reference/bootstrap.yaml
```
Expected: first grep finds `lsp_plugins:`, second grep finds no output.

- [ ] **Step 3: Commit**

```bash
git add plugins/ai-stack/reference/bootstrap.yaml
git commit -m "chore(ai-stack): migrate LSPs to plugin entries in bootstrap.yaml"
```

---

## Task 4: Delete obsolete skill directories

**Files:**
- Delete: `plugins/ai-stack/skills/add-entry/`
- Delete: `plugins/ai-stack/skills/add-service/`
- Delete: `plugins/ai-stack/skills/add-workflow/`
- Delete: `plugins/ai-stack/skills/install-mcps/`
- Delete: `plugins/ai-stack/skills/install-plugins/`
- Delete: `plugins/ai-stack/skills/install-skills/`

- [ ] **Step 1: Delete all six directories**

```bash
rm -rf \
  plugins/ai-stack/skills/add-entry \
  plugins/ai-stack/skills/add-service \
  plugins/ai-stack/skills/add-workflow \
  plugins/ai-stack/skills/install-mcps \
  plugins/ai-stack/skills/install-plugins \
  plugins/ai-stack/skills/install-skills
```

- [ ] **Step 2: Verify**

```bash
ls plugins/ai-stack/skills/
```
Expected: `bootstrap  sandbox`

- [ ] **Step 3: Commit**

```bash
git add -A plugins/ai-stack/skills/
git commit -m "chore(ai-stack): delete obsolete add-service, add-workflow, install-* skills"
```

---

## Task 5: Create modify/SKILL.md

**Files:**
- Create: `plugins/ai-stack/skills/modify/SKILL.md`

- [ ] **Step 1: Create the skill directory and file**

```bash
mkdir -p plugins/ai-stack/skills/modify
```

Write `plugins/ai-stack/skills/modify/SKILL.md` with this exact content:

```markdown
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
| plugin — external | `plugins/ai-stack/reference/plugins.yaml` |
| skill | `plugins/ai-stack/reference/skills.yaml` |
| mcp | `plugins/ai-stack/reference/mcps.yaml` |

Version is tracked in `plugins/ai-stack/.claude-plugin/plugin.json`.

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

*mcp* — an MCP server to register with Claude Code:
- `name`: server identifier (kebab-case)
- `transport`: `http`, `sse`, or `stdio`
- `url`: e.g. `http://localhost:PORT/mcp` (http/sse)
- `command` / `args`: (stdio only)
- `headers`: key/value map with `$VAR` references (optional; used for auth tokens)
- `scope`: `user`, `project`, or `local` (default: `user`)

**For `update`:**

Ask for the entry name. Read the current entry from the YAML and display it.
Ask which fields to change; gather new values only for those fields.

**For `remove`:**

Ask for the entry name.

### Step 3: Check entry existence

- **add**: if entry already exists, show it and ask: update it or cancel?
  - If update: treat as `update` from here, with patch version bump
  - If cancel: exit
- **update / remove**: find entry by name in the target file.
  - If not found: show error and exit.

### Step 4: Preview

Show what will change and the version bump. Do not modify any file until the user confirms.

**add / update:**
```
=== MODIFY PREVIEW ===
File:    plugins/ai-stack/reference/<type>s.yaml
Action:  <add new entry | update existing entry>

  - name: <name>
    source: <source>
    version: <version>     # if applicable
    url: <url>             # mcp only
    scope: <scope>         # mcp only

Version: plugins/ai-stack/.claude-plugin/plugin.json
  "version": "<current>" → "<bumped>"
======================
Proceed? (yes / cancel)
```

**remove:**
```
=== MODIFY PREVIEW ===
File:    plugins/ai-stack/reference/<type>s.yaml
Action:  remove entry

  - name: <name>
    ...

Version: plugins/ai-stack/.claude-plugin/plugin.json
  "version": "<current>" → "<bumped>"
======================
Proceed? (yes / cancel)
```

For built-in plugins, show the table row change in this file instead of a YAML block.

### Step 5: Write

On confirmation:

1. **Built-in plugin add**: insert a new row into the built-in table in this file, preserving row order and formatting.
2. **Built-in plugin remove**: delete the matching row from the built-in table in this file.
3. **External plugin / skill / mcp add or update**: append or replace the entry in the target YAML file, preserving existing entries, comments, and formatting.
4. **External plugin / skill / mcp remove**: delete the matching entry block from the YAML file.
5. Read `plugin.json` and bump the version:
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
git add <changed-file> plugins/ai-stack/.claude-plugin/plugin.json
git commit -m "chore(ai-stack): <add|update|remove> <type> <name>"
```
```

- [ ] **Step 2: Verify the file exists and has the correct frontmatter**

```bash
head -5 plugins/ai-stack/skills/modify/SKILL.md
```
Expected:
```
---
description: Add, update, or remove a plugin, skill, or MCP entry in the ai-stack registry, then bump the plugin version.
argument-hint: "[plugin|skill|mcp] [add|update|remove]"
---
```

- [ ] **Step 3: Commit**

```bash
git add plugins/ai-stack/skills/modify/
git commit -m "feat(ai-stack): add modify skill (replaces add-entry, gains update/remove)"
```

---

## Task 6: Rewrite bootstrap/SKILL.md

**Files:**
- Modify: `plugins/ai-stack/skills/bootstrap/SKILL.md`

- [ ] **Step 1: Replace the full file content**

Write `plugins/ai-stack/skills/bootstrap/SKILL.md`:

```markdown
---
description: Full machine setup — installs runtimes, LSP plugins, Claude plugins, skills, and registers MCP servers.
---

# /ai-stack:bootstrap

## Synopsis

```
/ai-stack:bootstrap   ← check prerequisites, then install everything
```

No arguments. Bootstrap is all-or-nothing — installs everything defined across the
four reference files below.

---

## Reference files

| What | File |
|---|---|
| Runtimes + package managers | `plugins/ai-stack/reference/bootstrap.yaml` |
| LSP plugins | `plugins/ai-stack/reference/bootstrap.yaml` (`lsp_plugins` section) |
| Claude plugins | `plugins/ai-stack/reference/plugins.yaml` |
| External skills | `plugins/ai-stack/reference/skills.yaml` |
| MCP servers | `plugins/ai-stack/reference/mcps.yaml` |

Read all files before starting any step.

---

## Process

### Step 1 — Prerequisites check

Run:

```bash
command -v go   && go version   || echo "go: MISSING"
command -v node && node --version || echo "node: MISSING"
```

If either is missing, stop immediately and display:

```
✗ <tool>: not found
  This skill cannot install <tool>.
  Install it from: <reason from bootstrap.yaml>
```

Do not proceed to Step 2.

### Step 2 — Runtimes / package managers

For each managed tool (`uv`, `pnpm`, `rustup`) from `bootstrap.yaml`, in order:

1. Run its `check` command.
2. If already present → record `already installed`.
3. If missing → run its `install` command, then record `installed`.

A failure in one does not stop the others — record `failed` and continue.

### Step 3 — LSP plugins

Check current plugin state:

```bash
claude plugin list
```

For each entry in the `lsp_plugins` section of `bootstrap.yaml`:

- If already installed → record `already installed`.
- If missing → run:
  ```bash
  claude plugin install <name>@<source> --scope user
  ```
  Record `installed` or `failed`.

A failure in one does not stop the rest.

### Step 4 — Claude plugins

Read `plugins/ai-stack/reference/plugins.yaml`. Compare against `claude plugin list` output.

For each plugin not already installed:

```bash
claude plugin install <name>@<source> --scope user
```

Record `already installed` / `installed` / `failed` for each.

### Step 5 — External skills

Read `plugins/ai-stack/reference/skills.yaml`.

For each skill, check user scope first:

```bash
ls ~/.claude/skills/<name> 2>/dev/null && echo "installed" || echo "missing"
```

If already present → record `already installed`.

If missing, install via sparse git checkout:

```bash
tmpdir=$(mktemp -d)
git clone --depth 1 --filter=blob:none --sparse --branch <version> \
    https://github.com/<source> "$tmpdir"
# if path is set:
git -C "$tmpdir" sparse-checkout set <path>
mkdir -p ~/.claude/skills/<name>
cp -r "$tmpdir/<path>/." ~/.claude/skills/<name>/
rm -rf "$tmpdir"
```

If no `path` field, use the repo root (`<path>` = `.`).

Record `installed` or `failed`.

### Step 6 — MCP servers

Check currently registered MCPs:

```bash
claude mcp list
```

Read `plugins/ai-stack/reference/mcps.yaml`. For each MCP:

- If already registered → record `already registered`.
- If `headers` contains `$VAR` references, expand from the current shell environment.
  If a required env var is unset, record `skipped (<VAR> not set)` and skip — do not register with an empty value.
- Otherwise register:
  ```bash
  claude mcp add --transport <transport> --scope <scope> \
    [--header "KEY: VALUE" ...] <name> <url>
  ```
  Record `registered` or `failed`.

### Step 7 — Summary

Print a compact status table covering every item processed:

```
=== BOOTSTRAP SUMMARY ===

Prerequisites:
go                          ok
node                        ok

Runtimes:
uv                          installed
pnpm                        already installed
rustup                      already installed

LSP plugins:
gopls-lsp                   already installed
pyright-lsp                 already installed
typescript-lsp              installed
rust-analyzer-lsp           installed

Plugins:
atlassian                   already installed
context7                    already installed
superpowers                 already installed

Skills:
template-slide-deck         installed
n8n-skills                  failed

MCPs:
gmail                       already registered
gdrive                      registered
devlake-prod-mysql-mcp      skipped (KONFLUX_MCP_SECRET_KEY not set)
devlake-local-mysql-mcp     skipped (DEVLAKE_MCP_SECRET_KEY not set)

=========================
```

If any item shows `failed`, print its error output beneath the table.
```

- [ ] **Step 2: Verify key sections are present**

```bash
grep -c "### Step" plugins/ai-stack/skills/bootstrap/SKILL.md
```
Expected: `7`

- [ ] **Step 3: Commit**

```bash
git add plugins/ai-stack/skills/bootstrap/SKILL.md
git commit -m "feat(ai-stack): rewrite bootstrap to absorb install-plugins, install-skills, install-mcps"
```

---

## Task 7: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Replace the ai-stack skill table rows**

In `CLAUDE.md`, find the skill table under `## Skills & Multi-Agent Coordination`. Replace the entire ai-stack block with:

```markdown
| `/ai-stack:bootstrap` | Full machine setup (runtimes, LSPs, plugins, skills, MCPs) |
| `/ai-stack:modify` | Add, update, or remove a plugin/skill/MCP in the registry |
| `/ai-stack:sandbox` | Install or update the LINCE toolkit |
```

Remove these rows:
- `/ai-stack:add-entry`
- `/ai-stack:add-service`
- `/ai-stack:add-workflow`
- `/ai-stack:install-plugins`
- `/ai-stack:install-skills`
- `/ai-stack:install-mcps`

- [ ] **Step 2: Verify**

```bash
grep "ai-stack" CLAUDE.md
```
Expected output contains only `bootstrap`, `modify`, `sandbox` — no `add-entry`, `install-*`, `add-service`, `add-workflow`.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md skill table for ai-stack consolidation"
```

---

## Task 8: Update track:jira skill

**Files:**
- Modify: `plugins/track/skills/jira/SKILL.md`

- [ ] **Step 1: Update synopsis line**

Change:
```
anything not provided. Uses the `mcp-atlassian` MCP server.
```
To:
```
anything not provided. Uses the `atlassian` plugin.
```

- [ ] **Step 2: Update cloudId derivation in Step 1**

Add this after the `$JIRA_PROJECT` bullet in the "Resolve from env or prompt" list:

```
- `cloudId` — derive from `$JIRA_URL` by stripping `https://`
  (e.g. `https://redhat.atlassian.net` → `redhat.atlassian.net`)
```

- [ ] **Step 3: Update Step 2 (find where it fits)**

Change:
```
1. `jira_search`: find related issues and epics
   ```
   project = <PROJECT> AND text ~ "<topic>" ORDER BY updated DESC
   ```
```
To:
```
1. `searchJiraIssuesUsingJql`: find related issues and epics
   - `cloudId`: derived from `$JIRA_URL`
   - `jql`: `project = <PROJECT> AND text ~ "<topic>" ORDER BY updated DESC`
```

- [ ] **Step 4: Update Step 3 (detect project type)**

Change:
```
Use `jira_search_fields` to discover instance-specific field IDs.
```
To:
```
Use `getJiraProjectIssueTypesMetadata` or `getJiraIssueTypeMetaWithFields` to discover instance-specific field IDs.
```

- [ ] **Step 5: Update Step 4 (draft the issue)**

Change:
```
Compose in plain Markdown (converted to ADF automatically by `mcp-atlassian`):
```
To:
```
Compose in plain Markdown — pass `contentFormat: "markdown"` to the atlassian plugin tools; no manual ADF conversion needed:
```

- [ ] **Step 6: Update Step 6 (submit)**

Replace the three tool calls:
```
1. `jira_create_issue` — all fields including labels via `additional_fields`
   - Team-managed: `parent` as a plain string `"PROJ-123"` (not a dict)
   - Classic: use the Epic Link field ID from `reference/jira-fields.md`
2. `jira_update_issue` — set story points if applicable
   - Pass `fields={}` when updating only via `additional_fields`; both must be dicts
3. `jira_create_issue_link` — for each related issue (see `reference/jira-link-types.md`)
```
With:
```
1. `createJiraIssue` — pass `cloudId`, `projectKey`, `issueTypeName`, `summary`, `description` with `contentFormat: "markdown"`, and `additional_fields` for labels/priority
   - Team-managed: `parent` as a plain string `"PROJ-123"` (not a dict)
   - Classic: use the Epic Link field ID from `reference/jira-fields.md`
2. `editJiraIssue` — set story points if applicable
   - Pass `fields: {}` when updating only via `additional_fields`; both must be dicts
3. `createIssueLink` — for each related issue (see `reference/jira-link-types.md`)
```

- [ ] **Step 7: Update Troubleshooting section**

Apply these replacements throughout the Troubleshooting section:
- `jira_update_issue` → `editJiraIssue`
- `jira_search_fields` → `getJiraIssueTypeMetaWithFields`
- `jira_search` → `searchJiraIssuesUsingJql`

- [ ] **Step 8: Verify no old tool names remain**

```bash
grep "jira_search\|jira_create\|jira_update\|jira_link\|mcp-atlassian" \
  plugins/track/skills/jira/SKILL.md
```
Expected: no output.

- [ ] **Step 9: Commit**

```bash
git add plugins/track/skills/jira/SKILL.md
git commit -m "feat(track): migrate jira skill from mcp-atlassian to atlassian plugin"
```

---

## Task 9: Update track/README.md

**Files:**
- Modify: `plugins/track/README.md`

- [ ] **Step 1: Replace mcp-atlassian reference**

Change:
```
- `mcp-atlassian` — for `/track:jira`
```
To:
```
- `atlassian` plugin — for `/track:jira`
```

- [ ] **Step 2: Verify**

```bash
grep "atlassian" plugins/track/README.md
```
Expected: `- \`atlassian\` plugin — for \`/track:jira\``

- [ ] **Step 3: Commit**

```bash
git add plugins/track/README.md
git commit -m "docs(track): update atlassian dependency from MCP to plugin"
```

---

## Task 10: Update quarterly:prep skill

**Files:**
- Modify: `plugins/quarterly/skills/prep/SKILL.md`

- [ ] **Step 1: Update MCP server reference in synopsis**

Change line 17:
```
Uses MCP servers: `gmail`, `mcp-atlassian`, `gdrive`.
```
To:
```
Uses MCP servers: `gmail`, `gdrive`. Uses plugin: `atlassian`.
```

- [ ] **Step 2: Update Step 3 (Jira activity)**

Change:
```
Read `$JIRA_URL` from environment. Run JQL queries in parallel via `jira_search`.
```
To:
```
Read `$JIRA_URL` from environment. Derive `cloudId` by stripping `https://` from the URL
(e.g. `https://redhat.atlassian.net` → `redhat.atlassian.net`).
Run JQL queries in parallel via `searchJiraIssuesUsingJql` with `cloudId` on each call.
```

- [ ] **Step 3: Update Error handling section**

Change:
```
**Jira currentUser() fails** — use `jira_get_user_profile` to verify account, then substitute username directly.
```
To:
```
**Jira currentUser() fails** — use `atlassianUserInfo` to verify the account, then substitute the `account_id` directly in the JQL.
```

- [ ] **Step 4: Verify no old tool names remain**

```bash
grep "mcp-atlassian\|jira_search\|jira_get_user_profile" \
  plugins/quarterly/skills/prep/SKILL.md
```
Expected: no output.

- [ ] **Step 5: Commit**

```bash
git add plugins/quarterly/skills/prep/SKILL.md
git commit -m "feat(quarterly): migrate prep skill from mcp-atlassian to atlassian plugin"
```

---

## Task 11: Update quarterly/README.md

**Files:**
- Modify: `plugins/quarterly/README.md`

- [ ] **Step 1: Update MCP server list**

Change:
```
MCP servers: `gmail`, `mcp-atlassian`, `gdrive`
```
To:
```
MCP servers: `gmail`, `gdrive`. Plugin: `atlassian`
```

- [ ] **Step 2: Verify**

```bash
grep "atlassian\|mcp-atlassian" plugins/quarterly/README.md
```
Expected: line with `Plugin: \`atlassian\`` — no `mcp-atlassian`.

- [ ] **Step 3: Commit**

```bash
git add plugins/quarterly/README.md
git commit -m "docs(quarterly): update atlassian dependency from MCP to plugin"
```

---

## Task 12: Version bump and final commit

**Files:**
- Modify: `plugins/ai-stack/.claude-plugin/plugin.json`

- [ ] **Step 1: Bump version to 0.6.0**

In `plugins/ai-stack/.claude-plugin/plugin.json`, change:
```json
"version": "0.5.0"
```
To:
```json
"version": "0.6.0"
```

- [ ] **Step 2: Verify**

```bash
cat plugins/ai-stack/.claude-plugin/plugin.json | grep version
```
Expected: `"version": "0.6.0"`

- [ ] **Step 3: Verify no remaining references to deleted skills**

```bash
grep -r "add-entry\|add-service\|add-workflow\|install-mcps\|install-plugins\|install-skills\|mcp-atlassian" \
  plugins/ CLAUDE.md --include="*.md" --include="*.yaml" --include="*.json" -l
```
Expected: only `docs/superpowers/specs/2026-04-30-ai-stack-skill-consolidation-design.md` (the spec itself) — no live skill or config files.

- [ ] **Step 4: Verify skill directory is clean**

```bash
ls plugins/ai-stack/skills/
```
Expected: `bootstrap  modify  sandbox`

- [ ] **Step 5: Final commit**

```bash
git add plugins/ai-stack/.claude-plugin/plugin.json
git commit -m "chore(ai-stack): bump version to 0.6.0 for skill consolidation"
```
