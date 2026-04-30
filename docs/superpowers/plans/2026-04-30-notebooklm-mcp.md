# notebooklm-mcp Container Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and publish a UBI9-based container image that runs `notebooklm-mcp-cli` as an HTTP MCP server with a noVNC web interface for browser-based Google auth, then wire it into the ai-stack compose stack.

**Architecture:** Single-stage UBI9 Python 3.12 container running four processes via an entrypoint script: Xvfb (virtual display), x11vnc, noVNC/websockify, and the MCP server. Credentials are bind-mounted from the host so they survive restarts. noVNC (port 6080) is only used at initial auth and cookie refresh; the MCP endpoint (port 17200) is the day-to-day interface.

**Tech Stack:** `registry.access.redhat.com/ubi9/python-312`, EPEL (x11vnc, noVNC), uv, `notebooklm-mcp-cli==0.6.1`, Playwright Chromium, GitHub Actions (`docker/build-push-action`), ghcr.io.

---

## File Map

### New repo: `kpiwko/notebooklm-mcp`

| File | Purpose |
|------|---------|
| `Containerfile` | Single-stage image definition |
| `scripts/entrypoint.sh` | Starts Xvfb, x11vnc, noVNC, then MCP server |
| `.github/workflows/build.yaml` | Builds and pushes to `ghcr.io/kpiwko/notebooklm-mcp` |
| `README.md` | Auth flow, compose snippet, cookie refresh |

### Existing repo: `ai-stack`

| File | Change |
|------|--------|
| `compose.yaml` | Add `notebooklm-mcp` service |
| `plugins/ai-stack/reference/mcps.yaml` | Add `notebooklm` MCP entry |
| `plugins/ai-stack/.claude-plugin/plugin.json` | Bump version `0.6.2` → `0.6.3` |

---

## Task 1: Create repo and stub structure

**Files:**
- Create: GitHub repo `kpiwko/notebooklm-mcp` (manual step)
- Create: `Containerfile`
- Create: `scripts/entrypoint.sh` (stub)
- Create: `.gitignore`

- [ ] **Step 1: Create the GitHub repo**

```bash
gh repo create kpiwko/notebooklm-mcp --public --description "NotebookLM MCP server container with noVNC auth"
gh repo clone kpiwko/notebooklm-mcp
cd notebooklm-mcp
```

- [ ] **Step 2: Write `.gitignore`**

```
__pycache__/
*.pyc
.env
```

- [ ] **Step 3: Write stub `scripts/entrypoint.sh`** (full version comes in Task 3)

```bash
mkdir scripts
cat > scripts/entrypoint.sh << 'EOF'
#!/bin/bash
set -e
echo "entrypoint stub — not yet implemented"
EOF
chmod +x scripts/entrypoint.sh
```

- [ ] **Step 4: Write `Containerfile`**

```dockerfile
FROM registry.access.redhat.com/ubi9/python-312:latest

LABEL name="notebooklm-mcp" \
      summary="NotebookLM MCP Server" \
      description="MCP server providing Google NotebookLM access via browser automation" \
      maintainer="kpiwko@redhat.com"

USER root

# EPEL provides x11vnc and noVNC (pulls in websockify); Chromium system deps below
RUN dnf install -y \
    https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm \
    && dnf install -y \
    xorg-x11-server-Xvfb x11vnc novnc xorg-x11-utils \
    alsa-lib at-spi2-atk at-spi2-core atk cairo cups-libs \
    dbus-libs expat flac-libs gdk-pixbuf2 glib2 glibc gtk3 \
    libX11 libXcomposite libXdamage libXext libXfixes libXrandr \
    libXtst libcanberra-gtk3 libdrm libgcc libstdc++ libxcb \
    libxkbcommon libxshmfence libxslt mesa-libgbm nspr nss \
    nss-util pango zlib \
    && dnf clean all && rm -rf /var/cache/dnf

RUN pip install --upgrade pip uv \
    && uv tool install notebooklm-mcp-cli==0.6.1 \
    && pip install playwright \
    && playwright install --only-shell chromium \
    && pip uninstall -y playwright

ENV DISPLAY=:99 \
    PATH="/root/.local/bin:$PATH"

VOLUME ["/root/.notebooklm-mcp-cli"]

EXPOSE 17200 6080

COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
```

Note: `xorg-x11-utils` provides `xdpyinfo` used in the entrypoint readiness check. If the build fails because the package name differs on UBI9, try `xorg-x11-apps` or check with `dnf search xdpyinfo`.

- [ ] **Step 5: Build the image locally to catch dnf/pip errors**

```bash
podman build -t localhost/notebooklm-mcp:dev .
```

Expected: image builds successfully, final size ~2–3 GB (Python + Chromium + VNC stack).

If `dnf install` fails on a package name, debug with:
```bash
podman run --rm registry.access.redhat.com/ubi9/python-312:latest \
  bash -c "dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm \
  && dnf search xdpyinfo && dnf search novnc"
```

- [ ] **Step 6: Verify package paths inside the built image**

```bash
podman run --rm localhost/notebooklm-mcp:dev bash -c "
  echo '=== noVNC web root ===' && find /usr/share/novnc -name 'vnc.html' 2>/dev/null
  echo '=== websockify ===' && which websockify || echo 'NOT FOUND — check PATH'
  echo '=== xdpyinfo ===' && which xdpyinfo || echo 'NOT FOUND — add xorg-x11-utils to dnf install'
  echo '=== notebooklm-mcp ===' && which notebooklm-mcp
"
```

Expected output:
```
=== noVNC web root ===
/usr/share/novnc/vnc.html
=== websockify ===
/usr/bin/websockify
=== xdpyinfo ===
/usr/bin/xdpyinfo
=== notebooklm-mcp ===
/root/.local/bin/notebooklm-mcp
```

**If paths differ**, update `scripts/entrypoint.sh` in Task 3 accordingly (e.g. `/usr/share/novnc/` might be `/usr/share/novnc/utils/` — adjust the `--web` flag).

- [ ] **Step 7: Commit**

```bash
git add Containerfile scripts/entrypoint.sh .gitignore
git commit -m "feat: add Containerfile and stub entrypoint"
```

---

## Task 2: Verify MCP server runs headlessly

Before building the full entrypoint, confirm `notebooklm-mcp` can start without a display.

**Files:**
- No file changes — this is a smoke test only.

- [ ] **Step 1: Run the MCP server in isolation inside the container**

```bash
podman run --rm -p 17200:17200 localhost/notebooklm-mcp:dev \
  notebooklm-mcp --transport http --port 17200 &
sleep 3
```

- [ ] **Step 2: Hit the MCP endpoint**

```bash
curl -s http://localhost:17200/mcp \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  --max-time 5
```

Expected: any JSON response or SSE stream (not a connection refused). The exact response shape depends on the MCP initialization handshake — any non-error response confirms the server is up.

If the request hangs or returns a connection error, the server may need `DISPLAY` set even for headless mode. In that case add `--env DISPLAY=:99` and start Xvfb first — but that scenario is handled in Task 3 anyway.

- [ ] **Step 3: Stop the background container**

```bash
podman stop $(podman ps -q --filter ancestor=localhost/notebooklm-mcp:dev)
```

---

## Task 3: Write full entrypoint and verify noVNC auth

**Files:**
- Modify: `scripts/entrypoint.sh`

- [ ] **Step 1: Write the full entrypoint**

Use the noVNC web root and websockify path confirmed in Task 1 Step 6. Default assumes `/usr/share/novnc`.

```bash
cat > scripts/entrypoint.sh << 'EOF'
#!/bin/bash
set -e

# Start virtual display
Xvfb :99 -screen 0 1280x800x24 -nolisten tcp &

# Wait for Xvfb to be ready before connecting x11vnc
until xdpyinfo -display :99 >/dev/null 2>&1; do sleep 0.1; done

# Start VNC server (no password, local only)
x11vnc -display :99 -nopw -listen 0.0.0.0 -forever -quiet &

# Start noVNC web client (bridges websocket on 6080 → VNC on 5900)
websockify --web /usr/share/novnc 6080 localhost:5900 &

# Start MCP server (foreground — container exits if this dies)
exec notebooklm-mcp --transport http --port 17200
EOF
chmod +x scripts/entrypoint.sh
```

- [ ] **Step 2: Rebuild with updated entrypoint**

```bash
podman build -t localhost/notebooklm-mcp:dev .
```

- [ ] **Step 3: Run the full container**

```bash
podman run -d --name nlm-test \
  -p 17200:17200 \
  -p 6080:6080 \
  localhost/notebooklm-mcp:dev
sleep 5
podman logs nlm-test
```

Expected logs: no errors; the MCP server line should appear last (it's the foreground process).

- [ ] **Step 4: Verify noVNC is reachable**

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:6080/vnc.html
```

Expected: `200`

- [ ] **Step 5: Verify MCP endpoint is reachable**

```bash
curl -s http://localhost:17200/mcp \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  --max-time 5
```

Expected: any non-error response.

- [ ] **Step 6: Verify nlm login opens Chrome in noVNC**

Open `http://localhost:6080/vnc.html` in a browser. Then in a second terminal:

```bash
podman exec -it nlm-test nlm login
```

Expected: Chrome window appears in the noVNC browser tab with a Google login page.

Type `Ctrl-C` to cancel (no real login needed for this smoke test).

- [ ] **Step 7: Stop and clean up**

```bash
podman stop nlm-test && podman rm nlm-test
```

- [ ] **Step 8: Commit**

```bash
git add scripts/entrypoint.sh
git commit -m "feat: implement entrypoint with Xvfb, x11vnc, noVNC, and MCP server"
```

---

## Task 4: Write CI/CD workflow

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

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Log in to ghcr.io
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/kpiwko/notebooklm-mcp
          tags: |
            type=ref,event=branch
            type=ref,event=tag
            type=sha,prefix=
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
EOF
```

- [ ] **Step 2: Commit and push to trigger CI**

```bash
git add .github/workflows/build.yaml
git commit -m "ci: add build and push workflow to ghcr.io"
git push origin main
```

- [ ] **Step 3: Monitor the workflow run**

```bash
gh run list --repo kpiwko/notebooklm-mcp --limit 5
gh run watch --repo kpiwko/notebooklm-mcp
```

Expected: workflow succeeds and image appears at `ghcr.io/kpiwko/notebooklm-mcp:latest`.

- [ ] **Step 4: Verify image is publicly pullable**

```bash
podman pull ghcr.io/kpiwko/notebooklm-mcp:latest
```

If the pull fails with a permission error, make the package public:
Go to `https://github.com/users/kpiwko/packages/container/notebooklm-mcp/settings` → "Change visibility" → Public.

---

## Task 5: Write README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README**

```markdown
# notebooklm-mcp

NotebookLM MCP server container. Runs [`notebooklm-mcp-cli`](https://github.com/jacob-bd/notebooklm-mcp-cli)
as an HTTP MCP server with a browser-based auth interface via noVNC.

## Ports

| Port | Purpose |
|------|---------|
| 17200 | MCP HTTP endpoint (`/mcp`) |
| 6080 | noVNC web interface (auth only) |

## First-run auth

NotebookLM has no public API. Auth requires a one-time interactive Google login
inside the container's virtual browser.

```bash
# 1. Start the container
podman run -d --name notebooklm-mcp \
  -p 17200:17200 \
  -p 6080:6080 \
  -v ~/.notebooklm-mcp-cli:/root/.notebooklm-mcp-cli \
  ghcr.io/kpiwko/notebooklm-mcp:latest

# 2. Open the VNC interface in your browser
open http://localhost:6080/vnc.html

# 3. In a second terminal, start the login flow
podman exec -it notebooklm-mcp nlm login
# Chrome opens in the VNC window — log into Google NotebookLM

# 4. Verify auth succeeded
podman exec notebooklm-mcp nlm login --check
```

Credentials are saved to `~/.notebooklm-mcp-cli/` on the host and survive container restarts.

## Cookie refresh

Google session cookies expire every few weeks. When you see auth errors, repeat the login:

```bash
open http://localhost:6080/vnc.html
podman exec -it notebooklm-mcp nlm login
```

## MCP registration

```bash
claude mcp add --transport http --scope user notebooklm http://localhost:17200/mcp
```

## ai-stack compose snippet

```yaml
notebooklm-mcp:
  image: ghcr.io/kpiwko/notebooklm-mcp:latest
  networks: [ai-stack]
  ports:
    - "17200:17200"
    - "6080:6080"
  volumes:
    - /Users/kpiwko/.notebooklm-mcp-cli:/root/.notebooklm-mcp-cli
  restart: unless-stopped
```
```

- [ ] **Step 2: Commit and push**

```bash
git add README.md
git commit -m "docs: add README with auth flow and compose snippet"
git push origin main
```

---

## Task 6: Update ai-stack repo

**Files:**
- Modify: `compose.yaml`
- Modify: `plugins/ai-stack/reference/mcps.yaml`
- Modify: `plugins/ai-stack/.claude-plugin/plugin.json`

Work in the `ai-stack` repo for this task.

- [ ] **Step 1: Add service to `compose.yaml`**

Add after the `gdrive-mcp` block (before the closing of the `services:` map):

```yaml
  ##############################################################################
  # notebooklm-mcp — NotebookLM MCP server, streamable HTTP transport
  # MCP endpoint: http://localhost:17200/mcp
  # Auth (first run or cookie refresh):
  #   1. open http://localhost:6080/vnc.html
  #   2. podman exec -it ai-stack-notebooklm-mcp-1 nlm login
  ##############################################################################
  notebooklm-mcp:
    image: ghcr.io/kpiwko/notebooklm-mcp:latest
    networks: [ai-stack]
    ports:
      - "17200:17200"
      - "6080:6080"
    volumes:
      - /Users/kpiwko/.notebooklm-mcp-cli:/root/.notebooklm-mcp-cli
    restart: unless-stopped
```

- [ ] **Step 2: Add MCP entry to `plugins/ai-stack/reference/mcps.yaml`**

Append after the `devlake-local-mysql-mcp` block:

```yaml
  - name: notebooklm
    transport: http
    url: http://localhost:17200/mcp
    scope: user
```

- [ ] **Step 3: Bump plugin version in `plugins/ai-stack/.claude-plugin/plugin.json`**

Change `"version": "0.6.2"` to `"version": "0.6.3"`.

- [ ] **Step 4: Verify compose file is valid**

```bash
podman compose config --quiet
```

Expected: no errors (exits 0).

- [ ] **Step 5: Commit**

```bash
git add compose.yaml plugins/ai-stack/reference/mcps.yaml plugins/ai-stack/.claude-plugin/plugin.json
git commit -m "feat(ai-stack): add notebooklm-mcp service and MCP registration"
```

---

## Task 7: End-to-end smoke test with published image

Validates that the full stack works from the perspective of a fresh pull.

- [ ] **Step 1: Pull the published image**

```bash
podman pull ghcr.io/kpiwko/notebooklm-mcp:latest
```

- [ ] **Step 2: Start via compose**

```bash
cd /path/to/ai-stack
podman compose up -d notebooklm-mcp
sleep 5
podman compose logs notebooklm-mcp
```

Expected: MCP server started, no crash loops.

- [ ] **Step 3: Verify MCP endpoint**

```bash
curl -s http://localhost:17200/mcp \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  --max-time 5
```

Expected: response (not connection refused).

- [ ] **Step 4: Verify noVNC**

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:6080/vnc.html
```

Expected: `200`

- [ ] **Step 5: Register with Claude Code**

```bash
claude mcp add --transport http --scope user notebooklm http://localhost:17200/mcp
claude mcp list
```

Expected: `notebooklm` appears in the list.
