# Claude Configuration Modernization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modernize `AGENTS.md`, `CLAUDE.md`, and `.claude/settings.local.json` in the ai-stack repo to 2026 patterns — skills-first, concise, no generic advice, consolidated permissions.

**Architecture:** Three independent file rewrites. `AGENTS.md` is trimmed to project-specific invariants only. `CLAUDE.md` becomes a thin Claude-specific wrapper delegating to `AGENTS.md` with a skills table. `settings.local.json` collapses 100+ granular permission entries into ~23 broad wildcard patterns.

**Tech Stack:** Markdown, JSON, `jq` for JSON validation.

**Spec:** `docs/superpowers/specs/2026-04-29-claude-config-modernization-design.md`

---

## File Map

| Action | File | What changes |
|---|---|---|
| Modify | `AGENTS.md` | Remove §5, §6, §7; trim §2; rename ADRs → Principles; slim §9 |
| Modify | `CLAUDE.md` | Full rewrite — thin wrapper + skills table |
| Modify | `.claude/settings.local.json` | Replace `permissions.allow` array; preserve everything else |

---

### Task 1: Trim AGENTS.md

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: Read current file**

```bash
wc -l AGENTS.md
```
Expected: 141 lines

- [ ] **Step 2: Write trimmed content**

Replace the entire file with:

```markdown
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

Infrastructure projects may add `pulumi/`, `kubernetes/` etc. as needed.

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

Everything else — feature design, implementation — flows through the superpowers
workflow (`docs/superpowers/specs/` + `docs/superpowers/plans/`).

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

---

## 6. Tool Usage

- Use `Grep`/`Glob` for searching rather than `Bash` grep/find when possible.
```

- [ ] **Step 3: Verify line count dropped**

```bash
wc -l AGENTS.md
```
Expected: ~75 lines (was 141)

- [ ] **Step 4: Commit**

```bash
git add AGENTS.md
git commit -m "docs(agents): trim to project-specific invariants, rename ADRs to principles

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 2: Rewrite CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Write new content**

Replace the entire file with:

```markdown
# Claude Code Rules

Project conventions are in [AGENTS.md](./AGENTS.md).

---

## Output Format

- Keep responses concise and actionable.
- Use code blocks with appropriate language tags.
- Prefer editing existing files over creating new ones.

---

## Tool Usage

- Read files before editing.
- Batch independent tool calls in one message.
- Use Grep/Glob for search, not Bash find/grep.

---

## Skills & Multi-Agent Coordination

Invoke the relevant skill before starting a task.

| Skill | When to use |
|---|---|
| `/superpowers:brainstorming` | Before implementing any feature |
| `/superpowers:writing-plans` | Before multi-step tasks |
| `/superpowers:executing-plans` | When running a written plan |
| `/superpowers:systematic-debugging` | When encountering a bug |
| `/superpowers:requesting-code-review` | Before merging |
| `/ai-stack:add-service` | Scaffold a new MCP service |
| `/ai-stack:add-workflow` | Add CI workflow to an existing service |
| `/ai-stack:install-plugins` | Install or update plugins |
| `/ai-stack:install-skills` | Install or update skills |
| `/ai-stack:install-mcps` | Register MCP servers |
| `/ai-stack:sandbox` | Install or update the LINCE toolkit |
| `/dev:review-cr` | Run CodeRabbit review on committed changes |

---

## Execution Pattern

For any non-trivial task:
1. Invoke the relevant skill first.
2. In one message: spawn agents, batch file ops, batch shell commands, batch todos.
3. New files go in subfolders — never in repo root.
```

- [ ] **Step 2: Verify line count**

```bash
wc -l CLAUDE.md
```
Expected: ~50 lines (was 141)

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(claude): rewrite as skills-first wrapper delegating to AGENTS.md

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 3: Consolidate settings.local.json

**Files:**
- Modify: `.claude/settings.local.json`

> Note: `settings.local.json` is gitignored — this change is local only.

- [ ] **Step 1: Resolve home directory**

```bash
echo $HOME
```
Note the output — you will substitute it for `$HOME` in the path below.

- [ ] **Step 2: Verify the hooks block (if any) before overwriting**

```bash
jq 'keys' .claude/settings.local.json
```
Expected output: `["permissions"]` — no hooks block to preserve in this file.
If you see other top-level keys, note them and carry them forward into the new file.

- [ ] **Step 3: Write consolidated content**

Replace the file with the following, substituting your actual home directory path
for `$HOME` in the three `Read` entries (e.g. `/Users/yourname` on macOS):

```json
{
  "permissions": {
    "allow": [
      "Bash(git *)",
      "Bash(gh *)",
      "Bash(podman *)",
      "Bash(docker *)",
      "Bash(claude *)",
      "Skill(update-config)",
      "Bash(nono *)",
      "Bash(openshell *)",
      "Bash(agent-sandbox *)",
      "Bash(zellij *)",
      "Bash(python3 *)",
      "Bash(uv *)",
      "Bash(fnm *)",
      "Bash(gcloud *)",
      "Bash(starship *)",
      "Bash(cr review *)",
      "WebSearch",
      "WebFetch(domain:github.com)",
      "Read(//$HOME/**)",
      "Read(//var/run/**)",
      "Read(//opt/homebrew/**)",
      "mcp__plugin_context7_context7__resolve-library-id",
      "mcp__plugin_context7_context7__query-docs"
    ]
  }
}
```

- [ ] **Step 4: Validate JSON**

```bash
jq . .claude/settings.local.json
```
Expected: pretty-printed JSON with no errors. If `jq` exits non-zero, fix the syntax.

- [ ] **Step 5: Verify entry count dropped**

```bash
jq '.permissions.allow | length' .claude/settings.local.json
```
Expected: 23

- [ ] **Step 6: Confirm file is gitignored (no commit needed)**

```bash
git status .claude/settings.local.json
```
Expected: file does not appear (it is gitignored). Done — no commit for this file.
