#!/usr/bin/env bash
# tools/run-skill.sh <skill> <scenario>
# Outputs JSON to stdout for promptfoo exec provider:
#   {"output": "<claude text>", "state": {<filesystem state>}}
set -euo pipefail

SKILL="${1:?skill required (up|down|bootstrap|project-init)}"
SCENARIO=$(cat)
[[ -z "$SCENARIO" ]] && SCENARIO="default"
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
env_content=$(cat "$EVAL_DIR/.env"               2>/dev/null || true)
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
  --arg     env_content       "$env_content" \
  --arg     claude_md_content "$claude_md_content" \
  '{output: $out, state: {
      compose_exists:    $compose_exists,
      env_exists:        $env_exists,
      claude_md_exists:  $claude_md_exists,
      agents_md_exists:  $agents_md_exists,
      skill_dir_exists:  $skill_dir_exists,
      compose_content:   $compose_content,
      env_content:       $env_content,
      claude_md_content: $claude_md_content
  }}'
