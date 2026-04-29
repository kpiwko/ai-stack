# Claude Configuration Modernization Design

**Date:** 2026-04-29
**Status:** approved

---

## Context

The ai-stack repository uses `CLAUDE.md` and `AGENTS.md` as identical files — a
carry-over from when they were set up as a symlink pair. `settings.local.json` has
accumulated 100+ permission entries over many sessions, most of them dead one-offs
or repeated subcommands of the same tool.

The goal is to bring both files in line with 2026 patterns, using
`developer-practices-documentation` as a reference point.

> Note: `settings.local.json` is gitignored and user-specific. The spec uses `$HOME`
> as a placeholder; the implementation resolves it to the actual home directory path.

---

## Decisions

### 1. CLAUDE.md / AGENTS.md split

`AGENTS.md` becomes the canonical shared conventions file (usable by any AI agent).
`CLAUDE.md` becomes a thin Claude-specific wrapper that delegates to `AGENTS.md` and
adds a skills table + execution pattern.

### 2. AGENTS.md — trim to project-specific invariants only

Remove all generic AI advice that belongs in Claude's default system prompt:
- "read relevant files before editing"
- "validate user input at system boundaries"
- security/OWASP guidance
- pre-action checklists

Keep only what is non-obvious and specific to this repo.

### 3. ADRs → Principles

The `docs/adr/` convention is renamed to `docs/principles/`. The purpose narrows:
principles only for cross-cutting decisions that constrain all future work (tooling
choices, build conventions, install script pattern). Everything else flows through the
superpowers workflow (specs + plans).

Principles template:
```
# Title
Status: accepted | deprecated
Constraint: one-line statement of what this mandates or forbids
Why: the reason — a past incident, a cost decision, a technical constraint
Applies to: what it constrains
```

### 4. settings.local.json — consolidate to broad patterns

Replace 100+ granular entries with ~25 broad wildcard patterns grouped by tool
category. Dead one-offs (specific `sed` line numbers, hardcoded paths into nested
repos, single-use shell incantations) are dropped entirely.

---

## AGENTS.md — target structure (~60 lines)

Sections to keep (trimmed):
- **Golden Rules** — batch operations, no root files, prefer editing over creating
- **Repository Structure** — folder layout table only (drop the prose); update `docs/adr/` row to `docs/principles/`
- **Principles** — renamed from ADRs, narrowed scope
- **Naming Conventions** — stable reference, kept as-is
- **Commit Style** — conventional commits + Co-Authored-By trailer
- **Tool Usage** — Grep/Glob preference only (remove the rest)

Sections to remove entirely:
- §5 AI & Human Collaboration
- §7 Security
- §6 Pre-Action Checklists

---

## CLAUDE.md — target structure (~50 lines)

```markdown
# Claude Code Rules

Project conventions are in AGENTS.md.

## Output Format
- Keep responses concise and actionable.
- Use code blocks with language tags.
- Prefer editing existing files over creating new ones.

## Tool Usage
- Read files before editing.
- Batch independent tool calls in one message.
- Use Grep/Glob for search, not Bash find/grep.

## Skills & Multi-Agent Coordination

Invoke the relevant skill before starting a task.

| Skill | When to use |
|---|---|
| /superpowers:brainstorming     | Before implementing any feature |
| /superpowers:writing-plans     | Before multi-step tasks |
| /superpowers:executing-plans   | When running a written plan |
| /superpowers:systematic-debugging | When encountering a bug |
| /superpowers:requesting-code-review | Before merging |
| /ai-stack:add-service          | Scaffold a new MCP service |
| /ai-stack:add-workflow         | Add CI workflow to an existing service |
| /ai-stack:install-plugins      | Install or update plugins |
| /ai-stack:install-skills       | Install or update skills |
| /ai-stack:install-mcps         | Register MCP servers |
| /ai-stack:sandbox              | Install or update the LINCE toolkit |
| /dev:review-cr                 | Run CodeRabbit review on committed changes |

## Execution Pattern

For any non-trivial task:
1. Invoke the relevant skill first.
2. In one message: spawn agents, batch file ops, batch shell commands, batch todos.
3. New files go in subfolders — never in repo root.
```

---

## settings.local.json — target allow list (~25 entries)

| Category | Patterns |
|---|---|
| git, GitHub CI | `Bash(git *)`, `Bash(gh *)` |
| Containers | `Bash(podman *)`, `Bash(docker *)` |
| Claude tooling | `Bash(claude *)`, `Skill(update-config)` |
| ai-stack tooling | `Bash(nono *)`, `Bash(openshell *)`, `Bash(agent-sandbox *)`, `Bash(zellij *)` |
| Languages/runtimes | `Bash(python3 *)`, `Bash(uv *)`, `Bash(fnm *)` |
| Cloud/infra | `Bash(gcloud *)`, `Bash(starship *)`, `Bash(cr review *)` |
| Web | `WebSearch`, `WebFetch(domain:github.com)` |
| Read | `Read(//$HOME/**)`, `Read(//var/run/**)`, `Read(//opt/homebrew/**)` |
| MCP | `mcp__plugin_context7_context7__resolve-library-id`, `mcp__plugin_context7_context7__query-docs` |

Dropped: all dead one-offs — specific `sed` line ranges, hardcoded `git -C` paths
into nested repos, single-use shell incantations, the Vertex AI test command, and
specific `xargs`/`grep`/`ln` patterns.

The hooks block in `settings.local.json` is preserved unchanged.

---

## Out of scope

- `lince/CLAUDE.md` — separate nested git repo, explicitly excluded
- `settings.local.json` hooks block — functional, no changes needed
- Any changes to plugin or skill files
