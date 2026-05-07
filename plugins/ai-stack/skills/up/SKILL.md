---
description: Start the ai-stack container stack. Copies compose.yaml and env.example into CWD if missing, then runs podman compose up -d. Idempotent.
---

# /ai-stack:up

## Synopsis

```
/ai-stack:up   ← set up compose.yaml + .env in CWD, then start all services
```

Idempotent — running again updates services without overwriting existing config files.

---

## Reference files

| What | File |
|---|---|
| Stack definition | `${CLAUDE_PLUGIN_ROOT}/reference/compose.yaml` |
| Environment template | `${CLAUDE_PLUGIN_ROOT}/reference/env.example` |

Read both files before starting any step.

---

## Process

### Step 1 — Prerequisites check

Run:

```bash
(command -v podman >/dev/null 2>&1 && podman compose version >/dev/null 2>&1 && echo "podman") \
  || (command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1 && echo "docker") \
  || echo "MISSING"
```

Record which tool is available (`podman` or `docker`). Use that tool for all compose
commands in subsequent steps.

If neither is found, stop and display:

```
✗ podman / docker compose: not found
  Install Podman Desktop: https://podman-desktop.io/
  or Docker Desktop:      https://www.docker.com/products/docker-desktop/
```

### Step 2 — Handle compose.yaml

Check if `compose.yaml` exists in the current directory:

```bash
ls compose.yaml 2>/dev/null && echo "exists" || echo "missing"
```

If **exists** → record `compose.yaml: found` and skip.

If **missing** → copy from the plugin:

```bash
cp "${CLAUDE_PLUGIN_ROOT}/reference/compose.yaml" compose.yaml
```

Record `compose.yaml: created`.

### Step 3 — Handle .env

Check if `.env` exists in the current directory:

```bash
ls .env 2>/dev/null && echo "exists" || echo "missing"
```

If **missing** → copy the template:

```bash
cp "${CLAUDE_PLUGIN_ROOT}/reference/env.example" .env
```

Record `.env: created from env.example`.

In both cases — scan `.env` for lines that still contain a placeholder value
(angle brackets indicate a value that was never filled in):

```bash
grep -E '^[A-Z_]+=.*<[^>]+>' .env || true
```

If any placeholder lines are found, display:

```
⚠ Fill in these variables in .env before the affected services will connect:

  GOOGLE_OAUTH_CLIENT_ID      workspace-mcp (Google OAuth)
  GOOGLE_OAUTH_CLIENT_SECRET  workspace-mcp (Google OAuth)
  DEVLAKE_MCP_SECRET_KEY      devlake-local-mysql-mcp
  KONFLUX_MYSQL_HOST          devlake-prod-mysql-mcp
  KONFLUX_MYSQL_USER          devlake-prod-mysql-mcp
  KONFLUX_MYSQL_PASS          devlake-prod-mysql-mcp
  KONFLUX_MCP_SECRET_KEY      devlake-prod-mysql-mcp

  Edit .env and re-run /ai-stack:up when ready.
```

Only show the variables that actually appeared in the `grep` output — do not
show variables that are already set to real values.

Proceed to Step 4 regardless. Services with missing vars will start but not connect.

### Step 4 — Start services

Run:

```bash
podman compose up -d   # or: docker compose up -d
```

If compose exits non-zero, print the error and stop.

### Step 5 — Summary

Run:

```bash
podman compose ps   # or: docker compose ps
```

Print a formatted summary:

```
=== ai-stack UP ===

Service                   Status     Endpoint
───────────────────────────────────────────────────────────
notebooklm-mcp            running    http://localhost:17200/mcp
                                     noVNC: http://localhost:17201/vnc.html
workspace-mcp             running    http://localhost:17150/mcp
devlake-local-mysql-mcp   running    http://localhost:17301/mcp
devlake-prod-mysql-mcp    running    http://localhost:17300/mcp

Config: <absolute path to CWD>/.env
====================================
```

For any service that shows `exited` or `error` in `compose ps`, add a line:

```
✗ <service-name>: exited — check its required variables in .env
```
