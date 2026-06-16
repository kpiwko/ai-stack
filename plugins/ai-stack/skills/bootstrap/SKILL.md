---
description: Full machine setup — installs runtimes, LSP plugins, Claude plugins, skills, and registers MCP servers.
---

# /ai-stack:bootstrap

## Synopsis

```
/ai-stack:bootstrap          ← check prerequisites, then install everything
/ai-stack:bootstrap force    ← reinstall / re-register everything, even if already present
```

Bootstrap runs all steps regardless of individual step failures — only the prerequisites
check (Step 1) is fail-fast. Without `force`, already-installed items are skipped.

---

## Reference files

> **Path resolution:** `../../reference/X` is relative to this skill's base directory.
> Use the absolute path from the `Base directory for this skill:` header: `<base-dir>/../../reference/X`.

| What | File |
|---|---|
| Runtimes + package managers | `../../reference/bootstrap.yaml` |
| LSP plugins | `../../reference/bootstrap.yaml` (`lsp_plugins` section) |
| Claude plugins | `../../reference/plugins.yaml` |
| External skills | `../../reference/skills.yaml` |
| MCP servers | `../../reference/mcps.yaml` |

Read all files before starting any step.

---

## Process

### Step 1 — Prerequisites check

First check if `mise` is installed:

```bash
command -v mise && mise --version || echo "mise: MISSING"
```

Then check go and node:

```bash
command -v go   && go version   || echo "go: MISSING"
command -v node && node --version || echo "node: MISSING"
```

If `mise` is installed but go or node are missing → **do not abort**. Record the missing tools
as `will be installed via mise` and continue to Step 2 (mise will install them).

If `mise` is **not** installed and go or node are missing → stop immediately and display:

```
✗ <tool>: not found
  This skill cannot install <tool> directly.
  Install it from: <reason from bootstrap.yaml>
  Or install mise first (brew install mise) and re-run /ai-stack:bootstrap.
```

Do not proceed to Step 2.

### Step 2 — Runtimes / package managers

**First, handle mise** from the `version_manager` section of `bootstrap.yaml`:

1. Run its `check` command (`command -v mise`).
2. If already present and `force` not passed → record `already installed`, then run:
   ```bash
   mise use --global python@3.12 node@20 go@1.24
   ```
   Record the global_runtimes command as run.
3. If missing, or if `force` was passed → run its `install` command (`brew install mise`), record `installed`, then run:
   ```bash
   mise use --global python@3.12 node@20 go@1.24
   ```
   Record the global_runtimes command as run.

**Then, for each remaining managed tool** (`uv`, `pnpm`, `rustup`) from `bootstrap.yaml`, in order:

1. Run its `check` command.
2. If already present and `force` not passed → record `already installed`.
3. If missing, or if `force` was passed → run its `install` command, then record `installed`.

Most runtime installers are idempotent and safe to re-run. A failure in one does not stop the others — record `FAILED` and continue.

### Step 3 — LSP plugins

Check current plugin state:

```bash
claude plugin list
```

For each entry in the `lsp_plugins` section of `bootstrap.yaml`:

- If already installed and `force` not passed → record `already installed`.
- If missing, or if `force` was passed → run:
  ```bash
  claude plugin install <name>@<source> --scope user
  ```
  where `<name>@<source>` is the full value from the list (e.g. `gopls-lsp@claude-plugins-official`).
  Record `installed` or `FAILED`.

A failure in one does not stop the rest.

### Step 4 — Claude plugins

Read `../../reference/plugins.yaml`. Compare against `claude plugin list` output.

Skip any plugin already processed in Step 3 — they will already be installed, and omitting
them from this section avoids duplicate rows in the summary.

For each remaining plugin:

- If already installed and `force` not passed → record `already installed`.
- If missing, or if `force` was passed → run:
  ```bash
  claude plugin install <name>@<source> --scope user
  ```

Record `already installed` / `installed` / `FAILED` for each.

### Step 5 — External skills

Read `../../reference/skills.yaml`.

For each skill:

- If `optional: true` → record `skipped (optional)` and continue.
- Determine install path:
  - `scope: project` → `.claude/skills/<name>` relative to the repo root
  - All other values or unset → `~/.claude/skills/<name>`

Check if already installed:

```bash
ls <install_path> 2>/dev/null && echo "installed" || echo "missing"
```

If already present and `force` not passed → record `already installed`.

If missing, or if `force` was passed → install via sparse git checkout (remove existing directory first if force):

```bash
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
git clone --depth 1 --filter=blob:none --sparse --branch <version> \
    https://github.com/<source> "$tmpdir"
# if path is set:
git -C "$tmpdir" sparse-checkout set <path>
mkdir -p <install_path>
cp -r "$tmpdir/<path>/." <install_path>/
```

If no `path` field, use the repo root (omit the `sparse-checkout set` step and copy from `$tmpdir` directly).

Record `installed` or `FAILED`.

### Step 6 — Handle .env

Check if `.env` exists in the current directory:

```bash
ls .env 2>/dev/null && echo "exists" || echo "missing"
```

If **missing** → use the Write tool to create `.env` in the current directory
with the content of `../../reference/env.example` from the repo.
Record `.env: created from env.example`.

If **present** → record `.env: found — skipping`.

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
  DEVLAKE_MCP_SECRET_KEY      devlake-local-mysql-mcp
  KONFLUX_MYSQL_HOST          devlake-prod-mysql-mcp
  KONFLUX_MYSQL_USER          devlake-prod-mysql-mcp
  KONFLUX_MYSQL_PASS          devlake-prod-mysql-mcp
  KONFLUX_MCP_SECRET_KEY      devlake-prod-mysql-mcp

  Edit .env and run /ai-stack:up when ready.
```

Only show the variables that actually appeared in the `grep` output — do not
show variables that are already set to real values.

Proceed to Step 7 regardless.

### Step 7 — MCP servers

Check currently registered MCPs:

```bash
claude mcp list
```

Read `../../reference/mcps.yaml`. Only process entries where `scope: user` or `scope` is unset
(default: `user`). Entries with `scope: project` are skipped — they are handled per-project by
`/ai-stack:project-init`.

Source `.env` from the current directory before expanding any `$VAR` references:

```bash
set -a; [ -f .env ] && . ./.env; set +a
```

For each applicable MCP:

- If already registered (match by name) and `force` not passed → record `already registered`.
- If already registered and `force` was passed → remove first, then re-register:
  ```bash
  claude mcp remove <name>
  ```
- If any field value contains `$VAR` references, expand from the shell environment (after
  sourcing `.env`). If a required env var is still unset, record `skipped (<VAR> not set)`
  and skip — do not register with an empty value.
- Otherwise register:
  ```bash
  claude mcp add --transport <transport> --scope <scope> \
    [--header "KEY: VALUE" ...] <name> <url>
  ```
  Record `registered` or `FAILED`.

### Step 8 — Summary

Print a compact status table covering every item processed:

```
=== BOOTSTRAP SUMMARY ===

Prerequisites:
go                          ok
node                        ok

Runtimes:
mise                        already installed (python@3.12 node@20 go@1.24 set globally)
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
n8n-skills                  skipped (optional)

Environment:
.env                        created from env.example

MCPs:
gmail                       already registered
gdrive                      registered
devlake-mysql-local         skipped (scope: project)
devlake-mysql-staging       skipped (scope: project)
devlake-mysql-prod          skipped (scope: project)

=========================

Run /ai-stack:project-init in your project to install optional skills and register project-scoped MCPs.
```

If any item shows `FAILED`, print its error output beneath the table.
