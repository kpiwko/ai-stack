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

5. **Keep instructions lean** — enough structure to be consistent, no walls of text.

---

## 2. Repository Structure

### 2.1 Root — allowed files only

`AGENTS.md`, `CLAUDE.md`, `TODO.md`, `README.md`, `LICENSE`, `.gitignore`,
`.editorconfig`, tooling configs, dependency manifests. Nothing else.

### 2.2 Common subfolders

| Directory | Purpose |
|---|---|
| `src/` | Production source code |
| `tests/` | All tests (unit, integration) |
| `docs/` | Internal documentation |
| `docs/adr/` | Architecture Decision Records |
| `docs/research/` | Research notes, reusable frameworks |
| `config/` | Configuration files (YAML, JSON, env templates) |
| `scripts/` or `tools/` | Automation and utility scripts |
| `examples/` | Example usage or demo projects |

Infrastructure projects may add `pulumi/`, `kubernetes/` etc. as needed.

---

## 3. Documentation & ADRs

- All internal docs go under `docs/` — never create new root-level `.md` files
  except `README.md` and `TODO.md`.
- **ADRs**: `docs/adr/NNNN-title-with-hyphens.md` — Status, Context, Decision,
  Consequences. Maintain `docs/adr/README.md` as index.
- Use an ADR when architecture, core tooling, or security/cost decisions have
  long-term impact.

---

## 4. Naming Conventions

- Names should be descriptive, not cute; stable over time (no date prefixes).
- Docs: `docs/overview.md`, `docs/architecture.md`, `docs/howto-<topic>.md`,
  `docs/research/<topic>.md`.
- See language agent definitions in `plugins/dev/agents/` for file naming per language.

---

## 5. AI & Human Collaboration

**When AI changes code:**
- Read relevant files before editing.
- Keep imports at top; respect existing patterns.
- For new features: consider security first, update docs, add tests.
- For bug fixes: understand root cause first, add regression test.

**When AI creates docs:**
- Put them under `docs/` — not root.

**When humans work:**
- Keep `TODO.md` current; use ADRs for major decisions; prefer small focused commits.

---

## 6. Pre-Action Checklists

**Before creating a new file:**
- [ ] Does an existing file already cover this responsibility?
- [ ] Is it in the right folder?
- [ ] Is the name clear and consistent?

**Before committing:**
- [ ] No working files in root.
- [ ] `TODO.md` up to date.
- [ ] Tests updated where appropriate.

---

## 7. Security

- Never commit secrets or credentials.
- Validate user input at system boundaries only — trust internal code.
- Follow principle of least privilege.
- Log errors with context but never log sensitive data.

---

## 8. Commit Style

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

---

## 9. Tool Usage (Claude Code)

- Use the `Read` tool before editing any file.
- Batch independent tool calls in a single message — never sequentially when
  parallel is possible.
- Make atomic, focused changes; avoid scope creep.
- Use `Grep`/`Glob` for searching rather than `Bash` grep/find when possible.
