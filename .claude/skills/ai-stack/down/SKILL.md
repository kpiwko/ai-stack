---
description: Stop the ai-stack container stack. Runs podman compose down in CWD. Idempotent.
---

# /ai-stack:down

## Synopsis

```
/ai-stack:down   ← stop all compose services in the current directory
```

Idempotent — safe to run even if services are already stopped.

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
commands below.

If neither is found, stop and display:

```
✗ podman / docker compose: not found
  Install Podman Desktop: https://podman-desktop.io/
  or Docker Desktop:      https://www.docker.com/products/docker-desktop/
```

### Step 2 — Check compose.yaml present

```bash
ls compose.yaml 2>/dev/null && echo "exists" || echo "missing"
```

If missing, stop and display:

```
✗ compose.yaml not found in current directory.
  Run /ai-stack:up first to initialise the stack here.
```

### Step 3 — Stop services

Run:

```bash
podman compose down   # or: docker compose down
```

If compose exits non-zero, print the error and stop.

### Step 4 — Summary

```
=== ai-stack DOWN ===
All services stopped.
=====================
```
