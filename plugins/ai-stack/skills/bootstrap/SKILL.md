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
  where `<name>@<source>` is the full value from the list (e.g. `gopls-lsp@claude-plugins-official`).
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

If no `path` field, use the repo root (omit the `sparse-checkout set` step and copy from `$tmpdir` directly).

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
