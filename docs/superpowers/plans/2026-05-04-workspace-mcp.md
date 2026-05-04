# Google Workspace MCP Container Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and publish a UBI9-based container image that runs `workspace-mcp` as an HTTP MCP server covering Gmail, Drive, Calendar, Docs, Sheets, Slides, Forms, and Apps Script — replacing the existing `gmail-mcp` and `gdrive-mcp` containers.

**Architecture:** Single-stage `registry.access.redhat.com/ubi9/python-312` container (public, no registry auth needed). Installs `uv` via pip, then installs `workspace-mcp` as a uv tool. An entrypoint script launches the server with the configured tool set. OAuth tokens persist in a bind-mounted volume. No virtual display stack — auth is a standard browser redirect to `localhost:17150/oauth2callback`.

**Tech Stack:** `registry.access.redhat.com/ubi9/python-312`, `uv`, `workspace-mcp` (PyPI), `redhat-actions/buildah-build@v2`, GitHub Actions, ghcr.io.

---

## File Map

### New repo: `kpiwko/workspace-mcp`

| File | Purpose |
|------|---------|
| `Containerfile` | UBI9 image — installs uv + workspace-mcp |
| `scripts/entrypoint.sh` | Starts workspace-mcp with `WORKSPACE_MCP_TOOLS` |
| `.github/workflows/build.yaml` | Multi-arch build (amd64 + arm64) → ghcr.io |
| `README.md` | Google Cloud setup, auth flow, compose snippet |

### Existing repo: `ai-stack`

| File | Change |
|------|--------|
| `compose.yaml` | Remove `gmail-mcp` + `gdrive-mcp`, add `workspace-mcp` |
| `plugins/ai-stack/reference/mcps.yaml` | Remove `gmail` + `gdrive`, add `workspace-mcp` |
| `plugins/ai-stack/.claude-plugin/plugin.json` | Bump `0.6.3` → `0.7.0` |

---

## Task 1: Create repo, Containerfile, and entrypoint

**Files:**
- Create: GitHub repo `kpiwko/workspace-mcp`
- Create: `Containerfile`
- Create: `scripts/entrypoint.sh`
- Create: `.gitignore`

- [ ] **Step 1: Create the GitHub repo and clone it**

```bash
gh repo create kpiwko/workspace-mcp --public \
  --description "Google Workspace MCP server container"
gh repo clone kpiwko/workspace-mcp
cd workspace-mcp
```

- [ ] **Step 2: Write `.gitignore`**

```
__pycache__/
*.pyc
.env
```

- [ ] **Step 3: Write `scripts/entrypoint.sh`**

```bash
mkdir -p scripts
cat > scripts/entrypoint.sh << 'EOF'
#!/bin/sh
set -e
exec workspace-mcp --transport streamable-http --tools ${WORKSPACE_MCP_TOOLS}
EOF
chmod +x scripts/entrypoint.sh
```

- [ ] **Step 4: Write `Containerfile`**

```dockerfile
FROM registry.access.redhat.com/ubi9/python-312:latest

LABEL name="workspace-mcp" \
      summary="Google Workspace MCP Server" \
      description="MCP server providing Google Workspace access via workspace-mcp (Gmail, Drive, Calendar, Docs, Sheets, Slides, Forms, Apps Script)" \
      maintainer="kpiwko@redhat.com"

USER root

# HOME override: UBI9 python-312 sets HOME=/opt/app-root/src by default;
# uv installs tools to $HOME/.local/bin, so this must point to /root.
ENV HOME=/root

RUN pip install --upgrade pip uv \
    && uv tool install --python python3.12 workspace-mcp

ENV PATH="/root/.local/bin:$PATH" \
    WORKSPACE_MCP_CREDENTIALS_DIR=/root/.config/workspace-mcp \
    WORKSPACE_MCP_TOOLS="gmail drive calendar docs sheets slides forms script" \
    WORKSPACE_MCP_PORT=8000 \
    WORKSPACE_MCP_HOST=0.0.0.0

VOLUME ["/root/.config/workspace-mcp"]

EXPOSE 8000

COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
```

Note: `registry.access.redhat.com` is the public UBI registry — no auth required. `script` is the workspace-mcp tool name for Google Apps Script (not `apps_script`).

- [ ] **Step 5: Build locally**

```bash
podman build -t localhost/workspace-mcp:dev .
```

Expected: image builds successfully. Final size ~1–2 GB (Python + workspace-mcp dependencies).

If `uv tool install workspace-mcp` fails, check the package name with:
```bash
podman run --rm registry.access.redhat.com/ubi9/python-312:latest \
  bash -c "pip install uv && uv tool install workspace-mcp && workspace-mcp --version"
```

- [ ] **Step 6: Verify the binary is on PATH inside the image**

```bash
podman run --rm localhost/workspace-mcp:dev workspace-mcp --version
```

Expected: prints the workspace-mcp version (e.g. `workspace-mcp 0.x.y`). If `command not found`, check that `PATH` includes `/root/.local/bin` and `HOME` is set to `/root`.

- [ ] **Step 7: Verify the server starts**

```bash
podman run --rm -d --name ws-test \
  -p 17150:8000 \
  -e GOOGLE_OAUTH_CLIENT_ID=placeholder \
  -e GOOGLE_OAUTH_CLIENT_SECRET=placeholder \
  localhost/workspace-mcp:dev
sleep 5
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:17150/
podman stop ws-test
```

Expected: HTTP status `200` or `401` (not connection refused). Any HTTP response confirms the server started. A `401` or redirect to Google login is normal with placeholder credentials.

- [ ] **Step 8: Commit**

```bash
git add Containerfile scripts/entrypoint.sh .gitignore
git commit -m "feat: add Containerfile and entrypoint for workspace-mcp"
```

---

## Task 2: CI/CD workflow

**Files:**
- Create: `.github/workflows/build.yaml`

- [ ] **Step 1: Write the workflow**

```bash
mkdir -p .github/workflows
cat > .github/workflows/build.yaml << 'EOF'
name: Build and push

on:
  push:
    branches: [main]
    tags: ['v*']

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  build:
    runs-on: ${{ matrix.runner }}
    strategy:
      matrix:
        include:
          - arch: amd64
            runner: ubuntu-24.04
          - arch: arm64
            runner: ubuntu-24.04-arm
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Build image
        id: build
        uses: redhat-actions/buildah-build@v2
        with:
          image: workspace-mcp
          tags: ${{ github.sha }}-${{ matrix.arch }}
          containerfiles: ./Containerfile
          platforms: linux/${{ matrix.arch }}

      - name: Push per-arch image
        uses: redhat-actions/push-to-registry@v2
        with:
          image: ${{ steps.build.outputs.image }}
          tags: ${{ steps.build.outputs.tags }}
          registry: ghcr.io/${{ github.repository_owner }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

  manifest:
    needs: build
    runs-on: ubuntu-24.04
    permissions:
      packages: write

    steps:
      - name: Log in to ghcr.io
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Docker meta
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository_owner }}/workspace-mcp
          tags: |
            type=raw,value=latest,enable={{is_default_branch}}
            type=ref,event=tag
            type=sha,prefix=

      - name: Create and push multi-arch manifest
        run: |
          IMAGE="ghcr.io/${{ github.repository_owner }}/workspace-mcp"
          while IFS= read -r tag; do
            docker buildx imagetools create \
              -t "$tag" \
              "${IMAGE}:${{ github.sha }}-amd64" \
              "${IMAGE}:${{ github.sha }}-arm64"
          done <<< "${{ steps.meta.outputs.tags }}"
EOF
```

Note: No `registry.redhat.io` login step needed — `registry.access.redhat.com` (used in the FROM line) is public and requires no auth. This simplifies CI compared to notebooklm-mcp.

- [ ] **Step 2: Commit and push to trigger CI**

```bash
git add .github/workflows/build.yaml
git commit -m "ci: add multi-arch build and push workflow"
git push origin main
```

- [ ] **Step 3: Monitor the workflow**

```bash
gh run list --limit 5
gh run watch
```

Expected: both `amd64` and `arm64` build jobs succeed, then the `manifest` job combines them. Total runtime ~5–8 minutes.

- [ ] **Step 4: Make the package public if needed**

```bash
gh api \
  -X PATCH \
  /user/packages/container/workspace-mcp \
  -f visibility=public
```

If that fails (package not yet created), go to `https://github.com/users/kpiwko/packages/container/workspace-mcp/settings` → Change visibility → Public after the first successful push.

- [ ] **Step 5: Verify the image is pullable**

```bash
podman pull ghcr.io/kpiwko/workspace-mcp:latest
podman run --rm ghcr.io/kpiwko/workspace-mcp:latest workspace-mcp --version
```

Expected: pulls the multi-arch image and prints the workspace-mcp version.

---

## Task 3: Write README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write `README.md`**

```markdown
# workspace-mcp

Google Workspace MCP server container. Runs [`workspace-mcp`](https://workspacemcp.com)
as an HTTP MCP server covering Gmail, Drive, Calendar, Docs, Sheets, Slides, Forms,
and Apps Script (`script`).

## Ports

| Port | Purpose |
|------|---------|
| 17150 | MCP HTTP endpoint (`/mcp`) |

## Google Cloud setup (one-time)

You need a Google OAuth 2.0 **Web application** credential. If you have an existing
Google Cloud project (e.g. for gmail-mcp), you can reuse it — just enable the
additional APIs and create a new Web application credential.

### 1. Enable APIs

Go to [APIs & Services → Library](https://console.cloud.google.com/apis/library) and
enable each of the following:

- Gmail API
- Google Drive API
- Google Calendar API
- Google Docs API
- Google Sheets API
- Google Slides API
- Google Forms API
- Apps Script API

### 2. Create OAuth credentials

1. Go to **APIs & Services → Credentials → Create Credentials → OAuth Client ID**
2. If prompted, configure the OAuth consent screen:
   - User type: **External**
   - Fill in App name, support email, developer contact email
   - Add your own email under **Test users**
   - Add these scopes (or leave empty for now and add them after):
     - `https://mail.google.com/`
     - `https://www.googleapis.com/auth/drive`
     - `https://www.googleapis.com/auth/calendar`
     - `https://www.googleapis.com/auth/documents`
     - `https://www.googleapis.com/auth/spreadsheets`
     - `https://www.googleapis.com/auth/presentations`
     - `https://www.googleapis.com/auth/forms`
     - `https://www.googleapis.com/auth/script.projects`
3. Application type: **Web application**
4. Add authorized redirect URI: `http://localhost:17150/oauth2callback`
5. Click **Create** — copy the **Client ID** and **Client Secret**

### 3. Set credentials in your environment

Add to your `.env` file (used by `podman compose`):

```
GOOGLE_OAUTH_CLIENT_ID=<your-client-id>
GOOGLE_OAUTH_CLIENT_SECRET=<your-client-secret>
```

## First-run auth

```bash
# 1. Create the credentials directory
mkdir -p ~/.config/workspace-mcp

# 2. Start the container (credentials env vars must be set)
podman compose up -d workspace-mcp

# 3. Open the auth page in your browser
open http://localhost:17150/

# 4. Complete the Google OAuth flow in your browser
#    Google redirects to localhost:17150/oauth2callback automatically
#    Token is saved to ~/.config/workspace-mcp
```

Subsequent container restarts reuse the stored refresh token automatically.

## Token refresh

If you see authentication errors, repeat the auth flow:

```bash
open http://localhost:17150/
```

## MCP registration

```bash
claude mcp add --transport http --scope user workspace-mcp http://localhost:17150/mcp
```

## Configuring tools

The default tool set is `gmail drive calendar docs sheets slides forms script`.
Override via `WORKSPACE_MCP_TOOLS` in `compose.yaml`:

```yaml
environment:
  WORKSPACE_MCP_TOOLS: "gmail drive calendar"
```

`script` is the workspace-mcp tool name for Google Apps Script.

## ai-stack compose snippet

```yaml
##############################################################################
# workspace-mcp — Google Workspace MCP server, streamable HTTP transport
# Covers: Gmail, Drive, Calendar, Docs, Sheets, Slides, Forms, Apps Script
# MCP endpoint: http://localhost:17150/mcp
# Auth (first run): open http://localhost:17150/ in your browser
##############################################################################
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
```

- [ ] **Step 2: Commit and push**

```bash
git add README.md
git commit -m "docs: add README with Google Cloud setup and auth flow"
git push origin main
```

---

## Task 4: Update ai-stack repo

Work in the `ai-stack` repo for this task (`/Users/kpiwko/devel/ai-stack`).

**Files:**
- Modify: `compose.yaml`
- Modify: `plugins/ai-stack/reference/mcps.yaml`
- Modify: `plugins/ai-stack/.claude-plugin/plugin.json`

- [ ] **Step 1: Stop and remove old containers**

```bash
cd /Users/kpiwko/devel/ai-stack
podman compose stop gmail-mcp gdrive-mcp
podman compose rm -f gmail-mcp gdrive-mcp
```

Expected: both containers removed. If they're not running, the command still succeeds.

- [ ] **Step 2: Remove `gmail-mcp` service block from `compose.yaml`**

Remove the entire block (including the comment header):

```yaml
  ##############################################################################
  # Gmail MCP — MCP server providing Gmail access via Device Authorization flow
  # Image built by CI: ghcr.io/kpiwko/gmail-mcp-server:latest
  # Auth page  : http://localhost:17633/auth  (first run — authorizes via browser)
  # MCP endpoint: http://localhost:17633/mcp
  ##############################################################################
  gmail-mcp:
    image: ghcr.io/kpiwko/gmail-mcp-server:latest
    networks: [ai-stack]
    ports:
      - "17633:6633"
    volumes:
      - /Users/kpiwko/.config/gmail-mcp-server:/config/gmail-mcp-server
    environment:
      GMAIL_CLIENT_ID: ${GMAIL_CLIENT_ID}
      GMAIL_CLIENT_SECRET: ${GMAIL_CLIENT_SECRET}
      XDG_CONFIG_HOME: /config
    restart: unless-stopped
```

- [ ] **Step 3: Remove `gdrive-mcp` service block from `compose.yaml`**

Remove the entire block (including the comment header):

```yaml
  ##############################################################################
  # gdrive-mcp — Google Drive MCP server, streamable HTTP transport
  # Prereq: authenticate once outside the container first:
  #   npx @piotr-agier/google-drive-mcp auth
  # MCP endpoint: http://localhost:17100/mcp
  # Register: claude mcp add --transport http --scope user gdrive http://localhost:17100/mcp
  ##############################################################################
  gdrive-mcp:
    image: registry.access.redhat.com/ubi9/nodejs-22:latest
    networks: [ai-stack]
    ports:
      - "17100:3100"
    command: ["npx", "-y", "@piotr-agier/google-drive-mcp", "start"]
    volumes:
      - /Users/kpiwko/.config/google-drive-mcp/credentials.json:/config/credentials.json:ro
      - /Users/kpiwko/.config/google-drive-mcp/tokens.json:/config/tokens.json
    environment:
      GOOGLE_DRIVE_OAUTH_CREDENTIALS: /config/credentials.json
      GOOGLE_DRIVE_MCP_TOKEN_PATH: /config/tokens.json
      MCP_TRANSPORT: http
      MCP_HTTP_PORT: "3100"
      MCP_HTTP_HOST: "0.0.0.0"
    restart: unless-stopped
```

- [ ] **Step 4: Add `workspace-mcp` service block to `compose.yaml`**

Add after the `notebooklm-mcp` block:

```yaml
  ##############################################################################
  # workspace-mcp — Google Workspace MCP server, streamable HTTP transport
  # Covers: Gmail, Drive, Calendar, Docs, Sheets, Slides, Forms, Apps Script
  # MCP endpoint: http://localhost:17150/mcp
  # Auth (first run): open http://localhost:17150/ in your browser
  ##############################################################################
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

- [ ] **Step 5: Verify `compose.yaml` is valid**

```bash
podman compose config --quiet
```

Expected: exits 0 with no errors.

- [ ] **Step 6: Update `plugins/ai-stack/reference/mcps.yaml`**

Remove the `gmail` entry:

```yaml
  - name: gmail
    transport: http
    url: http://localhost:17633/mcp
    scope: user
```

Remove the `gdrive` entry:

```yaml
  - name: gdrive
    transport: http
    url: http://localhost:17100/mcp
    scope: user
```

Add the `workspace-mcp` entry after the `notebooklm` entry:

```yaml
  - name: workspace-mcp
    transport: http
    url: http://localhost:17150/mcp
    scope: user
```

- [ ] **Step 7: Bump plugin version to `0.7.0`**

In `plugins/ai-stack/.claude-plugin/plugin.json`, change:

```json
"version": "0.6.3"
```

to:

```json
"version": "0.7.0"
```

- [ ] **Step 8: Commit**

```bash
git add compose.yaml \
        plugins/ai-stack/reference/mcps.yaml \
        plugins/ai-stack/.claude-plugin/plugin.json
git commit -m "feat(ai-stack): replace gmail-mcp and gdrive-mcp with workspace-mcp"
```

---

## Task 5: Google Cloud setup, first-run auth, and MCP migration

This task requires interactive steps (browser, Claude Code CLI). Do them in order.

**Files:**
- No code changes — configuration and validation only.

- [ ] **Step 1: Set up Google Cloud credentials**

Follow the Google Cloud setup section in the `README.md` written in Task 3:

1. Open [Google Cloud Console](https://console.cloud.google.com/) → select your existing project.
2. Enable these APIs under **APIs & Services → Library**:
   - Gmail API, Google Drive API, Google Calendar API, Google Docs API,
     Google Sheets API, Google Slides API, Google Forms API, Apps Script API
3. Go to **APIs & Services → Credentials → Create Credentials → OAuth Client ID**.
4. Application type: **Web application**.
5. Add authorized redirect URI: `http://localhost:17150/oauth2callback`
6. Copy the Client ID and Client Secret.

Add to `/Users/kpiwko/devel/ai-stack/.env`:

```
GOOGLE_OAUTH_CLIENT_ID=<your-client-id>
GOOGLE_OAUTH_CLIENT_SECRET=<your-client-secret>
```

- [ ] **Step 2: Create the credentials directory on the host**

```bash
mkdir -p ~/.config/workspace-mcp
```

- [ ] **Step 3: Start workspace-mcp**

```bash
cd /Users/kpiwko/devel/ai-stack
podman compose up -d workspace-mcp
sleep 5
podman compose logs workspace-mcp
```

Expected: server starts on port 8000, no crash. Logs show something like `Uvicorn running on http://0.0.0.0:8000`.

- [ ] **Step 4: Complete OAuth auth**

```bash
open http://localhost:17150/
```

In your browser: sign in with your Google account, grant all requested permissions, wait for the redirect to `localhost:17150/oauth2callback`. The page should confirm authorization.

Verify the token was saved:

```bash
ls ~/.config/workspace-mcp/
```

Expected: at least one file (the OAuth token JSON).

- [ ] **Step 5: Verify MCP endpoint**

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:17150/mcp
```

Expected: `200` or `405` (any HTTP response, not connection refused).

- [ ] **Step 6: Remove old MCP registrations from Claude Code**

```bash
claude mcp remove gmail
claude mcp remove gdrive
```

Expected: both removed without error. If either shows "not found", it was already removed — that's fine.

- [ ] **Step 7: Register workspace-mcp with Claude Code**

```bash
claude mcp add --transport http --scope user workspace-mcp http://localhost:17150/mcp
claude mcp list
```

Expected: `workspace-mcp` appears in the list as connected.

- [ ] **Step 8: Push ai-stack changes**

```bash
cd /Users/kpiwko/devel/ai-stack
git push origin main
```
