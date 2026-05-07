# OpenShell Podman Driver — Local Bootstrap

Instructions for running the OpenShell gateway with the Podman compute driver
on macOS (Apple Silicon). This bypasses the default k3s-based gateway and runs
sandboxes as rootless Podman containers instead.

## Prerequisites

```bash
brew install bash sccache mise gh
```

Ensure Podman Desktop is running with its Docker-compat socket active.

## One-time setup

### 1. Clone and enter the OpenShell repo

```bash
git clone https://github.com/NVIDIA/OpenShell ~/devel/work/OpenShell
cd ~/devel/work/OpenShell
```

### 2. Install mise toolchain

```bash
export GITHUB_TOKEN=$(gh auth token)
mise install
```

### 3. Build the gateway binary

```bash
cargo build -p openshell-server --release
```

### 4. Build the supervisor sideload image

The supervisor image is a scratch container with only the `openshell-sandbox`
binary. It must be built locally — it is not published to a registry.

```bash
ulimit -n 10240 && PATH="$(brew --prefix)/bin:$PATH" mise run build:docker:supervisor-sideload
```

This produces `localhost/openshell/supervisor:dev` in the local Podman image store.

## Running the gateway

Start in a dedicated terminal — the gateway runs in the foreground:

```bash
OPENSHELL_SSH_HANDSHAKE_SECRET="$(openssl rand -hex 32)" \
OPENSHELL_SUPERVISOR_IMAGE="openshell/supervisor:dev" \
  ~/devel/work/OpenShell/target/release/openshell-gateway \
    --port 17711 \
    --drivers podman \
    --disable-tls \
    --db-url "sqlite::memory:"
```

## Using the CLI

Point the CLI at the local gateway and create a sandbox:

```bash
export OPENSHELL_GATEWAY_ENDPOINT="http://127.0.0.1:17711"

# Verify connectivity
openshell status

# Create an interactive sandbox (no network policy)
openshell sandbox create --no-keep -- bash

# Create a sandbox with a specific image
openshell sandbox create --from ubuntu --no-keep -- bash

# Create a sandbox with the ai-stack network policy (required for MCP access)
openshell sandbox create --policy ./openshell/policy.yaml --no-keep -- claude
```

## Verifying DNS and network inside a sandbox

`ping` is blocked by the sandbox seccomp policy. Use these instead:

```bash
# Check /etc/hosts — host.containers.internal should be present (Podman driver)
cat /etc/hosts

# Check DNS resolver config
cat /etc/resolv.conf

# Resolve a hostname
getent hosts host.containers.internal

# Test HTTP reachability of an MCP endpoint (e.g. workspace-mcp on port 17150)
curl -v http://host.containers.internal:17150/mcp
```

Note: with the Podman driver the host gateway is `host.containers.internal`
(at `192.168.127.254`). The policy file uses `host.containers.internal` — verify
it appears in `/etc/hosts` inside the sandbox before testing MCP connectivity.

### Policy protocol field

For plain TCP (L4-only) access, **omit the `protocol` field entirely**. The
`protocol` field is only for L7 inspection (`rest`, `graphql`, `sql`). Including
`protocol: tcp` causes a validation error; leaving it out gives L4-only enforcement.

## Running Claude Code in a sandbox (Vertex AI)

> **This is a temporary workaround.** OpenShell does not yet have native Vertex AI support.
> Issue [#472](https://github.com/NVIDIA/OpenShell/issues/472) tracks the addition of a
> `vertex` provider type with automatic OAuth2 token refresh. Once merged, the workflow
> simplifies to a single `openshell sandbox create -- claude` with a pre-configured provider.
> Until then, the wrapper-script approach below is required.

Claude Code inside a sandbox requires:

1. **Vertex AI env vars** — injected via the `vertex-claude` provider
2. **Google ADC credentials** — uploaded into the sandbox at runtime
3. **A wrapper script** — sets env vars and execs `claude` (OpenShell providers
   inject credentials for L7 proxy enforcement only, not as process env vars)

### One-time: build OpenShell with the vertex-claude provider

The `vertex-claude` provider type is not upstream — it lives in a local patch.
`brew install z3` is a required build dependency for the SMT solver used by the
sandbox policy engine.

```bash
brew install z3
```

### Using `just` goals (recommended)

All env vars are read from `.env` (loaded automatically by `just`). Copy
`env.example` and fill in the OpenShell section before running any goal.

| Goal | What it does |
|---|---|
| `just openshell-bootstrap` | Check prereqs, build binaries + sideload image, restart gateway, register provider |
| `just openshell-bootstrap force` | Same but forces rebuild of binaries and sideload image |
| `just openshell` | Generate wrapper from env vars, stage credentials, launch sandbox |
| `just openshell-teardown` | Kill the gateway and clean up `/tmp/cs/` |

Required `.env` keys (see `env.example` for the full template):

```
OPENSHELL_DIR=/path/to/OpenShell
GOOGLE_APPLICATION_CREDENTIALS=/path/to/adc.json
ANTHROPIC_VERTEX_PROJECT_ID=<your-gcp-project>
CLAUDE_CODE_USE_VERTEX=1
CLOUD_ML_REGION=global
```

`openshell-bootstrap` checks that `bash sccache mise gh z3 cargo` are all in
`PATH` and that Podman is running before attempting any build. It skips the
binary build and sideload image build when they already exist; pass `force`
to rebuild unconditionally.

### Manual steps (reference)

Build and install the gateway binary after any `git pull`:

```bash
cd ~/devel/work/OpenShell
cargo build -p openshell-server --bin openshell-gateway --release
cargo install --locked --path crates/openshell-server --bin openshell-gateway --root ~/.local
```

Register the provider (lost on every gateway restart — `just openshell-bootstrap`
handles this automatically):

```bash
# ANTHROPIC_VERTEX_PROJECT_ID, CLAUDE_CODE_USE_VERTEX, CLOUD_ML_REGION must be set
OPENSHELL_GATEWAY_ENDPOINT="http://127.0.0.1:17711" \
  openshell provider create --name vertex-claude --type vertex-claude --from-existing
```

Notes on the sandbox launch:

- `--upload DIR:/tmp` places `DIR/` under `/tmp/` in the sandbox (files at `/tmp/cs/`).
  Using `--upload DIR:/tmp/cs` nests one level deeper — avoid this.
- `exec claude` replaces the shell process so network connections originate from
  `/usr/local/bin/claude` and pass the policy binary check.
- `CLAUDE_CONFIG_DIR` with a custom path causes Claude to look for `.claude.json`
  (hidden, with dot). The wrapper self-heals by copying `claude.json` → `.claude.json`
  on startup.

## Known issues

### Spurious `/etc/subuid` warning on macOS

```
WARN Rootless Podman detected but no /etc/subuid or /etc/subgid entry found
```

This warning is a false positive — `/etc/subuid` is a Linux concept and does
not exist on macOS. Podman Desktop handles UID mapping inside its VM
automatically. The warning can be ignored; sandbox creation succeeds normally.

### `mapfile: command not found` during build

macOS ships with bash 3.2. The build script requires bash 4+:

```bash
brew install bash
ulimit -n 10240 && PATH="$(brew --prefix)/bin:$PATH" mise run build:docker:supervisor-sideload
```

### `ProcessFdQuotaExceeded` linker error

The linker exhausts the macOS default file descriptor limit during linking.
Raise it before building:

```bash
ulimit -n 10240
```

### GitHub API rate limit during `mise install`

Authenticate mise with your GitHub token:

```bash
export GITHUB_TOKEN=$(gh auth token)
mise install
```
