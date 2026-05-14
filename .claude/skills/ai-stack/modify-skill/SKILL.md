---
description: Scaffold a new built-in skill in the ai-stack plugin — creates SKILL.md, eval config, runner setup, and wires everything together.
argument-hint: "[skill-name]"
---

# /ai-stack:modify-skill

Project-local dev tool for the ai-stack repo. Creates all the boilerplate for
a new built-in skill: SKILL.md template, promptfoo eval config, runner scenario
setup in `tools/run-skill.py`, and a slot in the `just eval` recipe.

## Synopsis

```
/ai-stack:modify-skill <name>   ← scaffold a new skill named <name>
/ai-stack:modify-skill          ← interactive: ask for name
```

---

## Working directory assumption

This skill is repo-local. All paths below are relative to the **repo root**
(the directory containing `plugins/`, `tools/`, `justfile`). Confirm the
current working directory is the repo root before proceeding.

---

## Process

### Step 1 — Gather inputs

If `<name>` was not provided as an argument, ask:

```
Skill name (kebab-case, e.g. "restart"):
```

Validate:
- Must be kebab-case (`[a-z][a-z0-9-]*`)
- Must not already exist: `plugins/ai-stack/skills/<name>/SKILL.md`

If it already exists, stop and display:

```
✗ plugins/ai-stack/skills/<name>/SKILL.md already exists.
  Use a different name or edit the file directly.
```

Ask for a one-line description:

```
Description (one line, e.g. "Restart all compose services"):
```

### Step 2 — Preview

Show everything that will be created or modified before touching any file:

```
=== modify-skill PREVIEW ===

Create: plugins/ai-stack/skills/<name>/SKILL.md
Create: plugins/ai-stack/evals/promptfooconfig-<name>.yaml
Modify: tools/run-skill.py          ← add <name>/default scenario case
Modify: justfile                    ← add <name> to just eval skills list
Bump:   plugins/ai-stack/.claude-plugin/plugin.json  <current> → <minor+1>.0

============================
Proceed? (yes / cancel)
```

Wait for confirmation. On "cancel", exit without writing anything.

### Step 3 — Create SKILL.md

Write `plugins/ai-stack/skills/<name>/SKILL.md`:

```markdown
---
description: <description>
---

# /ai-stack:<name>

## Synopsis

```
/ai-stack:<name>   ← <description>
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

### Step 2 — TODO

<!-- Describe what this skill does -->

### Step 3 — Summary

```
=== ai-stack <NAME> ===

<!-- Add summary output here -->

=======================
```
```

### Step 4 — Create eval config

Write `plugins/ai-stack/evals/promptfooconfig-<name>.yaml`:

```yaml
description: /ai-stack:<name> skill evals

prompts:
  - '{{scenario}}'

providers:
  - 'exec: python3 ../../../tools/run-skill.py <name>'

defaultTest:
  assert:
    - type: javascript
      value: |
        try { JSON.parse(output); return true; }
        catch(e) { return { pass: false, score: 0, reason: 'runner did not emit valid JSON: ' + output.slice(0,300) }; }

tests:
  - description: "Default: skill completes successfully"
    vars:
      scenario: default
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          // TODO: add assertions specific to this skill
          // r.output — full Claude text output
          // r.state  — filesystem state (compose_exists, env_exists, claude_md_exists, …)
          return { pass: true, score: 1, reason: 'ok' };
```

### Step 5 — Add runner scenario

Read `tools/run-skill.py`. Find the `elif skill == "bootstrap":` line inside
`setup_scenario()`. Insert a new block **immediately before** that line:

```python
    elif skill == "<name>":
        pass  # TODO: add scenario setup (copy compose.yaml, .env, etc.)
```

Use the Edit tool to make this targeted insertion without touching any other code.

### Step 6 — Wire into just eval

Read `justfile`. Find the line:

```
    skills=( up down bootstrap project-init status )
```

Append `<name>` to the list:

```
    skills=( up down bootstrap project-init status <name> )
```

Also update the comment on the line above it to include `<name>`:

```
# skill: up|down|bootstrap|project-init|status|<name>|all (default: all)
```

Use the Edit tool to make this targeted replacement.

### Step 7 — Bump plugin version

Read `plugins/ai-stack/.claude-plugin/plugin.json`. Increment the minor version,
reset patch to 0 (e.g. `0.12.0` → `0.13.0`). Write the updated file.

Also read `.claude-plugin/marketplace.json`. Find the `"ai-stack"` plugin entry
and update its `"version"` field to match. Write the updated file.

### Step 8 — Summary and offer commit

Report what was done:

```
=== modify-skill DONE ===

Created:  plugins/ai-stack/skills/<name>/SKILL.md
Created:  plugins/ai-stack/evals/promptfooconfig-<name>.yaml
Modified: tools/run-skill.py
Modified: justfile
Bumped:   plugin version <old> → <new>

Next steps:
  1. Edit plugins/ai-stack/skills/<name>/SKILL.md — fill in the skill logic
  2. Edit plugins/ai-stack/evals/promptfooconfig-<name>.yaml — add real assertions
  3. Edit tools/run-skill.py — add scenario setup for each test case
  4. Run: just eval <name>

=========================
```

Ask: "Commit scaffold? (yes / no)"

If yes:

```bash
git add plugins/ai-stack/skills/<name>/SKILL.md \
        plugins/ai-stack/evals/promptfooconfig-<name>.yaml \
        tools/run-skill.py \
        justfile \
        plugins/ai-stack/.claude-plugin/plugin.json \
        .claude-plugin/marketplace.json
git commit -m "feat(ai-stack): scaffold /ai-stack:<name> skill"
```
