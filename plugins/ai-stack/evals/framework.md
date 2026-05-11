# ai-stack Eval Framework

Evals use [promptfoo](https://promptfoo.dev) as the test runner.

## How it works

Each skill has a `promptfooconfig-<skill>.yaml` that declares test scenarios.
A shared runner script (`tools/run-skill.sh`) handles:

1. Create a temp directory (`$EVAL_DIR`)
2. Run scenario-specific setup (seed files declared in the YAML `setup` field or by `run-skill.sh`'s built-in case block)
3. Invoke `claude -p "/ai-stack:<skill> <args>"` from `$EVAL_DIR`
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

Graders are written as inline JavaScript in the `assert` block of each promptfoo YAML config. They do not live in separate files.

## State fields collected by `tools/run-skill.sh`

| Field | Type | Description |
|---|---|---|
| `compose_exists` | bool | `compose.yaml` present in EVAL_DIR |
| `env_exists` | bool | `.env` present in EVAL_DIR |
| `env_content` | string | Content of `.env` (empty if absent; secrets redacted) |
| `compose_content` | string | Content of `compose.yaml` (empty if absent) |
| `claude_md_exists` | bool | `CLAUDE.md` present in EVAL_DIR |
| `claude_md_content` | string | Content of `CLAUDE.md` |
| `agents_md_exists` | bool | `AGENTS.md` present in EVAL_DIR |
| `skill_dir_exists` | bool | `.claude/skills/` present in EVAL_DIR |

> Note: the table above shows the fields currently emitted by `run-skill.sh`. Fields are additive — each skill's scenarios may emit additional fields. See the relevant `promptfooconfig-<skill>.yaml` for the full field list.
