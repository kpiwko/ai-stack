# ai-stack

Personal AI tooling stack: Podman Compose services for MCP servers, plus Claude Code plugins for productivity workflows.

## Services

| Service | Port | Description |
|---|---|---|
| ai-beacon | 17090 | Knowledge base / prompt library UI |
| devlake-local-mysql-mcp | 17301 | Read-only MCP proxy for local DevLake MySQL |
| devlake-prod-mysql-mcp | 17300 | Read-only MCP proxy for remote Konflux RDS |
| gmail-mcp | 17633 | Gmail MCP server (search, draft, attachments) |
| mcp-atlassian | 17000 | Jira MCP server (streamable HTTP transport) |
| gdrive-mcp | 17100 | Google Drive MCP server (streamable HTTP transport) |

## Quick start

**1. Copy and fill in secrets**

```bash
cp env.example .env
# Edit .env
```

**2. Start services**

```bash
just up
# or selectively:
podman compose up -d gmail-mcp mcp-atlassian
```

Container images are built by CI and published to `ghcr.io/kpiwko/` — no local build needed.

## Plugins

Claude Code plugins live in `plugins/`. Install them once inside Claude Code:

```
/plugin install dev@kpiwko/ai-stack
/plugin install track@kpiwko/ai-stack
/plugin install quarterly@kpiwko/ai-stack
```

Third-party plugins and bare skills are tracked in `plugins.yaml`. See `just install-plugins` and `just install-skills`.

## Just recipes

```bash
just install-plugins   # print /plugin install commands for Claude Code
just install-skills    # fetch and install bare skills from plugins.yaml (requires: yq, git)
just check-images      # verify compose.yaml uses no localhost/ images
just up                # podman compose up -d
just down              # podman compose down
just status            # podman compose ps
```

## gmail-mcp

The container bind-mounts `~/.config/gmail-mcp-server/` so tokens from a previous run are
reused automatically. On first run, authorize via browser:

```bash
open http://localhost:17633/auth   # complete Google Device Authorization
```

Register with Claude Code once:

```bash
claude mcp add --transport http --scope user gmail http://localhost:17633/mcp
```

## devlake-local-mysql-mcp

Connects to a DevLake MySQL instance running on the host at port 3306. Start DevLake first:

```bash
cd ~/devel/work/devlake
podman compose -f docker-compose-dev.yml up -d mysql
```

Then start the MCP proxy:

```bash
podman compose up -d devlake-local-mysql-mcp
```

## Registering MCP servers with Claude Code

MySQL MCPs carry secrets and are registered **project-local** (`--scope local`), which writes
to `.claude/settings.local.json` (gitignored). Run from the project that needs DB access:

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

```bash
podman compose up -d mcp-atlassian
claude mcp add --transport http --scope user mcp-atlassian http://localhost:17000/mcp
```

Credentials come from `.env`: `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN`.

## gdrive-mcp (Google Drive)

Authenticate on the host before starting the container — the server cannot open a browser
inside the container:

```bash
npx @piotr-agier/google-drive-mcp auth
```

This writes `credentials.json` and `tokens.json` into `~/.config/google-drive-mcp/`.

```bash
podman compose up -d gdrive-mcp
claude mcp add --transport http --scope user gdrive http://localhost:17100/mcp
```

## OpenShell sandboxes

`openshell/policy.yaml` grants sandbox access to all services in this stack.
Services are reached via `host.openshell.internal` (OpenShell injects this as an alias
for the gateway host IP). Private IP ranges are explicitly allowlisted to override the
built-in SSRF guard.

### Rootful Podman required

OpenShell's gateway runs k3s inside a container. k3s requires kernel interfaces
(`/dev/kmsg`, OOM tuning, network namespaces) unavailable in rootless Podman.

Switch once:

```bash
podman machine stop
podman machine set --rootful
podman machine start
podman compose pull   # re-pull images (rootful/rootless use separate stores)
```

### Gateway port

OpenShell's gateway defaults to port 8080, which conflicts with services here.
Start it on a free port:

```bash
openshell gateway start --port 17711
```

### Launching a sandbox

```bash
podman compose up -d gmail-mcp devlake-local-mysql-mcp
openshell sandbox create --policy ./openshell/policy.yaml -- claude
```

From inside the sandbox, services are reachable at `host.openshell.internal:<port>`.

## macOS notes

- Named volumes are managed inside the Podman VM — data persists across restarts.
- `host.containers.internal` resolves to the macOS host from inside containers.
- `network_mode: host` is not supported; all services use bridge networking.

## License

MIT — see [LICENSE](LICENSE).
