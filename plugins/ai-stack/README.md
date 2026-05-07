# ai-stack plugin

Maintenance commands for this repo. Not distributed via the marketplace — available
automatically when working inside the ai-stack repository.

## Commands

| Command | Description |
|---|---|
| `/ai-stack:up` | Start the container stack (copies compose.yaml + .env if missing, then `podman compose up -d`) |
| `/ai-stack:down` | Stop all compose services |
| `/ai-stack:bootstrap` | Full machine setup (runtimes, LSPs, plugins, skills, MCPs) |
| `/ai-stack:modify [plugin\|skill\|mcp] [add\|update\|remove]` | Add, update, or remove a registry entry |
| `/ai-stack:project-init` | Initialise current directory as an ai-stack project (CLAUDE.md, AGENTS.md, optional skills) |
