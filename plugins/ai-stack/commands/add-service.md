---
description: Scaffold a new MCP service in this repo — creates Containerfile, multi-arch GitHub Actions workflow, and a compose.yaml entry.
argument-hint: "<service-name>"
---

# /ai-stack:add-service

## Synopsis

```
/ai-stack:add-service <service-name>
```

Scaffolds a complete new MCP service following the patterns already established in this repo.

---

## What gets created

1. `mcp/<service-name>/Containerfile` — multi-stage build (builder + UBI9 runtime)
2. `.github/workflows/<service-name>.yaml` — multi-arch Buildah workflow (amd64 + arm64)
3. Entry in `compose.yaml` — using `ghcr.io/<owner>/<service-name>:latest`

---

## Process

### Step 1: Gather info

Ask if not provided:
- Service name (kebab-case)
- Base technology: Go / Node.js / Python / other
- Internal port the service listens on
- Any environment variables it needs

### Step 2: Scaffold Containerfile

Follow the two-stage pattern from existing services:

**Go services:**
```dockerfile
FROM golang:<version> AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o <binary> ./cmd/<name>/

FROM registry.access.redhat.com/ubi9/ubi-minimal:latest
COPY --from=builder /build/<binary> /usr/local/bin/<binary>
EXPOSE <port>
CMD ["/usr/local/bin/<binary>"]
```

**Node.js services:**
```dockerfile
FROM registry.access.redhat.com/ubi9/nodejs-22:latest AS builder
# ... build steps ...

FROM registry.access.redhat.com/ubi9/nodejs-22-minimal:latest AS runtime
EXPOSE <port>
CMD ["node", "dist/index.js"]
```

Add a `.dockerignore` alongside the Containerfile excluding: `.env`, `*.env`,
`credentials.json`, `token.json`, `dist/`, `bin/`, `.claude/`.

### Step 3: Scaffold GitHub Actions workflow

Use the multi-arch Buildah pattern from `.github/workflows/mcp-mysql.yaml`:
- Matrix: `ubuntu-24.04` (amd64) + `ubuntu-24.04-arm` (arm64)
- Build with `redhat-actions/buildah-build@v2`
- Push per-arch image tagged `<sha>-<arch>`
- Manifest job merges into `ghcr.io/<owner>/<service-name>:latest`
- Path filter: `mcp/<service-name>/**` and the workflow file itself

### Step 4: Add compose.yaml entry

Follow the existing pattern — use `ghcr.io/<owner>/<service-name>:latest`,
add to the `ai-stack` network, expose the port, pass env vars from `.env`.

Add a matching entry to `env.example` for any new environment variables.

### Step 5: Show summary

List all created/modified files and remind the user to:
1. Push to trigger the first CI build
2. Make the ghcr.io package public after first push (GitHub → Packages → Package settings)
3. Register the MCP server with Claude Code once running
