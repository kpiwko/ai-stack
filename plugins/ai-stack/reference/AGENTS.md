# Agent Rules

Base rules for AI assistants working in any repository. Language-specific conventions
and tool workflows live in plugins — see `plugins/` in this repo.

---

## 1. Golden Rules

1. **One message = all related operations** — batch reads, writes, shell commands, and
   agent spawns together. Never make a tool call, wait for a response, then make another
   that could have been sent at the same time.

2. **No working files in repo root** — root holds only: `AGENTS.md`, `CLAUDE.md`,
   `TODO.md`, `README.md`, `LICENSE`, `.gitignore`, dependency files, tooling configs.
   All code, docs, tests, and scripts go into subfolders.

3. **Planning lives in `TODO.md`** — keep it short and actionable; remove steps once done.

4. **Prefer editing over creating** — edit existing files rather than creating new ones.
   Only create a new file when a clear responsibility or context is missing.

5. **Prefer search tools over shell** — Use `Grep`/`Glob` for searching rather than
   `Bash` grep/find when possible.

---

## 2. Repository Structure

| Directory | Purpose |
|---|---|
| `src/` | Production source code |
| `tests/` | All tests (unit, integration) |
| `docs/` | Internal documentation |
| `docs/principles/` | Cross-cutting decisions that constrain all future work |
| `docs/superpowers/` | Work artifacts: specs and implementation plans |
| `docs/research/` | Research notes, reusable frameworks |
| `config/` | Configuration files (YAML, JSON, env templates) |
| `scripts/` or `tools/` | Automation and utility scripts |
| `examples/` | Example usage or demo projects |

Infrastructure projects may add `pulumi/`, `kubernetes/` etc. as needed. Directories are conventional — create them as the project grows.

---

## 3. Principles

`docs/principles/NNNN-title-with-hyphens.md` — for decisions that constrain all future
work in this repo: tooling choices, build conventions, required script patterns.
Maintain `docs/principles/README.md` as index.

Template:

```
# Title
Status: accepted | deprecated
Constraint: one-line statement of what this mandates or forbids
Why: the reason — a past incident, a cost decision, a technical constraint
Applies to: what it constrains (all services / all skills / all MCP builds / etc.)
```

For feature design and implementation, create a spec under `docs/superpowers/specs/`
and an implementation plan under `docs/superpowers/plans/` before writing code.

---

## 4. Naming Conventions

- Names should be descriptive, not cute; stable over time (no date prefixes).
- Docs: `docs/overview.md`, `docs/architecture.md`, `docs/howto-<topic>.md`,
  `docs/research/<topic>.md`.
- See language agent definitions in `plugins/dev/agents/` for file naming per language.

---

## 5. Commit Style

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

When AI assists with a commit, include a Co-Authored-By trailer:

```
feat: add user authentication

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

