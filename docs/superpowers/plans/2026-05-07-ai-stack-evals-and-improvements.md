# ai-stack Plugin: Evals + Improvements

> **STATUS: COMPLETED (2026-05-13)**
>
> **What shipped vs. original design:**
> - `tools/run-skill.sh` (bash) was replaced by `tools/run-skill.py` (Python) — same interface, better error handling and retry logic
> - Skill invocation changed from `claude -p "/ai-stack:<skill>"` to passing SKILL.md content directly as the `-p` prompt (bypasses global plugin installation requirement; lets evals run from local repo without pushing)
> - The `build_skill_prompt()` function prepends `Base directory for this skill:` and `Invoked as:` headers so the skill gets the same context it would from a real invocation
> - `tools/run-skill.sh` was never committed; `tools/run-skill.py` is the shipped implementation
> - All eval configs reference `python3 tools/run-skill.py` instead of `bash tools/run-skill.sh`

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a promptfoo-based eval framework for ai-stack skills so skill changes can be verified before shipping, plus a `/ai-stack:status` skill and a hooks reference doc.

**Architecture:** Evals use [promptfoo](https://promptfoo.dev) as the test runner. Each skill gets a `promptfooconfig-<skill>.yaml` with YAML-declared scenarios and JavaScript graders that check observable outcomes (filesystem state + Claude output text). A thin bash script `tools/run-skill.sh` handles temp-dir setup, invokes `claude -p`, collects filesystem state, and emits JSON to stdout for promptfoo's `exec` provider. `just eval` wires it all together.

**Tech Stack:** promptfoo (`npx promptfoo`), `claude -p` (headless invocation), `jq`, bash, justfile.

**Key design principle:** Grade **outcomes** (files created, output text, MCP registrations), not tool-call sequences. Pass@k via promptfoo's `--repeat N`.

---

## File Structure

| Action | Path | Purpose |
|---|---|---|
| Create | `plugins/ai-stack/evals/framework.md` | Eval conventions, run commands, TDD cycle |
| Create | `tools/run-skill.sh` | Setup → `claude -p` → state collection → JSON output |
| Create | `plugins/ai-stack/evals/promptfooconfig-up.yaml` | 4 scenarios for `/ai-stack:up` |
| Create | `plugins/ai-stack/evals/promptfooconfig-down.yaml` | 3 scenarios for `/ai-stack:down` |
| Create | `plugins/ai-stack/evals/promptfooconfig-bootstrap.yaml` | 4 scenarios for `/ai-stack:bootstrap` |
| Create | `plugins/ai-stack/evals/promptfooconfig-project-init.yaml` | 4 scenarios for `/ai-stack:project-init` |
| Modify | `justfile` | Add `just eval [skill] [pattern]` recipe |
| Create | `plugins/ai-stack/skills/status/SKILL.md` | New `/ai-stack:status` skill |
| Modify | `plugins/ai-stack/.claude-plugin/plugin.json` | Bump version to 0.11.0 |
| Modify | `plugins/ai-stack/README.md` | Add status skill, evals section |
| Modify | `plugins/ai-stack/reference/CLAUDE.md` | Add `/ai-stack:status` to skills table |
| Create | `plugins/ai-stack/reference/hooks.md` | Document Claude hooks wiring |

---

### Task 1: Eval Framework Doc (`evals/framework.md`)

**Files:**
- Create: `plugins/ai-stack/evals/framework.md`

- [ ] **Step 1: Write `framework.md`**

```markdown
# ai-stack Eval Framework

Evals use [promptfoo](https://promptfoo.dev) as the test runner.

## How it works

Each skill has a `promptfooconfig-<skill>.yaml` that declares test scenarios.
A shared runner script (`tools/run-skill.sh`) handles:

1. Create a temp directory (`$EVAL_DIR`)
2. Run scenario-specific setup (seed files)
3. Invoke `claude -p "/ai-stack:<skill>"` from `$EVAL_DIR`
4. Collect filesystem state
5. Emit a JSON object to stdout: `{"output": "<claude text>", "state": {...}}`

Promptfoo's `exec` provider captures this JSON. JavaScript graders parse it
and check observable outcomes — not which tools Claude called.

## Running evals

```bash
# All scenarios for one skill
just eval up

# Filter by description substring
just eval up "Fresh directory"

# Pass@k (repeat each test 3 times, pass if any succeeds)
just eval up "" 3

# All skills
just eval
```

## TDD cycle for skill changes

1. **RED** — add a scenario to the YAML config, run `just eval <skill>`, confirm FAIL
2. **GREEN** — edit the SKILL.md to satisfy the scenario, run again, confirm PASS
3. **REFACTOR** — clean up the skill text, run all scenarios, confirm no regressions

## Grader conventions

All graders receive the JSON string in `output`. Parse it first:

```javascript
const r = JSON.parse(output);
// r.output   — full text from Claude
// r.state    — filesystem/env state collected after the skill ran
```

Return `{ pass: true }` or `{ pass: false, reason: "..." }`.

## State fields collected by `tools/run-skill.sh`

| Field | Type | Description |
|---|---|---|
| `compose_exists` | bool | `compose.yaml` present in EVAL_DIR |
| `env_exists` | bool | `.env` present in EVAL_DIR |
| `compose_content` | string | Content of `compose.yaml` (empty if absent) |
| `claude_md_exists` | bool | `CLAUDE.md` present in EVAL_DIR |
| `claude_md_content` | string | Content of `CLAUDE.md` |
| `agents_md_exists` | bool | `AGENTS.md` present in EVAL_DIR |
| `skill_dir_exists` | bool | `.claude/skills/` present in EVAL_DIR |
```

- [ ] **Step 2: Commit**

```bash
git add plugins/ai-stack/evals/framework.md
git commit -m "docs(evals): add promptfoo eval framework conventions"
```

---

### Task 2: Runner Script (`tools/run-skill.sh`)

**Files:**
- Create: `tools/run-skill.sh`

Prerequisite: `jq` must be available (`brew install jq` on macOS; already present on most Linux).

- [ ] **Step 1: Write `tools/run-skill.sh`**

```bash
#!/usr/bin/env bash
# tools/run-skill.sh <skill> <scenario>
# Outputs JSON to stdout for promptfoo exec provider:
#   {"output": "<claude text>", "state": {<filesystem state>}}
set -euo pipefail

SKILL="${1:?skill required (up|down|bootstrap|project-init)}"
SCENARIO="${2:-default}"
EVAL_DIR=$(mktemp -d)
trap 'rm -rf "$EVAL_DIR"' EXIT

# ── Scenario setup ────────────────────────────────────────────────────────────
case "${SKILL}/${SCENARIO}" in
  # /ai-stack:up
  up/fresh)             cp .env "$EVAL_DIR/.env" ;;
  up/no-env)            true ;;
  up/existing-compose)  printf 'original' > "$EVAL_DIR/compose.yaml"; cp .env "$EVAL_DIR/.env" ;;
  up/placeholder-env)   cp plugins/ai-stack/reference/env.example "$EVAL_DIR/.env" ;;
  # /ai-stack:down
  down/has-compose)     cp compose.yaml "$EVAL_DIR/compose.yaml"; cp .env "$EVAL_DIR/.env" ;;
  down/no-compose)      true ;;
  down/already-stopped) cp compose.yaml "$EVAL_DIR/compose.yaml"; cp .env "$EVAL_DIR/.env" ;;
  # /ai-stack:bootstrap  (runs in repo root, not EVAL_DIR)
  bootstrap/*)          true ;;
  # /ai-stack:project-init
  project-init/empty)         true ;;
  project-init/existing-md)   printf 'existing content' > "$EVAL_DIR/CLAUDE.md" ;;
  project-init/force)         printf 'old content' > "$EVAL_DIR/CLAUDE.md" ;;
  project-init/optional-skill) true ;;
  *)
    echo "Unknown scenario: ${SKILL}/${SCENARIO}" >&2
    exit 1 ;;
esac

# ── Determine invocation ──────────────────────────────────────────────────────
ARGS=""
[[ "$SCENARIO" == "force" ]] && ARGS=" force"

# bootstrap runs in repo root (it registers MCPs etc.)
WORK_DIR="$EVAL_DIR"
[[ "$SKILL" == "bootstrap" ]] && WORK_DIR="$(pwd)"

# ── Invoke claude ─────────────────────────────────────────────────────────────
CLAUDE_OUT=$(cd "$WORK_DIR" && claude -p "/ai-stack:${SKILL}${ARGS}" --no-update-check 2>&1) || true

# ── Collect state ─────────────────────────────────────────────────────────────
compose_exists=$([ -f "$EVAL_DIR/compose.yaml" ]        && echo true || echo false)
env_exists=$([ -f "$EVAL_DIR/.env" ]                    && echo true || echo false)
claude_md_exists=$([ -f "$EVAL_DIR/CLAUDE.md" ]         && echo true || echo false)
agents_md_exists=$([ -f "$EVAL_DIR/AGENTS.md" ]         && echo true || echo false)
skill_dir_exists=$([ -d "$EVAL_DIR/.claude/skills" ]    && echo true || echo false)
compose_content=$(cat "$EVAL_DIR/compose.yaml"   2>/dev/null || true)
claude_md_content=$(cat "$EVAL_DIR/CLAUDE.md"    2>/dev/null || true)

# ── Emit JSON ─────────────────────────────────────────────────────────────────
jq -n \
  --arg     out               "$CLAUDE_OUT" \
  --argjson compose_exists    "$compose_exists" \
  --argjson env_exists        "$env_exists" \
  --argjson claude_md_exists  "$claude_md_exists" \
  --argjson agents_md_exists  "$agents_md_exists" \
  --argjson skill_dir_exists  "$skill_dir_exists" \
  --arg     compose_content   "$compose_content" \
  --arg     claude_md_content "$claude_md_content" \
  '{output: $out, state: {
      compose_exists:   $compose_exists,
      env_exists:       $env_exists,
      claude_md_exists: $claude_md_exists,
      agents_md_exists: $agents_md_exists,
      skill_dir_exists: $skill_dir_exists,
      compose_content:  $compose_content,
      claude_md_content: $claude_md_content
  }}'
```

- [ ] **Step 2: Make executable and syntax-check**

```bash
chmod +x tools/run-skill.sh
bash -n tools/run-skill.sh
echo "syntax ok"
```

Expected: `syntax ok`

- [ ] **Step 3: Smoke test (dry run — no claude invocation)**

```bash
# Temporarily stub claude to avoid real invocation
PATH_REAL="$PATH"
mkdir -p /tmp/stub-bin
echo '#!/bin/bash; echo "stub output"' > /tmp/stub-bin/claude
chmod +x /tmp/stub-bin/claude
PATH="/tmp/stub-bin:$PATH" bash tools/run-skill.sh up fresh | jq .
PATH="$PATH_REAL"
rm -rf /tmp/stub-bin
```

Expected: valid JSON with `output`, `state.compose_exists`, `state.env_exists` fields.

- [ ] **Step 4: Commit**

```bash
git add tools/run-skill.sh
git commit -m "feat(evals): add run-skill.sh runner for promptfoo exec provider"
```

---

### Task 3: `/ai-stack:up` Promptfoo Config

**Files:**
- Create: `plugins/ai-stack/evals/promptfooconfig-up.yaml`

- [ ] **Step 1: Write the config**

```yaml
description: /ai-stack:up skill evals

providers:
  - id: exec
    config:
      command: bash tools/run-skill.sh up {{scenario}}

defaultTest:
  assert:
    - type: javascript
      value: |
        try { JSON.parse(output); return true; }
        catch(e) { return { pass: false, reason: 'runner did not emit valid JSON: ' + output.slice(0,300) }; }

tests:
  - description: "Fresh directory: compose.yaml and .env created, summary shown"
    vars:
      scenario: fresh
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          if (!r.state.compose_exists)       return { pass: false, reason: 'compose.yaml not created' };
          if (!r.state.env_exists)           return { pass: false, reason: '.env not created' };
          if (!r.output.includes('ai-stack UP')) return { pass: false, reason: 'summary header missing from output' };
          return { pass: true };

  - description: "Existing compose.yaml: not overwritten (idempotent)"
    vars:
      scenario: existing-compose
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          if (r.state.compose_content !== 'original') return { pass: false, reason: 'compose.yaml was overwritten' };
          if (!r.output.includes('ai-stack UP'))      return { pass: false, reason: 'summary missing' };
          return { pass: true };

  - description: "Placeholder .env: warning shown, skill does not abort"
    vars:
      scenario: placeholder-env
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          if (!/Fill in|⚠/.test(r.output))        return { pass: false, reason: 'no placeholder warning shown' };
          if (!r.output.includes('ai-stack UP'))   return { pass: false, reason: 'skill aborted instead of continuing' };
          return { pass: true };

  - description: "No .env: template copied, placeholder warning shown"
    vars:
      scenario: no-env
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          if (!r.state.env_exists)           return { pass: false, reason: '.env not created from template' };
          if (!r.state.compose_exists)       return { pass: false, reason: 'compose.yaml not created' };
          if (!/Fill in|⚠/.test(r.output))  return { pass: false, reason: 'no placeholder warning shown' };
          return { pass: true };
```

- [ ] **Step 2: Commit**

```bash
git add plugins/ai-stack/evals/promptfooconfig-up.yaml
git commit -m "feat(evals): add promptfoo config for /ai-stack:up"
```

---

### Task 4: `/ai-stack:down` Promptfoo Config

**Files:**
- Create: `plugins/ai-stack/evals/promptfooconfig-down.yaml`

- [ ] **Step 1: Write the config**

```yaml
description: /ai-stack:down skill evals

providers:
  - id: exec
    config:
      command: bash tools/run-skill.sh down {{scenario}}

defaultTest:
  assert:
    - type: javascript
      value: |
        try { JSON.parse(output); return true; }
        catch(e) { return { pass: false, reason: 'runner did not emit valid JSON' }; }

tests:
  - description: "compose.yaml present: services stopped, summary shown"
    vars:
      scenario: has-compose
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          if (!r.output.includes('ai-stack DOWN'))       return { pass: false, reason: 'DOWN summary missing' };
          if (!r.output.includes('All services stopped')) return { pass: false, reason: '"All services stopped" missing' };
          return { pass: true };

  - description: "No compose.yaml: error shown, skill stops"
    vars:
      scenario: no-compose
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          if (!/compose\.yaml not found|run \/ai-stack:up/i.test(r.output))
            return { pass: false, reason: 'no error for missing compose.yaml' };
          return { pass: true };

  - description: "Services already stopped: idempotent, no error output"
    vars:
      scenario: already-stopped
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          if (!r.output.includes('ai-stack DOWN')) return { pass: false, reason: 'DOWN summary missing' };
          if (/\berror\b|\bfailed\b/i.test(r.output)) return { pass: false, reason: 'unexpected error in output' };
          return { pass: true };
```

- [ ] **Step 2: Commit**

```bash
git add plugins/ai-stack/evals/promptfooconfig-down.yaml
git commit -m "feat(evals): add promptfoo config for /ai-stack:down"
```

---

### Task 5: `/ai-stack:bootstrap` Promptfoo Config

**Files:**
- Create: `plugins/ai-stack/evals/promptfooconfig-bootstrap.yaml`

Note: bootstrap runs in the repo root (it registers MCPs, installs runtimes). The runner
sets `WORK_DIR` to `$(pwd)` for `bootstrap/*` scenarios. These evals are integration tests
against the real machine state and should be run on a clean dev machine or CI.

- [ ] **Step 1: Write the config**

```yaml
description: /ai-stack:bootstrap skill evals

providers:
  - id: exec
    config:
      command: bash tools/run-skill.sh bootstrap {{scenario}}

defaultTest:
  assert:
    - type: javascript
      value: |
        try { JSON.parse(output); return true; }
        catch(e) { return { pass: false, reason: 'runner did not emit valid JSON' }; }

tests:
  - description: "Prerequisites pass: BOOTSTRAP SUMMARY appears in output"
    vars:
      scenario: default
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          if (!r.output.includes('BOOTSTRAP SUMMARY')) return { pass: false, reason: 'summary missing — skill may have aborted at prerequisites' };
          if (/go.*MISSING|node.*MISSING/.test(r.output)) return { pass: false, reason: 'prerequisite check failed' };
          return { pass: true };

  - description: "Already-installed runtimes: marked 'already installed' in summary"
    vars:
      scenario: default
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          if (!r.output.includes('already installed')) return { pass: false, reason: 'no "already installed" rows — expected at least one managed runtime to be present' };
          return { pass: true };

  - description: "force: managed runtimes show 'installed' not 'already installed'"
    vars:
      scenario: force
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          const lines = r.output.split('\n');
          const uvLine = lines.find(l => l.includes('uv'));
          if (!uvLine) return { pass: false, reason: 'uv row missing from summary' };
          if (uvLine.includes('already installed')) return { pass: false, reason: 'uv was skipped despite force' };
          return { pass: true };

  - description: "Unset MCP env var: MCP skipped with reason shown"
    vars:
      scenario: default
    assert:
      - type: javascript
        value: |
          // Only meaningful when DEVLAKE_MCP_SECRET_KEY is unset.
          // If the var is set in the environment, this test is a no-op (returns pass).
          const r = JSON.parse(output);
          if (process.env.DEVLAKE_MCP_SECRET_KEY) return { pass: true };
          if (!r.output.includes('DEVLAKE_MCP_SECRET_KEY not set'))
            return { pass: false, reason: 'MCP skip reason not shown for unset var' };
          return { pass: true };
```

- [ ] **Step 2: Commit**

```bash
git add plugins/ai-stack/evals/promptfooconfig-bootstrap.yaml
git commit -m "feat(evals): add promptfoo config for /ai-stack:bootstrap"
```

---

### Task 6: `/ai-stack:project-init` Promptfoo Config

**Files:**
- Create: `plugins/ai-stack/evals/promptfooconfig-project-init.yaml`

- [ ] **Step 1: Write the config**

```yaml
description: /ai-stack:project-init skill evals

providers:
  - id: exec
    config:
      command: bash tools/run-skill.sh project-init {{scenario}}

defaultTest:
  assert:
    - type: javascript
      value: |
        try { JSON.parse(output); return true; }
        catch(e) { return { pass: false, reason: 'runner did not emit valid JSON' }; }

tests:
  - description: "Empty directory: CLAUDE.md and AGENTS.md created"
    vars:
      scenario: empty
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          if (!r.state.claude_md_exists)  return { pass: false, reason: 'CLAUDE.md not created' };
          if (!r.state.agents_md_exists)  return { pass: false, reason: 'AGENTS.md not created' };
          if (!r.output.includes('created')) return { pass: false, reason: 'no "created" status in summary' };
          return { pass: true };

  - description: "CLAUDE.md exists without force: skipped, not overwritten"
    vars:
      scenario: existing-md
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          if (r.state.claude_md_content !== 'existing content')
            return { pass: false, reason: 'CLAUDE.md was overwritten despite no force flag' };
          if (!r.output.includes('skipped')) return { pass: false, reason: 'no "skipped" status in summary' };
          return { pass: true };

  - description: "force: existing CLAUDE.md overwritten with template content"
    vars:
      scenario: force
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          if (r.state.claude_md_content === 'old content')
            return { pass: false, reason: 'CLAUDE.md not overwritten despite force' };
          if (!r.state.claude_md_exists) return { pass: false, reason: 'CLAUDE.md missing after force' };
          if (!r.output.includes('overwritten')) return { pass: false, reason: 'no "overwritten" status in summary' };
          return { pass: true };

  - description: "Empty directory: optional skills section shown in output"
    vars:
      scenario: empty
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          if (!r.output.includes('Optional skills')) return { pass: false, reason: 'optional skills prompt not shown' };
          return { pass: true };
```

- [ ] **Step 2: Commit**

```bash
git add plugins/ai-stack/evals/promptfooconfig-project-init.yaml
git commit -m "feat(evals): add promptfoo config for /ai-stack:project-init"
```

---

### Task 7: `just eval` Recipe

**Files:**
- Modify: `justfile`

- [ ] **Step 1: Add `eval` recipe to `justfile`**

Add after the `lince` recipe:

```just
# Run ai-stack skill evals with promptfoo.
# skill: up|down|bootstrap|project-init|all (default: all)
# pattern: substring filter on test description (default: run all)
# repeat: run each test N times for pass@k (default: 1)
eval skill='all' pattern='' repeat='1':
    #!/bin/bash
    set -euo pipefail
    skills=( up down bootstrap project-init )
    [[ "{{skill}}" != "all" ]] && skills=( "{{skill}}" )
    for s in "${skills[@]}"; do
        cfg="plugins/ai-stack/evals/promptfooconfig-${s}.yaml"
        [[ -f "$cfg" ]] || { echo "No eval config for skill: $s"; continue; }
        args=( --config "$cfg" --no-cache )
        [[ -n "{{pattern}}" ]] && args+=( --filter-pattern "{{pattern}}" )
        [[ "{{repeat}}" != "1" ]] && args+=( --repeat "{{repeat}}" )
        npx --yes promptfoo eval "${args[@]}"
    done
```

- [ ] **Step 2: Verify recipe syntax**

```bash
just --list | grep eval
```

Expected: `eval` appears in the list.

- [ ] **Step 3: Commit**

```bash
git add justfile
git commit -m "feat(evals): add just eval recipe (promptfoo runner)"
```

---

### Task 8: `/ai-stack:status` Skill

**Files:**
- Create: `plugins/ai-stack/skills/status/SKILL.md`

- [ ] **Step 1: Write `skills/status/SKILL.md`**

```markdown
---
description: Show the current health of all ai-stack compose services with endpoints.
---

# /ai-stack:status

## Synopsis

```
/ai-stack:status   ← show service health for the compose stack in CWD
```

---

## Process

### Step 1 — Prerequisites check

Run:

```bash
(command -v podman >/dev/null 2>&1 && podman compose version >/dev/null 2>&1 && echo "podman") \
  || (command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1 && echo "docker") \
  || echo "MISSING"
```

If neither is found, stop and display:

```
✗ podman / docker compose: not found
```

### Step 2 — Check compose.yaml

```bash
ls compose.yaml 2>/dev/null && echo "exists" || echo "missing"
```

If missing, display:

```
✗ compose.yaml not found in current directory.
  Run /ai-stack:up first.
```

### Step 3 — Collect status

Run:

```bash
podman compose ps   # or: docker compose ps
```

### Step 4 — Display summary

Print a table with a row per service. Show `running` or `exited`. Include known
endpoints for running services (source from compose.yaml ports mapping):

```
=== ai-stack STATUS ===

Service                   Status     Endpoint
────────────────────────────────────────────────────────────
notebooklm-mcp            running    http://localhost:17200/mcp
                                     noVNC: http://localhost:17201/vnc.html
workspace-mcp             running    http://localhost:17150/mcp
devlake-local-mysql-mcp   exited
devlake-prod-mysql-mcp    running    http://localhost:17300/mcp

Config: <absolute path to CWD>/.env
========================
```

For any `exited` service, append a hint on the next line:

```
✗ devlake-local-mysql-mcp exited — check its required variables in .env
```
```

- [ ] **Step 2: Update `plugins/ai-stack/README.md`**

Add `status` to the Skills table:

```markdown
| `/ai-stack:status` | Show compose service health + endpoints |
```

Add an Evals section after the Skills table:

```markdown
## Evals

Eval scenarios for each skill live in `evals/promptfooconfig-<skill>.yaml`.

```bash
just eval up                   # all scenarios for one skill
just eval up "Fresh directory"  # filter by description
just eval "" "" 3              # all skills, pass@3
just eval                      # all skills, all scenarios
```

See `evals/framework.md` for conventions and the TDD cycle.
```

- [ ] **Step 3: Update `plugins/ai-stack/reference/CLAUDE.md`**

Add to skills table:

```
| `/ai-stack:status` | Check service health |
```

- [ ] **Step 4: Commit**

```bash
git add plugins/ai-stack/skills/status/SKILL.md \
        plugins/ai-stack/README.md \
        plugins/ai-stack/reference/CLAUDE.md
git commit -m "feat(skills): add /ai-stack:status skill"
```

---

### Task 9: Hooks Reference Doc

**Files:**
- Create: `plugins/ai-stack/reference/hooks.md`

- [ ] **Step 1: Write `hooks.md`**

```markdown
# Claude Hooks Reference

Claude Code supports shell hooks — commands that run automatically on events.

## Hook events

| Event | When it fires |
|---|---|
| `PreToolUse` | Before any tool call |
| `PostToolUse` | After any tool call |
| `Stop` | When the agent stops producing output |
| `SubagentStop` | When a subagent stops |

## Settings location

Hooks are defined in `~/.claude/settings.json` (user scope) or `.claude/settings.json`
(project scope, committed to repo).

## Format

```json
{
  "hooks": {
    "<Event>": [
      {
        "matcher": "<tool-name or glob or *>",
        "hooks": [
          { "type": "command", "command": "<shell command>" }
        ]
      }
    ]
  }
}
```

## Example: session-start environment check

This hook fires on the first tool use of each session and injects environment status
(git state, .env presence, running services) as a system-reminder:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          { "type": "command", "command": "~/.claude/scripts/session-start.sh" }
        ]
      }
    ]
  }
}
```

Save the script to `~/.claude/scripts/session-start.sh` and make it executable:

```bash
mkdir -p ~/.claude/scripts
chmod +x ~/.claude/scripts/session-start.sh
```

## Debugging hooks

```bash
# Test a hook manually
bash ~/.claude/scripts/session-start.sh

# Hook output appears in Claude's system-reminder messages during a session
```

To remove a hook: delete its entry from `~/.claude/settings.json`.
```

- [ ] **Step 2: Commit**

```bash
git add plugins/ai-stack/reference/hooks.md
git commit -m "docs: add Claude hooks reference"
```

---

### Task 10: Bump Version + Reload Plugin

**Files:**
- Modify: `plugins/ai-stack/.claude-plugin/plugin.json`

- [ ] **Step 1: Bump version to 0.11.0**

Edit `plugins/ai-stack/.claude-plugin/plugin.json`:

```json
{
  "version": "0.11.0"
}
```

(Change only the `version` field; leave all other fields unchanged.)

- [ ] **Step 2: Commit and push**

```bash
git add plugins/ai-stack/.claude-plugin/plugin.json
git commit -m "chore: bump ai-stack plugin to 0.11.0"
git push
```

- [ ] **Step 3: Update and reload plugin**

```bash
claude plugin marketplace update ai-stack
claude plugin update ai-stack@ai-stack
```

Expected: `claude plugin list` shows version 0.11.0.

---

## Self-Review

**Spec coverage:**
- Eval framework with promptfoo → Task 1 (conventions) + Tasks 3–6 (configs) ✓
- Runner script → Task 2 ✓
- `just eval` → Task 7 ✓
- `/ai-stack:status` skill → Task 8 ✓
- Hooks reference → Task 9 ✓
- Version bump → Task 10 ✓

**Grader approach:** All JS graders check `r.state.*` (filesystem) and `r.output` text — observable outcomes, not tool sequences.

**bootstrap caveat:** bootstrap evals run against real machine state (they register MCPs, install runtimes). They're integration tests, not unit tests. Mark them with a comment in the config; CI should gate on `up`, `down`, `project-init` only and run `bootstrap` manually.

**pass@k:** `just eval up "" 3` passes `--repeat 3` to promptfoo; it reports how many of 3 runs passed. Promptfoo's HTML report shows per-attempt results.
