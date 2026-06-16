---
description: Show the current health of all ai-stack compose services with endpoints.
---

# /ai-stack:status

## Synopsis

```
/ai-stack:status   ← show service health for the ai-stack compose services
```

The stack runs as a global singleton — services started from the ai-stack repo are
visible from any working directory. This skill checks CWD for a local compose.yaml
and falls back to the plugin reference copy so it works from any project directory.

---

## Reference files

> **Path resolution:** `../../reference/X` is relative to this skill's base directory.
> Use the absolute path from the `Base directory for this skill:` header: `<base-dir>/../../reference/X`.

| What | File |
|---|---|
| Stack definition (fallback) | `../../reference/compose.yaml` |

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

### Step 2 — Locate compose.yaml

Check CWD first, then fall back to the plugin reference:

```bash
if [ -f compose.yaml ]; then
  echo "cwd"
elif [ -f "<base-dir>/../../reference/compose.yaml" ]; then
  echo "reference"
else
  echo "missing"
fi
```

Where `<base-dir>` is the path from the `Base directory for this skill:` header.

- If found in CWD → record `COMPOSE_FILE=compose.yaml` (relative)
- If found in reference → record `COMPOSE_FILE=<base-dir>/../../reference/compose.yaml` (absolute)
- If neither found → stop and display:

```
✗ compose.yaml not found.
  Run /ai-stack:up first to start the stack.
```

### Step 3 — Collect status

Run using whichever compose file was found:

```bash
podman compose -f "$COMPOSE_FILE" ps   # or: docker compose -f "$COMPOSE_FILE" ps
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
devlake-mysql-local       running    http://localhost:17300/mcp
devlake-mysql-staging     exited
devlake-mysql-prod        running    http://localhost:17320/mcp

Config: <absolute path to COMPOSE_FILE>
========================
```

For any `exited` service, append a hint on the next line:

```
✗ devlake-mysql-staging exited — check its required variables in .env
```
