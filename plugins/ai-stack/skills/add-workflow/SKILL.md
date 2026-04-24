---
description: Generate a multi-arch Buildah GitHub Actions workflow for an existing service in mcp/.
argument-hint: "<service-name>"
---

# /ai-stack:add-workflow

## Synopsis

```
/ai-stack:add-workflow <service-name>
```

Generates `.github/workflows/<service-name>.yaml` using the multi-arch Buildah pattern
established in this repo. Use this when a service directory already exists but has no CI.

---

## Process

1. Confirm `mcp/<service-name>/Containerfile` exists — error if not.
2. Read the existing `mcp/mysql` workflow as the template reference.
3. Generate `.github/workflows/<service-name>.yaml` with:
   - `on.push.paths`: `mcp/<service-name>/**` and the workflow file itself
   - `on.push.tags`: `<service-name>/v*`
   - Matrix: `ubuntu-24.04` (amd64) + `ubuntu-24.04-arm` (arm64)
   - Build: `redhat-actions/buildah-build@v2`
   - Push per-arch: `redhat-actions/push-to-registry@v2`
   - Manifest: `docker buildx imagetools create` merging both arch images
   - Image name: `ghcr.io/${{ github.repository_owner }}/<service-name>`
   - Final tags: `latest` on default branch, version from tag pattern
4. Show the generated file and ask for confirmation before writing.
