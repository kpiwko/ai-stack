# ai-stack

Personal AI tooling stack: Podman Compose services for MCP servers, plus Claude Code plugins for productivity workflows.

## Services

| Service | Port | Description |
|---|---|---|
| devlake-local-mysql-mcp | 17301 | Read-only MCP proxy for local DevLake MySQL |
| devlake-prod-mysql-mcp | 17300 | Read-only MCP proxy for remote Konflux RDS |
| notebooklm-mcp | 17200 | NotebookLM MCP server |
| workspace-mcp | 17150 | Google Workspace MCP (Gmail, Drive, Calendar, Docs, Sheets) |

## Getting started with Claude Code

**1. Register the marketplace and install the ai-stack plugin:**

```
claude plugin marketplace add https://github.com/kpiwko/ai-stack.git --scope user
claude plugin install ai-stack@ai-stack
```

**2. Copy and fill in secrets, then run bootstrap inside a Claude session:**

```bash
cp env.example .env
# Edit .env — fill in GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET, etc.
```

```
/ai-stack:bootstrap
```

Bootstrap starts the compose stack, installs runtimes (uv, pnpm, rustup), LSP plugins
(gopls, pyright, typescript-lsp, rust-analyzer), Claude plugins (superpowers, context7,
atlassian, dev, track, quarterly), and registers MCP servers with Claude Code.

**Updating plugins:**

```bash
claude plugin marketplace update ai-stack
claude plugin update ai-stack@ai-stack
```

Restart Claude Code after updating for changes to take effect.

## Just recipes

```bash
just lince-bootstrap             # install or update LINCE toolkit (agent-sandbox, lince-dashboard)
just lince                       # launch the LINCE dashboard

just openshell-bootstrap         # build OpenShell gateway + sideload image, start gateway, register provider
just openshell-bootstrap rebuild # force rebuild even if binaries/image already exist
just openshell                   # generate Vertex AI wrapper and launch Claude Code in a sandbox
just openshell-teardown          # delete sandboxes, stop gateway, clean up staging files
```

Stack lifecycle (`up`, `down`, `status`) is handled by the `/ai-stack:up` and `/ai-stack:down` Claude skills.

## devlake-local-mysql-mcp

Connects to a DevLake MySQL instance running on the host at port 3306. Start DevLake's
MySQL service first, then register this MCP via `/ai-stack:bootstrap`. The command
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

## notebooklm-mcp

On first run (or when cookies expire), authenticate via the bundled VNC browser:

```bash
open http://localhost:17201/vnc.html
podman exec -it ai-stack-notebooklm-mcp-1 nlm login
```

## workspace-mcp

On first run, make any Google Workspace tool call — the server returns a clickable OAuth
URL. Complete the Google OAuth flow in your browser. Credentials are stored in
`~/.config/workspace-mcp/` and reused on subsequent runs.

## Agent sandboxes (experimental)

Running AI coding agents in isolated sandboxes is an active area. Two separate experimental
approaches are available here; neither is production-ready. See also
[OpenKaiden](https://openkaiden.ai/) — a desktop application that runs AI coding agents in
isolated sandboxes with enterprise governance controls.

### LINCE (Zellij dashboard + bwrap/nono sandbox)

> **Experimental.** LINCE is a standalone toolkit and is not yet integrated with OpenShell.
> It uses `bubblewrap` (Linux) or `nono` (macOS) for filesystem/process isolation and
> Zellij for multi-agent session management.

Install or update via just:

```bash
just lince-bootstrap
```

This runs the interactive quickstart installer from the local `lince/` checkout, installing
`agent-sandbox`, the `lince-dashboard` Zellij plugin, and supporting scripts. Launch the
dashboard with `just lince`.

### OpenShell (Podman + network policy enforcement)

> **Experimental.** Running Claude Code in an OpenShell sandbox with Vertex AI currently
> requires a manual credential wrapper. This is a workaround until OpenShell adds native
> Vertex AI support (tracked in NVIDIA/OpenShell issue #472). Once that lands, the workflow
> simplifies to `openshell sandbox create -- claude` with a configured provider.

Set up via `just` goals (not the plugin — OpenShell setup requires build tools and a running
gateway, which the plugin cannot manage):

```bash
# One-time setup (or after OpenShell git pull):
just openshell-bootstrap

# Each session:
just openshell

# Tear everything down:
just openshell-teardown
```

`openshell/policy.yaml` grants sandbox network access to all MCP services in this stack.
Local services are reached via `host.containers.internal` (injected by the Podman driver).

Gateway logs go to `/tmp/openshell-gateway.log`. See `openshell/bootstrap.md` for full
setup instructions and known issues.

## macOS notes

- Named volumes are managed inside the Podman VM — data persists across restarts.
- `host.containers.internal` resolves to the macOS host from inside containers.
- `network_mode: host` is not supported; all services use bridge networking.

## License

MIT — see [LICENSE](LICENSE).
