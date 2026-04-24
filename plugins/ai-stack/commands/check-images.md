---
description: Verify all compose.yaml services use remote registry images, not localhost/ references.
---

# /ai-stack:check-images

## Synopsis

```
/ai-stack:check-images
```

Scans `compose.yaml` for any `image:` entries that still reference `localhost/` instead
of a remote registry (`ghcr.io/`, `registry.access.redhat.com/`, etc.).

---

## Process

1. Read `compose.yaml`.
2. Find all `image:` lines.
3. Report:
   - **OK**: images using a remote registry
   - **FAIL**: images using `localhost/` or no registry prefix

```
=== IMAGE CHECK ===
OK   ghcr.io/kpiwko/gmail-mcp-server:latest   (gmail-mcp)
OK   ghcr.io/kpiwko/mcp-mysql:latest           (devlake-local-mysql-mcp)
FAIL localhost/my-new-service:latest           (my-new-service)
==================
```

4. For any FAIL entries, suggest the correct `ghcr.io/<owner>/<name>:latest` image reference
   and remind the user to set up the CI workflow with `/ai-stack:add-workflow`.
