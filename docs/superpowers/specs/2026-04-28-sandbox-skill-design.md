# Design: `/ai-stack:sandbox` skill

**Date:** 2026-04-28  
**Status:** Approved

---

## Overview

A new skill in the `ai-stack` plugin that guides users through installing or updating the LINCE toolkit (agent-sandbox + lince-dashboard). It handles prerequisite checking, locates a local lince checkout, and delegates to lince's own shell installers — no logic duplication.

---

## Invocation

```
/ai-stack:sandbox          ← auto-detect state; install or update as needed
/ai-stack:sandbox install  ← force install mode
/ai-stack:sandbox update   ← force update mode
```

---

## Workflow

### Step 0 — Detect if running inside agent-sandbox (guard)

Before doing anything else, check whether the skill is being invoked from inside an agent-sandbox environment. If it is, the install/update cannot succeed — the sandbox makes `$HOME` read-only (or a tmpfs), so writes to `~/.local/bin`, `~/.config/zellij/`, etc. will fail silently or with errors.

**Detection signals** (check all three; any one is sufficient):

| Signal | Command | Meaning |
|---|---|---|
| `LINCE_AGENT_ID` env var is set | `[ -n "$LINCE_AGENT_ID" ]` | Inside a sandboxed agent (when `--id` was passed) |
| `$HOME` path is under `.agent-sandbox/` | `[[ "$HOME" == */.agent-sandbox/* ]]` | nono backend sets `HOME=~/.agent-sandbox/home` |
| `$HOME` is a tmpfs mount | `findmnt -n -o FSTYPE "$HOME" 2>/dev/null \| grep -q tmpfs` | bwrap backend overlays `$HOME` with tmpfs |

If any signal fires, exit immediately with a clear message:
```
⚠  This skill cannot run inside agent-sandbox.

The installer writes to ~/.local/bin, ~/.config/zellij/, and ~/.bashrc —
all of which are read-only or ephemeral inside the sandbox.

Run /ai-stack:sandbox from a regular terminal session (outside the sandbox).
```

> **Note for lince project**: A dedicated `AGENT_SANDBOX=1` env var set unconditionally by both bwrap and nono backends would make this check simpler and more reliable. Worth filing as a feature request.

### Step 1 — Detect current state

Check what is already installed:
- `command -v agent-sandbox` (sandbox binary)
- `~/.config/zellij/plugins/lince-dashboard.wasm` (dashboard plugin)
- `~/.config/lince-dashboard/config.toml` (dashboard config)

If all components are present and no argument was given → default to **update mode**.  
If nothing is installed → default to **install mode**.  
Mixed state → report which are installed/missing and ask the user which mode to use.

### Step 2 — Locate lince source (local only, no cloning)

Search candidate paths in order:
1. `<skill-base-dir>/../../../../../lince/` — the `lince/` sibling directory inside the ai-stack checkout (skill lives at `plugins/ai-stack/skills/sandbox/`, so 5 levels up reaches repo root)
2. `./lince/` — current working directory
3. `~/lince`

Verify each by checking that `quickstart.sh` exists inside it.

If a candidate is found, confirm with the user:
```
Found lince at: /path/to/lince
Use this path? [Y/n]:
```

If no candidate is found, ask the user to provide the path:
```
Could not find lince locally.
Please provide the path to your lince checkout:
Path:
```

No network access, no cloning.

### Step 3 — Check prerequisites

Detect OS (Linux vs macOS) and check accordingly:

| Tool | Required for | Install hint |
|---|---|---|
| `python3` (3.11+) | sandbox | `dnf install python3` / `brew install python@3.11` |
| `git` | both | system package manager |
| `zellij` (≥ 0.40) | dashboard | `dnf install zellij` / `brew install zellij` |
| `rustup` | dashboard | `curl ... https://sh.rustup.rs | sh` |
| `wasm32-wasip1` target | dashboard | `rustup target add wasm32-wasip1` |
| `bubblewrap` | sandbox (Linux) | `dnf install bubblewrap` / `apt install bubblewrap` |
| `nono` | sandbox (macOS) | `brew install nono` |

Display status clearly:
```
Prerequisites:
  ✓ python3 3.12
  ✓ git
  ✓ zellij 0.43.0
  ✓ rustup + wasm32-wasip1
  ✗ bubblewrap — not found
    Fedora/RHEL: sudo dnf install bubblewrap
    Ubuntu/Debian: sudo apt install bubblewrap
```

If a blocking prerequisite is missing (e.g. no sandbox backend at all, no rustup), warn and ask:
```
Missing required tools. Continue anyway? [y/N]:
```

### Step 4A — Install mode

Run:
```bash
bash <lince-path>/quickstart.sh
```

The existing interactive TUI handles all decisions: sandbox backend selection, agent selection (Claude/Codex/Gemini/OpenCode), VoxCode, confirmation, WASM build, and alias setup. The skill does not reimplement any of this.

### Step 4B — Update mode

Let the user pick what to update:
```
Components to update:
  1) agent-sandbox
  2) lince-dashboard
  3) both [default]

Choice [3]:
```

Then run the corresponding updaters:
- `bash <lince-path>/sandbox/update.sh`
- `bash <lince-path>/lince-dashboard/update.sh`

### Step 5 — Post-action guidance

**After install:**
```
Done! Reload your shell and launch the dashboard:

  source ~/.bashrc    # or ~/.zshrc
  zd

Press 'n' to spawn your first agent. Press '?' for the full keybindings.

Note: the /lince-setup skill has been installed to ~/.claude/skills/ —
use it to register new AI agents with the dashboard.
```

**After update:**
```
Updated. If you're inside a Zellij session, restart it to load the new plugin.
```

---

## Files

| File | Change |
|---|---|
| `plugins/ai-stack/skills/sandbox/SKILL.md` | New — the skill |
| `plugins/ai-stack/.claude-plugin/plugin.json` | Minor version bump (new skill added) |

---

## Out of scope

- Cloning lince from GitHub
- Implementing backend/agent selection (delegated to `quickstart.sh`)
- Building the WASM plugin (delegated to `lince-dashboard/install.sh`)
- Manual uninstall guidance
