# Google Workspace MCP Container Design

## Goal

Replace the existing `gmail-mcp` and `gdrive-mcp` containers with a single `workspace-mcp` container that runs [`workspace-mcp`](https://workspacemcp.com) (taylorwilsdon/google_workspace_mcp) as an HTTP MCP server, covering Gmail, Drive, Calendar, Docs, Sheets, Slides, Forms, and Apps Script.

## Architecture

Single-stage UBI9 Python 3.12 container. Installs `uv` via pip, then runs `uvx workspace-mcp --transport streamable-http` at startup. No virtual display stack — OAuth auth uses a standard browser redirect to a localhost callback URL handled by the server itself.

**New repo:** `kpiwko/workspace-mcp`
**Published image:** `ghcr.io/kpiwko/workspace-mcp:latest`
**Host port:** 17150 → container port 8000
**MCP endpoint:** `http://localhost:17150/mcp`

## Container design

```
FROM registry.redhat.io/ubi9/python-312:latest

RUN pip install --upgrade pip uv

ENV HOME=/root \
    WORKSPACE_MCP_CREDENTIALS_DIR=/root/.config/workspace-mcp \
    WORKSPACE_MCP_TOOLS="gmail drive calendar docs sheets slides forms script" \
    WORKSPACE_MCP_PORT=8000 \
    WORKSPACE_MCP_HOST=0.0.0.0 \
    PATH="/root/.local/bin:$PATH"

VOLUME ["/root/.config/workspace-mcp"]
EXPOSE 8000

CMD ["sh", "-c", "uvx workspace-mcp --transport streamable-http --tools ${WORKSPACE_MCP_TOOLS}"]
```

`GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` are injected at runtime via `compose.yaml` (from `.env`) — not baked into the image.

`WORKSPACE_MCP_TOOLS` defaults to the full set but can be overridden in `compose.yaml` without rebuilding. Note: Google Apps Script maps to the tool name `script` in workspace-mcp (not `apps_script`).

## Google Cloud setup (one-time)

These steps are included in the implementation plan and README.

1. Open [Google Cloud Console](https://console.cloud.google.com/) and select your existing project.
2. Go to **APIs & Services → Library** and enable:
   - Gmail API
   - Google Drive API
   - Google Calendar API
   - Google Docs API
   - Google Sheets API
   - Google Slides API
   - Google Forms API
   - Apps Script API
3. Go to **APIs & Services → Credentials → Create Credentials → OAuth Client ID**.
4. Application type: **Web application**.
5. Add authorized redirect URI: `http://localhost:17150/oauth2callback`
6. Copy the **Client ID** and **Client Secret** into your `.env`:
   ```
   GOOGLE_OAUTH_CLIENT_ID=<client-id>
   GOOGLE_OAUTH_CLIENT_SECRET=<client-secret>
   ```

## Auth flow

First run (no token yet):

```bash
# Container is running with credentials env vars set
open http://localhost:17150/         # opens OAuth consent in host browser
# Authorize → Google redirects to localhost:17150/oauth2callback
# Token saved to ~/.config/workspace-mcp (mounted volume)
```

Subsequent runs reuse the stored refresh token automatically. No manual re-auth needed until revoked.

## CI/CD

Multi-arch build following the notebooklm-mcp pattern:

- Matrix: `ubuntu-24.04` (amd64) + `ubuntu-24.04-arm` (arm64) native runners
- Build with `redhat-actions/buildah-build@v2`, push per-arch image tagged `<sha>-<arch>`
- Combine with `docker buildx imagetools create` into a multi-arch manifest
- Tags: `latest` (main branch), `v*` (tags), `<sha>`
- Required secrets: `RH_REGISTRY_USER`, `RH_REGISTRY_TOKEN` (registry.redhat.io pull), `GITHUB_TOKEN` (ghcr.io push)

## Migration

### Stopping old services

```bash
podman compose stop gmail-mcp gdrive-mcp
podman compose rm -f gmail-mcp gdrive-mcp
```

### compose.yaml changes

Remove `gmail-mcp` (port 17633) and `gdrive-mcp` (port 17100) service blocks.

Add:

```yaml
workspace-mcp:
  image: ghcr.io/kpiwko/workspace-mcp:latest
  networks: [ai-stack]
  ports:
    - "17150:8000"
  volumes:
    - /Users/kpiwko/.config/workspace-mcp:/root/.config/workspace-mcp
  environment:
    GOOGLE_OAUTH_CLIENT_ID: ${GOOGLE_OAUTH_CLIENT_ID}
    GOOGLE_OAUTH_CLIENT_SECRET: ${GOOGLE_OAUTH_CLIENT_SECRET}
  restart: unless-stopped
```

### mcps.yaml changes

Remove `gmail` and `gdrive` entries. Add:

```yaml
- name: workspace-mcp
  transport: http
  url: http://localhost:17150/mcp
  scope: user
```

### Claude MCP registration

```bash
claude mcp remove gmail
claude mcp remove gdrive
claude mcp add --transport http --scope user workspace-mcp http://localhost:17150/mcp
```

### Plugin version

Bump `plugins/ai-stack/.claude-plugin/plugin.json`: `0.6.3` → `0.7.0` (minor bump — MCP entries added and removed).

## File map

### New repo: `kpiwko/workspace-mcp`

| File | Purpose |
|------|---------|
| `Containerfile` | UBI9 Python 3.12 image with uv + workspace-mcp |
| `scripts/entrypoint.sh` | Starts uvx workspace-mcp with configured tools |
| `.github/workflows/build.yaml` | Multi-arch build and push to ghcr.io |
| `README.md` | Google Cloud setup, auth flow, compose snippet |

### Existing repo: `ai-stack`

| File | Change |
|------|--------|
| `compose.yaml` | Remove gmail-mcp + gdrive-mcp, add workspace-mcp |
| `plugins/ai-stack/reference/mcps.yaml` | Remove gmail + gdrive, add workspace-mcp |
| `plugins/ai-stack/.claude-plugin/plugin.json` | Bump version 0.6.3 → 0.7.0 |
