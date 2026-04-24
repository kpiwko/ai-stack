# ai-stack plugin

Maintenance commands for this repo. Not distributed via the marketplace — available
automatically when working inside the ai-stack repository.

## Commands

| Command | Description |
|---|---|
| `/ai-stack:add-service <name>` | Scaffold Containerfile, multi-arch CI workflow, and compose.yaml entry |
| `/ai-stack:add-workflow <name>` | Generate multi-arch Buildah workflow for an existing service |
| `/ai-stack:check-images` | Verify all compose.yaml services use remote registry images |
| `/ai-stack:install-plugins [name\|all]` | Install ai-stack and 3rd party plugins (user/project/local scope) |
| `/ai-stack:install-skills [name\|all]` | Install bare skills (user/project/local scope) |
| `/ai-stack:install-mcps [name\|all]` | Register MCP servers with Claude Code (user/project/local scope) |
