# ai-stack

Personal AI tooling stack: MCP servers for data access and productivity, plus Claude Code plugins for developer workflows.

## What's Included

### MCP Servers

| Name | Scope | Description |
|---|---|---|
| devlake-mysql-local | project | Read-only SQL access to local DevLake MySQL |
| devlake-mysql-staging | project | Read-only SQL access to Konflux staging RDS |
| devlake-mysql-prod | project | Read-only SQL access to Konflux prod RDS |
| notebooklm | user | NotebookLM (notebooklm.google.com) |
| workspace-mcp | user | Google Workspace — Gmail, Drive, Calendar, Docs, Sheets, Slides, Forms |

**User-scoped** MCPs are registered once globally via `/ai-stack:bootstrap`.
**Project-scoped** MCPs are registered per-project via `/ai-stack:project-init`.

### Plugins

| Plugin | Description |
|---|---|
| ai-stack | Stack lifecycle: bootstrap, up/down/status, project-init, modify |
| dev | Developer workflows: code review (CodeRabbit), git workflow with PR gates, language coding agents |
| track | Track decisions and work in external systems: Jira, Google Docs, Google Drive |
| quarterly | Quarterly review: gather activity data from Gmail, Jira, and Drive; generate structured reflection |

### Skills

| Skill | Description |
|---|---|
| `/ai-stack:bootstrap` | Full machine setup — runtimes, LSP plugins, Claude plugins, MCP servers |
| `/ai-stack:up` | Start the container stack (idempotent) |
| `/ai-stack:down` | Stop the container stack |
| `/ai-stack:status` | Show service health and endpoints |
| `/ai-stack:project-init` | Initialise a project directory (CLAUDE.md, AGENTS.md, project MCPs) |
| `/ai-stack:modify` | Add, update, or remove a plugin/skill/MCP in the registry |
| `/dev:git-workflow` | Branch lifecycle and PR/MR creation with approval gates (GitHub + GitLab) |
| `/dev:review-cr` | Run CodeRabbit CLI review on committed changes |
| `/track:jira` | Create or update a Jira issue |
| `/track:gdrive-doc` | Create or update a Google Doc in the right Drive location |
| `/track:gdrive-organize` | Reorganize a Google Drive based on a structure document |
| `/quarterly:prep` | Gather activity data from Gmail, Jira, and Drive for a quarter |
| `/quarterly:connect` | Guide a structured quarterly reflection |

## Installation

**1. Register the marketplace and install plugins:**

```bash
claude plugin marketplace add https://github.com/kpiwko/ai-stack.git --scope user
claude plugin install ai-stack@ai-stack
```

**2. Run bootstrap inside a Claude session:**

```
/ai-stack:bootstrap
```

Bootstrap installs runtimes (uv, pnpm, rustup), LSP plugins (gopls, pyright,
typescript-lsp, rust-analyzer), Claude plugins (superpowers, context7, atlassian,
dev, track, quarterly), and registers user-scoped MCP servers.

**3. Edit `.env` with your secrets:**

Bootstrap creates `.env` from a template if missing. Fill in placeholder values —
Google OAuth credentials, database passwords, MCP secret keys. The template lists
every variable with comments.

**4. Start the services:**

```
/ai-stack:up
```

## Per-Project Setup

Run `/ai-stack:project-init` inside any project directory. It will:

- Copy `CLAUDE.md` and `AGENTS.md` templates (skips if already present)
- Offer to register project-scoped MCP servers (devlake-mysql-*)
- Ensure `.mcp.json` is in `.gitignore` (it contains expanded bearer tokens)

## MCP Authentication

### NotebookLM

On first run (or when cookies expire), authenticate via the bundled VNC browser:

```bash
open http://localhost:17201/vnc.html
podman exec -it ai-stack-notebooklm-mcp-1 nlm login
```

### workspace-mcp

On first run, make any Google Workspace tool call — the server returns a clickable
OAuth URL. Complete the Google OAuth flow in your browser. Credentials are stored in
`~/.config/workspace-mcp/` and reused on subsequent runs.

## DevLake Local Setup

Connects to a DevLake MySQL instance running on the host at port 3306. Start DevLake's
MySQL service first, then register this MCP via `/ai-stack:project-init`.

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
   devlake-mysql-local:
     networks: [ai-stack, devprod]
     environment:
       MYSQL_HOST: mysql   # replace with DevLake's MySQL container name
   ```

## Updating

```bash
claude plugin marketplace update ai-stack
claude plugin update ai-stack@ai-stack
```

Restart Claude Code after updating for changes to take effect.

## macOS Notes

- Named volumes are managed inside the Podman VM — data persists across restarts.
- `host.containers.internal` resolves to the macOS host from inside containers.
- `network_mode: host` is not supported; all services use bridge networking.

## License

MIT — see [LICENSE](LICENSE).
