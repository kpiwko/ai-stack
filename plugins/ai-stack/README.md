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
| `/ai-stack:status` | Show compose service health + endpoints |

## Evals

Eval scenarios for each skill live in `evals/promptfooconfig-<skill>.yaml`.

```bash
just eval up                    # all scenarios for one skill
just eval up "Fresh directory"  # filter by description
just eval "" "" 3               # all skills, pass@3
just eval                       # all skills, all scenarios
```

See `evals/framework.md` for conventions and the TDD cycle.
