---
description: Show the current health of all ai-stack compose services with endpoints.
---

# /ai-stack:status

## Synopsis

```
/ai-stack:status   ← show service health for the compose stack in CWD
```

---

## Process

### Step 1 — Prerequisites check

Run:

```bash
(command -v podman >/dev/null 2>&1 && podman compose version >/dev/null 2>&1 && echo "podman") \
  || (command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1 && echo "docker") \
  || echo "MISSING"
```

If neither is found, stop and display:

```
✗ podman / docker compose: not found
```

### Step 2 — Check compose.yaml

```bash
ls compose.yaml 2>/dev/null && echo "exists" || echo "missing"
```

If missing, display:

```
✗ compose.yaml not found in current directory.
  Run /ai-stack:up first.
```

### Step 3 — Collect status

Run:

```bash
podman compose ps   # or: docker compose ps
```

### Step 4 — Display summary

Print a table with a row per service. Show `running` or `exited`. Include known
endpoints for running services (source from compose.yaml ports mapping):

```
=== ai-stack STATUS ===

Service                   Status     Endpoint
────────────────────────────────────────────────────────────
notebooklm-mcp            running    http://localhost:17200/mcp
                                     noVNC: http://localhost:17201/vnc.html
workspace-mcp             running    http://localhost:17150/mcp
devlake-local-mysql-mcp   exited
devlake-prod-mysql-mcp    running    http://localhost:17300/mcp

Config: <absolute path to CWD>/.env
========================
```

For any `exited` service, append a hint on the next line:

```
✗ devlake-local-mysql-mcp exited — check its required variables in .env
```
