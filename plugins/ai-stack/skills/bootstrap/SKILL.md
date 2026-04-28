---
description: Install LSP servers and their runtimes for Go, Python, TypeScript, and Rust.
---

# /ai-stack:bootstrap

## Synopsis

```
/ai-stack:bootstrap   ← check prerequisites, install managed tools and LSP servers
```

No arguments. Bootstrap is all-or-nothing — installs everything defined in
`plugins/ai-stack/reference/bootstrap.yaml`.

---

## Reference

`plugins/ai-stack/reference/bootstrap.yaml` is the source of truth for what gets
checked and installed. Read it to get exact tool names, check commands, and install
commands before running any step.

---

## Process

### Step 1 — Prerequisites check

Run:

```bash
command -v go   && go version   || echo "go: MISSING"
command -v node && node --version || echo "node: MISSING"
```

If either `go` or `node` is missing, stop immediately and display:

```
✗ <tool>: not found
  This skill cannot install <tool>.
  Install it from: <reason from bootstrap.yaml>
```

Do not proceed to Step 2.

### Step 2 — Runtime / package manager installs

For each managed tool (`uv`, `pnpm`, `rustup`) in order:

1. Run its `check` command.
2. If already present → record `already installed`.
3. If missing → run its `install` command from `bootstrap.yaml`, then record `installed`.

Run checks and installs sequentially. A failure in one does not stop the others — record
`failed` and continue.

### Step 3 — LSP server installs

Install all four LSP servers in order, using commands from `bootstrap.yaml`:

1. `gopls` — `go install golang.org/x/tools/gopls@latest`
2. `pyright` — `uv tool install pyright`
3. `typescript-language-server` — `pnpm add -g typescript typescript-language-server`
4. `rust-analyzer` — `rustup component add rust-analyzer`

A failure in one does not stop the rest. Record outcome for each.

### Step 4 — Summary

Print a compact status table covering every item checked or installed:

```
go                          ok   (prerequisite)
node                        ok   (prerequisite)
uv                          installed
pnpm                        already installed
rustup                      installed
gopls                       ok
pyright                     ok
typescript-language-server  ok
rust-analyzer               ok
```

If any item failed, list it with `FAILED` and show the error output beneath the table.
