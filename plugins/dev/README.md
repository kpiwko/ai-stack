# dev plugin

Developer workflow tools for Claude Code.

## Install

```
/plugin install dev@kpiwko/ai-stack
```

## Commands

| Command | Description |
|---|---|
| `/dev:review-cr [N\|branch]` | Run CodeRabbit CLI review, triage findings, apply fixes, amend commits |

## Agents

Coding agents carry language-specific conventions. Invoke them explicitly or Claude
will use them as sub-agents in coding workflows.

| Agent | Description |
|---|---|
| `@agent-dev:go-coder` | Idiomatic Go — golangci-lint rules, table-driven tests, error wrapping |
| `@agent-dev:python-coder` | Python with uv, ruff, pytest, Google-style docstrings |
| `@agent-dev:typescript-coder` | TypeScript with pnpm, ESLint, Prettier, Vitest |
