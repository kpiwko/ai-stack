# local-ai

Podman Compose stack for local AI tooling and MCP servers.

## Services

| Profile | Service | Port | Description |
|---|---|---|---|
| `ai-beacon` | ai-beacon | 17090 | Knowledge base / prompt library UI |
| `devlake-local-mysql-mcp` | devlake-local-mysql-mcp | 17301 | Read-only MCP proxy for local DevLake MySQL |
| `devlake-prod-mysql-mcp` | devlake-prod-mysql-mcp | 17300 | Read-only MCP proxy for remote Konflux RDS |
| `gmail-mcp` | gmail-mcp | 17633 | Gmail MCP server (search, draft, attachments) |
| `mcp-atlassian` | mcp-atlassian | 17000 | Jira MCP server (streamable HTTP transport) |
| `gdrive-mcp` | gdrive-mcp | 17100 | Google Drive MCP server (streamable HTTP transport) |

## One-time setup

**1. Environment file**

```bash
cp env.example .env
# Edit .env and fill in secrets
```

**2. Build the Gmail MCP image**

```bash
podman build -t localhost/gmail-mcp-server gmail-mcp-server/
```

**3. Build the MySQL MCP image** (used by both `devlake-local-mysql-mcp` and `devlake-prod-mysql-mcp`)

```bash
podman build -t localhost/mcp-mysql mcp-mysql/
```

## Usage

```shell
podman compose up -d            # start everything
podman compose stop <name>      # stop one service
podman compose up -d <name>     # start one service
podman compose down             # stop all (volumes are preserved)
```

## gmail-mcp

The container bind-mounts `~/.config/gmail-mcp-server/` directly, so any
token cached there from a previous run is picked up automatically on start.

If no token exists yet, open the auth page after starting:

```shell
open http://localhost:17633/auth   # step through Google Device Authorization
```

The `/auth` page shows a Google link and a short code. After you authorize,
the token is saved to `~/.config/gmail-mcp-server/token.json` and reused on
every subsequent start — no volume management needed.

Register with Claude Code (once, after authorizing):

```shell
claude mcp add --transport http --scope user gmail http://localhost:17633/mcp
```

## devlake-local-mysql-mcp

This profile connects to a DevLake MySQL instance running on the host at port
3306. Start DevLake first from its own repo:

```bash
cd ~/devel/work/devlake
podman compose -f docker-compose-dev.yml up -d mysql
```

Then start the MCP proxy:

```bash
podman compose --profile devlake-local-mysql-mcp up -d
```

## Registering MCP servers with Claude Code

The MySQL MCPs contain secrets and are registered as **project-local** (`--scope local`), which
writes to `.claude/settings.local.json` (gitignored). Run from within each project directory that
needs database access:

```bash
source ~/devel/local-ai/.env

claude mcp add --transport http --scope local devlake-prod-mysql-mcp \
  http://localhost:17300/mcp \
  --header "Authorization: Bearer ${KONFLUX_MCP_SECRET_KEY}"

claude mcp add --transport http --scope local devlake-local-mysql-mcp \
  http://localhost:17301/mcp \
  --header "Authorization: Bearer ${DEVLAKE_MCP_SECRET_KEY}"
```

Verify a server is responding before registering:

```bash
curl -s -X POST http://localhost:17300/mcp \
  -H "Authorization: Bearer ${KONFLUX_MCP_SECRET_KEY}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

## mcp-atlassian (Jira)

Runs as a persistent HTTP service. Start it with:

```shell
podman compose --profile mcp-atlassian up -d
```

Register with Claude Code once (the server must be running):

```shell
claude mcp add --transport http --scope user mcp-atlassian http://localhost:17000/mcp
```

Credentials are passed to the container via `.env` (`JIRA_URL`, `JIRA_USERNAME`,
`JIRA_API_TOKEN`). The MCP endpoint is `http://localhost:17000/mcp`.

## gdrive-mcp (Google Drive)

Authentication must happen on the host before starting the container — the
server cannot open a browser inside the container:

```shell
npx @piotr-agier/google-drive-mcp auth
```

This writes `credentials.json` and `tokens.json` into
`~/.config/google-drive-mcp/`, which the container bind-mounts read-only
(credentials) and read-write (tokens, for automatic refresh).

Start the service:

```shell
podman compose --profile gdrive-mcp up -d
```

Register with Claude Code:

```shell
claude mcp add --transport http --scope user gdrive http://localhost:17100/mcp
```

## Using with OpenShell sandboxes

`openshell-policy.yaml` grants sandbox access to all services in this stack.
All services are reached via `host.openshell.internal`, which OpenShell injects
as an alias for the gateway host IP. Because that resolves to a private RFC 1918
address, each endpoint in the policy explicitly allowlists private IP ranges to
override the built-in SSRF guard.

### Podman: rootful mode required

OpenShell's gateway runs k3s (lightweight Kubernetes) inside a container.
k3s's kubelet requires access to kernel interfaces (`/dev/kmsg`, OOM tuning,
network namespaces) that are not available in rootless Podman. See
[OpenShell issue #882](https://github.com/NVIDIA/OpenShell/issues/882).

Switch the Podman machine to rootful mode **once**:

```shell
podman machine stop
podman machine set --rootful
podman machine start
```

After switching, re-pull images for any running services (rootful and rootless
use separate image stores):

```shell
podman compose pull
```

### Gateway port

OpenShell's gateway defaults to host port 8080, which conflicts with several
services in this stack. Start it on a free port instead:

```shell
openshell gateway start --port 17711
```

Subsequent `openshell sandbox create` calls will reuse the already-running
gateway, so `--port` only needs to be set when (re)starting the gateway.

### Launching a sandbox

Start the profiles you need, then launch a sandbox with the policy:

```shell
podman compose --profile gmail-mcp --profile devlake-local-mysql-mcp up -d
openshell sandbox create --policy ./openshell-policy.yaml -- claude
```

From inside the sandbox, services are reachable at:

| Service | URL |
|---|---|
| ai-beacon | `http://host.openshell.internal:17090` |
| devlake-local-mysql-mcp | `http://host.openshell.internal:17301/mcp` |
| devlake-prod-mysql-mcp | `http://host.openshell.internal:17300/mcp` |
| gmail-mcp | `http://host.openshell.internal:17633/mcp` |
| mcp-atlassian | `http://host.openshell.internal:17000/mcp` |
| gdrive-mcp | `http://host.openshell.internal:17100/mcp` |

The policy uses `enforcement: audit` on all endpoints — violations are logged but
not blocked. Switch to `enforce` once you have confirmed traffic patterns are as
expected.

## macOS notes

- Named volumes are managed inside the podman VM — data persists across restarts.
- `host.containers.internal` resolves to the macOS host from inside containers
  (used by `devlake-mcp` to reach the host-published MySQL port).
- `network_mode: host` is not supported; all services use bridge networking.
