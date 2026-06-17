# Claude Code Rules

Project conventions are in [AGENTS.md](./AGENTS.md).

---

## Output Format

- Keep responses concise and actionable.
- Use code blocks with appropriate language tags.
- Prefer editing existing files over creating new ones.

---

## Tool Usage

- Read files before editing.
- Batch independent tool calls in one message.
- Use Grep/Glob for search, not Bash find/grep.

---

## Skills & Multi-Agent Coordination

Invoke the relevant skill before starting a task.

| Skill | When to use |
|---|---|
| `/superpowers:brainstorming` | Before implementing any feature |
| `/superpowers:writing-plans` | Before multi-step tasks |
| `/superpowers:executing-plans` | When running a written plan |
| `/superpowers:systematic-debugging` | When encountering a bug |
| `/superpowers:requesting-code-review` | Before merging |
| `/ai-stack:up` | Start the container stack (idempotent; copies compose.yaml + .env if missing) |
| `/ai-stack:bootstrap` | Full machine setup (runtimes, LSPs, plugins, skills, MCPs) |
| `/ai-stack:modify` | Add, update, or remove a plugin/skill/MCP in the registry |
| `/ai-stack:down` | Stop the container stack |
| `/ai-stack:status` | Check service health |
| `/ai-stack:project-init` | Initialise current directory (CLAUDE.md, AGENTS.md, optional skills) |
| `/dev:review-cr` | Run CodeRabbit review on committed changes |
| `/dev:git-workflow` | Start feature branch or prepare PR/MR |

---

## Execution Pattern

For any non-trivial task:
1. Invoke the relevant skill first.
2. In one message: spawn agents, batch file ops, batch shell commands, batch todos.
3. New files go in subfolders — never in repo root.

---

## Task Tool Best Practices

- Provide clear, specific prompts.
- Use appropriate agent types: `Explore` (codebase search), `Plan` (implementation planning), `general-purpose` (multi-step tasks).

---

## Memory & Context

- Use TaskCreate/TaskUpdate to track progress across turns.
- Keep TODO.md updated for persistence across sessions.
