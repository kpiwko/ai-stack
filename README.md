# ai-stack

Personal AI tooling stack: Podman Compose services for MCP servers, plus Claude Code plugins for productivity workflows.

## Services

| Service | Port | Description |
|---|---|---|
| ai-beacon | 17090 | Session manager for multiple Claude sessions |
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

## Getting started with Claude Code

**1. Register the marketplace and install the ai-stack plugin:**

```
claude plugin marketplace add https://github.com/kpiwko/ai-stack.git --scope user
claude plugin install ai-stack@ai-stack
```

**2. Use it inside a Claude session to set up everything else:**

```
/ai-stack:install-plugins   ← install dev, track, quarterly plugins
/ai-stack:install-skills    ← install bare skills (template-slide-deck, n8n-skills)
/ai-stack:install-mcps      ← register MCP servers with Claude Code
```

All three commands are interactive: they show what's available, what's already installed,
and let you pick scope (user / project / local) before making any changes.

**3. Install LSP servers and language runtimes:**

```
/ai-stack:bootstrap
```

Sets up Go, Python (pyright), TypeScript, and Rust language servers for code intelligence
in Claude Code.

**Updating plugins:**

```bash
claude plugin marketplace update ai-stack
claude plugin update ai-stack@ai-stack
```

Restart Claude Code after updating for changes to take effect.

**Updating plugins inside the agent-sandbox (LINCE):**

The sandbox uses an isolated Claude config at `~/.agent-sandbox/claude-config/`.
Target it explicitly with `CLAUDE_CONFIG_DIR`:

```bash
CLAUDE_CONFIG_DIR=~/.agent-sandbox/claude-config claude plugin marketplace update ai-stack
CLAUDE_CONFIG_DIR=~/.agent-sandbox/claude-config claude plugin update ai-stack@ai-stack
```

## Just recipes

```bash
just up       # podman compose up -d
just down     # podman compose down
just status   # podman compose ps
```

## gmail-mcp

The container bind-mounts `~/.config/gmail-mcp-server/` so tokens from a previous run are
reused automatically. On first run, authorize via browser:

```bash
open http://localhost:17633/auth   # complete Google Device Authorization
```

Then register with Claude Code via `/ai-stack:install-mcps`.

## devlake-local-mysql-mcp

Connects to a DevLake MySQL instance running on the host at port 3306. Start DevLake's
MySQL service first, then register this MCP via `/ai-stack:install-mcps`. The command
reads `$DEVLAKE_MCP_SECRET_KEY` from the environment — make sure `.env` is sourced first.

**Optional: connect via shared Podman network instead of host port**

If DevLake runs in Podman Compose with a named network, you can attach this service to
that network and reach MySQL by container name — no host port exposure needed.

1. Find DevLake's network name: `podman network ls`

2. Declare it as external in `compose.yaml`:
   ```yaml
   networks:
     ai-stack:
       driver: bridge
     devprod:        # replace with DevLake's actual network name
       external: true
   ```

3. Add the network to the service and update `MYSQL_HOST` to the MySQL container name:
   ```yaml
   devlake-local-mysql-mcp:
     networks: [ai-stack, devprod]
     environment:
       MYSQL_HOST: mysql   # replace with DevLake's MySQL container name
   ```

## mcp-atlassian (Jira)

Credentials come from `.env`: `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN`. Start the
service then register via `/ai-stack:install-mcps`.

## gdrive-mcp (Google Drive)

Authenticate on the host before starting the container — the server cannot open a browser
inside the container:

```bash
npx @piotr-agier/google-drive-mcp auth
```

This writes `credentials.json` and `tokens.json` into `~/.config/google-drive-mcp/`.
Then start the service and register via `/ai-stack:install-mcps`.

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
