set dotenv-load

default:
    @just --list

# Build OpenShell binaries + sideload image, restart the gateway, and register the vertex-claude provider.
# Pass force=true to rebuild even when binaries/image already exist.
# Requires env: OPENSHELL_DIR, ANTHROPIC_VERTEX_PROJECT_ID, CLAUDE_CODE_USE_VERTEX, CLOUD_ML_REGION
openshell-bootstrap rebuild='':
    #!/bin/bash
    set -euo pipefail
    [[ -f .env ]] && { set -a; source .env; set +a; }
    : "${OPENSHELL_DIR:?must be set — add to .env}"
    : "${ANTHROPIC_VERTEX_PROJECT_ID:?must be set — add to .env}"
    : "${CLAUDE_CODE_USE_VERTEX:?must be set — add to .env}"
    : "${CLOUD_ML_REGION:?must be set — add to .env}"
    GATEWAY_PORT="${OPENSHELL_PORT:-17711}"
    SUPERVISOR_IMAGE="${OPENSHELL_SUPERVISOR_IMAGE:-openshell/supervisor:dev}"

    echo "==> Checking prerequisites..."
    missing=()
    for tool in bash sccache mise gh z3 cargo; do
        command -v "$tool" &>/dev/null || missing+=("$tool")
    done
    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "ERROR: Missing tools: ${missing[*]}" >&2
        echo "       brew install bash sccache mise gh z3" >&2
        echo "       (cargo comes from mise or rustup.rs)" >&2
        exit 1
    fi
    if ! podman info &>/dev/null 2>&1; then
        echo "ERROR: Podman is not running — start Podman Desktop first." >&2
        exit 1
    fi

    cd "$OPENSHELL_DIR"

    if [[ -n "{{rebuild}}" ]] || [[ ! -f ~/.local/bin/openshell-gateway ]]; then
        ulimit -n 10240
        echo "==> Building openshell gateway..."
        cargo build -p openshell-server --bin openshell-gateway --release
        echo "==> Installing openshell gateway..."
        cargo install --locked --path crates/openshell-server --bin openshell-gateway --root ~/.local
    else
        echo "==> Gateway binary exists — skipping build (just openshell-bootstrap rebuild to force)"
    fi

    if [[ -n "{{rebuild}}" ]] || ! podman image exists "$SUPERVISOR_IMAGE" 2>/dev/null; then
        echo "==> Building supervisor sideload image ($SUPERVISOR_IMAGE)..."
        ulimit -n 10240
        PATH="$(brew --prefix)/bin:$PATH" mise run build:docker:supervisor-sideload
        if [[ "$SUPERVISOR_IMAGE" != "openshell/supervisor:dev" ]] && \
           [[ "$SUPERVISOR_IMAGE" != "localhost/openshell/supervisor:dev" ]]; then
            podman tag openshell/supervisor:dev "$SUPERVISOR_IMAGE"
        fi
    else
        echo "==> Sideload image $SUPERVISOR_IMAGE exists — skipping (just openshell-bootstrap rebuild to force)"
    fi

    echo "==> Stopping any running gateway..."
    pkill -f openshell-gateway 2>/dev/null || true
    sleep 1

    echo "==> Starting gateway on port $GATEWAY_PORT..."
    OPENSHELL_SSH_HANDSHAKE_SECRET="$(openssl rand -hex 32)" \
    OPENSHELL_SUPERVISOR_IMAGE="$SUPERVISOR_IMAGE" \
      ~/.local/bin/openshell-gateway \
        --port "$GATEWAY_PORT" \
        --drivers podman \
        --disable-tls \
        --db-url "sqlite::memory:" \
        >> /tmp/openshell-gateway.log 2>&1 &
    GATEWAY_PID=$!
    echo "==> Gateway started (PID $GATEWAY_PID), log: /tmp/openshell-gateway.log"
    echo "==> Waiting for readiness..."
    sleep 3

    echo "==> Registering vertex-claude provider..."
    OPENSHELL_GATEWAY_ENDPOINT="http://127.0.0.1:$GATEWAY_PORT" \
      openshell provider create --name vertex-claude --type vertex-claude --from-existing
    echo "==> Done. Gateway PID: $GATEWAY_PID"

# Delete all sandboxes, stop the OpenShell gateway, and clean up sandbox staging files.
openshell-teardown:
    #!/bin/bash
    set -euo pipefail
    GATEWAY_PORT="${OPENSHELL_PORT:-17711}"
    echo "==> Deleting all sandboxes..."
    OPENSHELL_GATEWAY_ENDPOINT="http://127.0.0.1:$GATEWAY_PORT" \
      openshell sandbox delete --all 2>/dev/null \
        && echo "    Sandboxes deleted." \
        || echo "    Gateway unreachable — skipping sandbox deletion."
    echo "==> Stopping OpenShell gateway..."
    pkill -f openshell-gateway 2>/dev/null \
        && echo "    Gateway stopped." \
        || echo "    Gateway was not running."
    echo "==> Cleaning up /tmp/cs/..."
    rm -rf /tmp/cs
    echo "==> Done."

# Install or update the LINCE toolkit (agent-sandbox + lince-dashboard).
# Runs the interactive TUI quickstart installer from the lince/ submodule.
lince-bootstrap:
    cd lince && bash quickstart.sh

# Launch the LINCE dashboard (Zellij + lince-dashboard plugin).
lince:
    zd

# Launch Claude Code in an OpenShell sandbox with Vertex AI credentials.
# Generates claude-vertex-wrapper dynamically from current env vars — no credentials stored in repo.
# Requires env: OPENSHELL_DIR, ANTHROPIC_VERTEX_PROJECT_ID, CLAUDE_CODE_USE_VERTEX,
#               CLOUD_ML_REGION, GOOGLE_APPLICATION_CREDENTIALS
openshell:
    #!/bin/bash
    set -euo pipefail
    [[ -f .env ]] && { set -a; source .env; set +a; }
    : "${OPENSHELL_DIR:?must be set — add to .env}"
    : "${ANTHROPIC_VERTEX_PROJECT_ID:?must be set — add to .env}"
    : "${CLAUDE_CODE_USE_VERTEX:?must be set — add to .env}"
    : "${CLOUD_ML_REGION:?must be set — add to .env}"
    : "${GOOGLE_APPLICATION_CREDENTIALS:?must be set — add to .env}"
    GATEWAY_PORT="${OPENSHELL_PORT:-17711}"
    if [[ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]]; then
        echo "ERROR: ADC credentials not found at $GOOGLE_APPLICATION_CREDENTIALS" >&2
        echo "       Run: gcloud auth application-default login" >&2
        exit 1
    fi
    mkdir -p /tmp/cs/claude-config
    cp "$GOOGLE_APPLICATION_CREDENTIALS" /tmp/cs/adc.json
    cp -r ~/.claude/. /tmp/cs/claude-config/ 2>/dev/null || true
    {
      echo '#!/bin/bash'
      echo "export ANTHROPIC_VERTEX_PROJECT_ID=${ANTHROPIC_VERTEX_PROJECT_ID}"
      echo "export CLAUDE_CODE_USE_VERTEX=${CLAUDE_CODE_USE_VERTEX}"
      echo "export CLOUD_ML_REGION=${CLOUD_ML_REGION}"
      echo "export ANTHROPIC_MODEL=${ANTHROPIC_MODEL:-claude-sonnet-4-6}"
      cat << 'WRAPPER_EOF'
    export GOOGLE_APPLICATION_CREDENTIALS=/tmp/cs/adc.json
    export CLAUDE_CONFIG_DIR=/tmp/cs/claude-config
    if [ -f "$CLAUDE_CONFIG_DIR/claude.json" ] && [ ! -f "$CLAUDE_CONFIG_DIR/.claude.json" ]; then
      cp "$CLAUDE_CONFIG_DIR/claude.json" "$CLAUDE_CONFIG_DIR/.claude.json"
    fi
    exec claude "$@"
    WRAPPER_EOF
    } > /tmp/cs/claude-vertex-wrapper
    chmod +x /tmp/cs/claude-vertex-wrapper
    OPENSHELL_GATEWAY_ENDPOINT="http://127.0.0.1:$GATEWAY_PORT" \
      openshell sandbox create \
        --policy ./openshell/policy.yaml \
        --upload /tmp/cs:/tmp \
        --no-keep -- /tmp/cs/claude-vertex-wrapper
