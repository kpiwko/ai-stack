# Claude Hooks Reference

Claude Code supports shell hooks — commands that run automatically on events.

## Hook events

| Event | When it fires |
|---|---|
| `PreToolUse` | Before any tool call |
| `PostToolUse` | After any tool call |
| `Stop` | When the agent stops producing output |
| `SubagentStop` | When a subagent stops |

## Settings location

Hooks are defined in `~/.claude/settings.json` (user scope) or `.claude/settings.json`
(project scope, committed to repo).

## Format

```json
{
  "hooks": {
    "<Event>": [
      {
        "matcher": "<tool-name or glob or *>",
        "hooks": [
          { "type": "command", "command": "<shell command>" }
        ]
      }
    ]
  }
}
```

## Example: session-start environment check

This hook fires on the first tool use of each session and injects environment status
(git state, .env presence, running services) as a system-reminder:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          { "type": "command", "command": "~/.claude/scripts/session-start.sh" }
        ]
      }
    ]
  }
}
```

Save the script to `~/.claude/scripts/session-start.sh` and make it executable:

```bash
mkdir -p ~/.claude/scripts
chmod +x ~/.claude/scripts/session-start.sh
```

## Debugging hooks

```bash
# Test a hook manually
bash ~/.claude/scripts/session-start.sh

# Hook output appears in Claude's system-reminder messages during a session
```

To remove a hook: delete its entry from `~/.claude/settings.json`.
