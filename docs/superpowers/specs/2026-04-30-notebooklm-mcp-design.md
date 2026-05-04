# notebooklm-mcp Container — Design Spec

**Date:** 2026-04-30  
**Status:** Approved

---

## Problem

NotebookLM has no public API. Accessing it from AI agents requires browser automation
(Playwright/CDP) to extract and reuse Google session cookies. The goal is to run
`notebooklm-mcp-cli` as a containerized MCP server that integrates with the existing
ai-stack compose setup, with a self-contained browser-based auth flow that requires no
host-side tooling.

---

## Architecture

Two runtime roles in one container:

- **MCP server** — `notebooklm-mcp --transport http --port 17200` serves the MCP HTTP
  endpoint. Chromium runs headlessly for normal operation; no display required.
- **Auth stack** — Xvfb (virtual display) + x11vnc + noVNC (web VNC client on port 6080).
  Always running; only used interactively when cookies need to be (re)created.

Credentials (`~/.notebooklm-mcp-cli/profiles/default/auth.json`) are stored on the host
and bind-mounted into the container, so they survive container restarts and rebuilds.

**Auth flow (first run and cookie refresh):**
1. `podman compose up -d notebooklm-mcp`
2. Open `http://localhost:6080/vnc.html` in a browser — virtual desktop appears
3. Run `podman exec -it ai-stack-notebooklm-mcp-1 nlm login`
4. Chrome opens inside the virtual display; log into Google NotebookLM
5. Cookies saved to the mounted volume; MCP endpoint at `http://localhost:17200/mcp` is live
6. Cookie refresh (every few weeks): repeat steps 2–4

---

## New Repository: `kpiwko/notebooklm-mcp`

A git submodule at `mcp/notebooklm-mcp`, following the existing `mcp/gmail` pattern.
The ai-stack repo references the published image; the submodule holds the Containerfile and CI.

### Repository structure

```
Containerfile
scripts/
  entrypoint.sh
.github/
  workflows/
    build.yaml
README.md
```

### `Containerfile`

```dockerfile
FROM registry.redhat.io/ubi9/python-312:latest

LABEL name="notebooklm-mcp" \
      summary="NotebookLM MCP Server" \
      description="MCP server providing Google NotebookLM access via browser automation" \
      maintainer="kpiwko@redhat.com"

USER root

# Conditionally register RHEL subscription if secrets are provided (CI path).
# Locally, Podman Desktop's RHEL podman machine passes the host subscription through automatically.
# EPEL provides x11vnc and noVNC (websockify); xorg-x11-server-Xvfb and xorg-x11-utils from AppStream.
RUN --mount=type=secret,id=rh_username \
    --mount=type=secret,id=rh_password \
    if [ -f /run/secrets/rh_username ]; then \
      subscription-manager register \
        --username=$(cat /run/secrets/rh_username) \
        --password=$(cat /run/secrets/rh_password); \
    fi \
    && dnf install -y \
      https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm \
    && dnf install -y \
      xorg-x11-server-Xvfb x11vnc novnc xorg-x11-utils \
      alsa-lib at-spi2-atk at-spi2-core atk cairo cups-libs \
      dbus-libs expat flac-libs gdk-pixbuf2 glib2 glibc gtk3 \
      libX11 libXcomposite libXdamage libXext libXfixes libXrandr \
      libXtst libcanberra-gtk3 libdrm libgcc libstdc++ libxcb \
      libxkbcommon libxshmfence libxslt mesa-libgbm nspr nss \
      nss-util pango zlib \
    && subscription-manager unregister 2>/dev/null || true \
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

### `scripts/entrypoint.sh`

```sh
#!/bin/bash
set -e

Xvfb :99 -screen 0 1280x800x24 -nolisten tcp &
# Wait for Xvfb to be ready before starting x11vnc
until xdpyinfo -display :99 >/dev/null 2>&1; do sleep 0.1; done
x11vnc -display :99 -nopw -listen 0.0.0.0 -forever -quiet &
websockify --web /usr/share/novnc 6080 localhost:5900 &

exec notebooklm-mcp --transport http --port 17200
```

### `.github/workflows/build.yaml`

Standard GitHub Actions workflow:
- Trigger: push to `main`, tags `v*`
- Log in to `registry.redhat.io` using `RH_USERNAME` / `RH_PASSWORD` repository secrets before build
- Pass secrets as `--secret id=rh_username` / `--secret id=rh_password` build args so `subscription-manager` can register during the RUN layer
- Build and push to `ghcr.io/kpiwko/notebooklm-mcp:latest` and `ghcr.io/kpiwko/notebooklm-mcp:<tag>` using `docker/build-push-action`
- Locally, Podman Desktop's RHEL machine passes the host RHEL subscription through — no extra flags needed

---

## Changes to `ai-stack` repo

### `compose.yaml` — new service

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

### `plugins/ai-stack/reference/mcps.yaml` — new entry

```yaml
  - name: notebooklm
    transport: http
    url: http://localhost:17200/mcp
    scope: user
```

---

## Port assignments

| Port | Purpose |
|------|---------|
| 17200 | MCP HTTP endpoint (`/mcp`) |
| 6080 | noVNC web interface (auth only) |

---

## Implementation checklist

### Repo: `kpiwko/notebooklm-mcp` (submodule at `mcp/notebooklm-mcp`)
- [ ] Create GitHub repo `kpiwko/notebooklm-mcp` and add as submodule
- [ ] Write `Containerfile` (UBI9 + conditional subscription-manager)
- [ ] Write `scripts/entrypoint.sh`
- [ ] Write `.github/workflows/build.yaml` (build + push to ghcr.io)
- [ ] Smoke-test: build locally, verify MCP endpoint starts headlessly
- [ ] Smoke-test: verify `nlm login` opens Chrome in noVNC at `http://localhost:6080/vnc.html`
- [ ] Write `README.md` (auth flow, compose snippet, cookie refresh instructions)

### Repo: `ai-stack`
- [ ] Add `notebooklm-mcp` service to `compose.yaml`
- [ ] Add `notebooklm` entry to `plugins/ai-stack/reference/mcps.yaml`
- [ ] Bump plugin version in `plugins/ai-stack/.claude-plugin/plugin.json`
- [ ] Commit both changes

---

## Open questions (implementation-time)

- **noVNC web root path** — EPEL's noVNC package puts web files at `/usr/share/novnc`;
  confirm this path holds on UBI9 after install. Also confirm `websockify` command is
  on PATH after `dnf install novnc` (it ships as `python3-websockify` dependency).
- **MCP headless mode** — verify `notebooklm-mcp` starts and serves `/mcp` without
  requiring `DISPLAY` (expected: yes, Chromium supports `--headless` without Xvfb).
- **`xdpyinfo` availability** — `xdpyinfo` is used in the entrypoint to wait for Xvfb;
  it comes from the `xorg-x11-utils` package which may need to be added to the
  `dnf install` list if not pulled in as a dependency.
