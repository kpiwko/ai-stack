---
description: Full machine setup — installs runtimes, LSP plugins, Claude plugins, skills, and registers MCP servers.
---

# /ai-stack:bootstrap

## Synopsis

```
/ai-stack:bootstrap   ← check prerequisites, then install everything
```

No arguments. Bootstrap runs all steps regardless of individual step failures — only
the prerequisites check (Step 1) is fail-fast.

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

A failure in one does not stop the others — record `FAILED` and continue.

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
  Record `installed` or `FAILED`.

A failure in one does not stop the rest.

### Step 4 — Claude plugins

Read `plugins/ai-stack/reference/plugins.yaml`. Compare against `claude plugin list` output.

Skip any plugin already processed in Step 3 — they will already be installed, and omitting
them from this section avoids duplicate rows in the summary.

For each remaining plugin not already installed:

```bash
claude plugin install <name>@<source> --scope user
```

Record `already installed` / `installed` / `FAILED` for each.

### Step 5 — External skills

Read `plugins/ai-stack/reference/skills.yaml`.

For each skill:

- If `optional: true` → record `skipped (optional)` and continue.
- Determine install path:
  - `scope: project` → `.claude/skills/<name>` relative to the repo root
  - All other values or unset → `~/.claude/skills/<name>`

Check if already installed:

```bash
ls <install_path> 2>/dev/null && echo "installed" || echo "missing"
```

If already present → record `already installed`.

If missing, install via sparse git checkout:

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

### Step 6 — MCP servers

Check currently registered MCPs:

```bash
claude mcp list
```

Read `plugins/ai-stack/reference/mcps.yaml`. For each MCP:

- If already registered (match by name) → record `already registered`.
- If `scope` is not set, default to `user`.
- If any field value contains `$VAR` references, expand from the current shell environment.
  If a required env var is unset, record `skipped (<VAR> not set)` and skip — do not register with an empty value.
- Otherwise register:
  ```bash
  claude mcp add --transport <transport> --scope <scope> \
    [--header "KEY: VALUE" ...] <name> <url>
  ```
  Record `registered` or `FAILED`.

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
template-slide-deck         skipped (optional)
n8n-skills                  skipped (optional)

MCPs:
gmail                       already registered
gdrive                      registered
devlake-prod-mysql-mcp      skipped (KONFLUX_MCP_SECRET_KEY not set)
devlake-local-mysql-mcp     skipped (DEVLAKE_MCP_SECRET_KEY not set)

=========================
```

If any item shows `FAILED`, print its error output beneath the table.

### Step 8 — Optional skills offer

If no skills were skipped as optional, skip this step entirely.

Otherwise print:

```
Optional skills are available but not installed by default:
  <name>   <source>[@<version>]
  ...

Install any? Enter name(s) separated by spaces, or press Enter to skip:
```

Wait for input. If the user enters one or more names:

- Validate each name against the optional skills list; ignore unrecognised names with a warning.
- For each valid name, run the full Step 5 install logic (determine scope, check if already
  installed, sparse-checkout and copy).
- Print a short confirmation for each:
  ```
  template-slide-deck   installed
  ```

If the user presses Enter with no input, print `No optional skills installed.` and finish.
