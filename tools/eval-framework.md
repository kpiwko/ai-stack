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

Eval configs are auto-discovered from `plugins/*/evals/promptfooconfig-*.yaml`.

```bash
# All scenarios for one skill (execution or activation)
just eval up
just eval jira-activation

# Filter by description substring
just eval up "Fresh directory"

# Pass@k (repeat each test 3 times, pass if any succeeds)
just eval jira-activation "" 3

# All skills across all plugins
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

## Activation evals

Activation evals test whether Claude would **invoke** the right skill given a
natural language prompt — distinct from execution evals which test what happens
once a skill runs.

The runner (`tools/run-activation-eval.py`) auto-discovers skill descriptions
from `plugins/*/skills/*/SKILL.md` frontmatter and builds a skills listing. It
asks Claude which skill matches a given user message, then emits:

```json
{"output": "<raw text>", "invoked_skill": "<skill name or none>"}
```

Activation eval configs live alongside execution evals and follow the naming
convention `promptfooconfig-<name>-activation.yaml`. Graders check
`r.invoked_skill` against the expected value.

### Writing activation scenarios

Each scenario provides a natural language user message and asserts which skill
should (or should not) be invoked:

```yaml
tests:
  - description: "positive: user asks to create a Jira ticket"
    vars:
      scenario: "can we create a JIRA to track this work?"
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          if (r.invoked_skill !== 'track:jira')
            return { pass: false, score: 0, reason: `expected track:jira, got ${r.invoked_skill}` };
          return { pass: true, score: 1, reason: 'ok' };

  - description: "negative: unrelated request"
    vars:
      scenario: "can you write a README?"
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          if (r.invoked_skill === 'track:jira')
            return { pass: false, score: 0, reason: 'false positive' };
          return { pass: true, score: 1, reason: 'ok' };
```

Use pass@3 (`just eval <name> "" 3`) for reliability — LLM-as-judge results
can vary between runs.

## Adding a new skill to evals

### Execution evals

1. Create `plugins/<plugin>/evals/promptfooconfig-<skill>.yaml`
2. Add scenario setup cases to `tools/run-skill.py` → `setup_scenario()`
3. If the skill produces new filesystem artifacts, add fields to `collect_state()`

### Activation evals

1. Create `plugins/<plugin>/evals/promptfooconfig-<skill>-activation.yaml`
2. Add positive scenarios (should invoke the skill) and negative scenarios (should not)
3. If the skill description doesn't trigger reliably, add "Use when..." cues to the SKILL.md frontmatter

Both types are auto-discovered by `just eval` from `plugins/*/evals/promptfooconfig-*.yaml`.
