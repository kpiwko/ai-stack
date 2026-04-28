# Design: `/ai-stack:bootstrap` Skill

**Date:** 2026-04-28
**Status:** Draft

---

## Context

The ai-stack repo includes agent definitions for Go, Python, TypeScript, and Rust development.
Developers and agents need LSP servers installed to get code intelligence. Today there is no
automated way to bootstrap these tools — this skill fills that gap.

---

## Goal

A single `/ai-stack:bootstrap` command that installs all LSP servers and their required
runtimes/package managers across Go, Python, TypeScript, and Rust.

---

## Reference File

`plugins/ai-stack/reference/bootstrap.yaml` is the source of truth for what gets installed,
organized by language. It documents prerequisites (must already exist), managed tools (installed
by the skill if missing), and LSP servers.

```yaml
languages:
  go:
    runtime:
      name: go
      check: go version
      required: true
      reason: "Install from https://go.dev/dl/"
    lsp:
      name: gopls
      install: "go install golang.org/x/tools/gopls@latest"

  python:
    runtime:
      name: uv
      check: uv --version
      install: "curl -LsSf https://astral.sh/uv/install.sh | sh"
    lsp:
      name: pyright
      install: "uv tool install pyright"

  typescript:
    runtime:
      name: node
      check: node --version
      required: true
      reason: "Install from https://nodejs.org/ or via brew"
    package_manager:
      name: pnpm
      check: pnpm --version
      install: "npm install -g pnpm"
    lsp:
      name: typescript-language-server
      install: "pnpm add -g typescript typescript-language-server"

  rust:
    runtime:
      name: rustup
      check: rustup --version
      install: "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y"
    lsp:
      name: rust-analyzer
      install: "rustup component add rust-analyzer"
```

---

## Skill Location

`plugins/ai-stack/skills/bootstrap/skill.md`

---

## Skill Behavior

### Step 1 — Prerequisites check

Check that `go` and `node` are on PATH:

```bash
command -v go
command -v node
```

If either is missing, fail immediately with the reason and install URL from `bootstrap.yaml`.
Do not proceed.

### Step 2 — Runtime/package manager installs

For each managed tool (`uv`, `pnpm`, `rustup`): check if present, install if not.
Report `already installed` or `installed` for each.

### Step 3 — LSP server installs

Install all four LSP servers in order:
1. `gopls` — via `go install golang.org/x/tools/gopls@latest`
2. `pyright` — via `uv tool install pyright`
3. `typescript-language-server` — via `pnpm add -g typescript typescript-language-server`
4. `rust-analyzer` — via `rustup component add rust-analyzer`

Each step reports success or failure individually. A failure in one does not stop the rest.

### Step 4 — Summary

Print a compact status table:

```
go           ok  (prerequisite)
node         ok  (prerequisite)
uv           installed
pnpm         already installed
rustup       installed
gopls        ok
pyright      ok
typescript-language-server  ok
rust-analyzer  ok
```

---

## Design Decisions

- **No arguments** — bootstrap is all-or-nothing; selective installs can be added later if needed.
- **No sandbox guard** — the skill works inside and outside agent-sandbox. Installs succeed in
  both contexts (ephemeral inside sandbox, persistent outside).
- **Fail fast on prerequisites** — Go and Node are assumed present; the skill cannot and does not
  install them. All other tools are managed by the skill.
- **Reference file as documentation** — `bootstrap.yaml` gives a human-readable overview of
  every tool, install command, and prerequisite without reading the skill prose.
