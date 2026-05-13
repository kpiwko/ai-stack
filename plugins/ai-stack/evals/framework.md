# ai-stack Eval Framework

Evals use [promptfoo](https://promptfoo.dev) as the test runner.

## How it works

Each skill has a `promptfooconfig-<skill>.yaml` that declares test scenarios.
The shared runner (`tools/run-skill.py`) handles each eval run:

1. Create a temp directory (`EVAL_DIR`) for file isolation
2. Run scenario-specific setup — seed files the skill expects to find (compose.yaml, .env, CLAUDE.md)
3. Read the skill's `SKILL.md` from `plugins/ai-stack/skills/<name>/SKILL.md` and build a prompt:
   - Prepend `Base directory for this skill: <path>` and `Invoked as: /ai-stack:<skill> <args>`
   - Pass the combined text as `claude -p <prompt>`
4. Collect filesystem state from `EVAL_DIR` after claude exits
5. Emit JSON to stdout: `{"output": "<claude text>", "state": {...}}`

Promptfoo's `exec` provider captures this JSON. JavaScript graders check observable
outcomes — not which tools Claude called.

## Why SKILL.md is passed as a prompt (not via plugin invocation)

The original design invoked `claude -p "/ai-stack:<skill>"`. This required the plugin
to be globally installed (the subprocess reads `~/.claude/plugins/cache/`), which meant
you had to push and run `/plugin update` before testing local changes. The current approach
reads SKILL.md directly from the local repo and passes it as the `-p` prompt — no plugin
installation needed, no push required.

The `--add-dir` flags give Claude file access without affecting skill discovery:
- `--add-dir <eval_dir>` — lets Claude read/write the isolated test directory (compose.yaml, .env, etc.)
- `--add-dir plugins/ai-stack` — lets Claude read reference files (`../reference/compose.yaml`, etc.)

Bootstrap runs in the repo root instead of a temp dir (it reads machine state and runs
real commands), so it uses `--add-dir <repo_root>` instead.

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

Graders are written as inline JavaScript in the `assert` block of each promptfoo YAML config.

## State fields collected by `tools/run-skill.py`

| Field | Type | Description |
|---|---|---|
| `compose_exists` | bool | `compose.yaml` present in EVAL_DIR |
| `env_exists` | bool | `.env` present in EVAL_DIR |
| `env_content` | string | Content of `.env` (empty if absent) |
| `compose_content` | string | Content of `compose.yaml` (empty if absent) |
| `claude_md_exists` | bool | `CLAUDE.md` present in EVAL_DIR |
| `claude_md_content` | string | Content of `CLAUDE.md` |
| `agents_md_exists` | bool | `AGENTS.md` present in EVAL_DIR |
| `skill_dir_exists` | bool | `.claude/skills/` present in EVAL_DIR |

> Fields are additive — see the relevant `promptfooconfig-<skill>.yaml` for the full field list used by each scenario.

## Adding a new skill to evals

1. Create `plugins/ai-stack/evals/promptfooconfig-<skill>.yaml`
2. Add scenario setup cases to `tools/run-skill.py` → `setup_scenario()`
3. If the skill produces new filesystem artifacts, add fields to `collect_state()`
4. Add the skill name to the `just eval` recipe in `justfile`
