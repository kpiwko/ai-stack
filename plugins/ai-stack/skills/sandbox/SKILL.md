---
description: Install or update the LINCE toolkit (agent-sandbox + lince-dashboard).
argument-hint: "[install|update]"
---

# /ai-stack:sandbox

## Synopsis

```
/ai-stack:sandbox          ← auto-detect state; install or update as needed
/ai-stack:sandbox install  ← force install mode
/ai-stack:sandbox update   ← force update mode
```

---

## Process

### Step 0 — Sandbox guard

Before anything else, run these checks to detect if you are inside an agent-sandbox environment:

```bash
echo "LINCE_AGENT_ID=${LINCE_AGENT_ID:-}"
echo "HOME=$HOME"
findmnt -n -o FSTYPE "$HOME" 2>/dev/null || true
```

If any of the following are true, stop and display the message below — do not proceed:
- `LINCE_AGENT_ID` is non-empty
- `$HOME` contains `.agent-sandbox/` (e.g. `~/.agent-sandbox/home`)
- The FSTYPE of `$HOME` is `tmpfs`

```
⚠  This skill cannot run inside agent-sandbox.

The installer writes to ~/.local/bin, ~/.config/zellij/, and ~/.bashrc —
all of which are read-only or ephemeral inside the sandbox.

Run /ai-stack:sandbox from a regular terminal session (outside the sandbox).
```

### Step 1 — Detect current state

Check what is installed:

```bash
command -v agent-sandbox 2>/dev/null && echo "agent-sandbox: installed" || echo "agent-sandbox: missing"
test -f ~/.config/zellij/plugins/lince-dashboard.wasm && echo "lince-dashboard.wasm: installed" || echo "lince-dashboard.wasm: missing"
test -f ~/.config/lince-dashboard/config.toml && echo "lince-dashboard config: installed" || echo "lince-dashboard config: missing"
```

Determine mode (when no argument is given):
- All three present → **update mode** (inform the user)
- None present → **install mode** (inform the user)
- Mixed → report which are installed/missing, ask: `Install missing components (i) or update what's installed (u)? [i/u]:`

If an argument was given: `install` → install mode, `update` → update mode.

### Step 2 — Locate lince source

The skill base directory is shown at invocation time in the header line:
`Base directory for this skill: /path/to/plugins/ai-stack/skills/sandbox`

Use that path to compute the repo root (4 levels up) and check candidates:

```bash
SKILL_BASE="<skill-base-dir from invocation header>"
for candidate in \
    "$(cd "$SKILL_BASE/../../../../lince" 2>/dev/null && pwd)" \
    "$(pwd)/lince" \
    "$HOME/lince"; do
    [ -f "$candidate/quickstart.sh" ] && echo "FOUND: $candidate" && break
done
```

If a candidate is found, confirm with the user:
```
Found lince at: /path/to/lince
Use this path? [Y/n]:
```

If no candidate is found, ask:
```
Could not find lince locally.
Please provide the path to your lince checkout:
Path:
```

Verify the provided path has `quickstart.sh` before continuing.

### Step 3 — Check prerequisites

Detect OS:
```bash
uname -s
```

Run all checks:
```bash
# Python 3.11+
python3 -c "import sys; v=sys.version_info; print('python3:', str(v.major)+'.'+str(v.minor), 'OK' if v >= (3,11) else 'NEED 3.11+')" 2>/dev/null || echo "python3: MISSING"

# git
command -v git >/dev/null 2>&1 && git --version || echo "git: MISSING"

# zellij
command -v zellij >/dev/null 2>&1 && zellij --version || echo "zellij: MISSING"

# rustup
command -v rustup >/dev/null 2>&1 && rustup --version || echo "rustup: MISSING"

# wasm32-wasip1 target
rustup target list --installed 2>/dev/null | grep -q wasm32-wasip1 && echo "wasm32-wasip1: OK" || echo "wasm32-wasip1: MISSING"

# bubblewrap (Linux only)
[ "$(uname -s)" = "Linux" ] && { command -v bwrap >/dev/null 2>&1 && bwrap --version || echo "bubblewrap: MISSING"; }

# nono
command -v nono >/dev/null 2>&1 && echo "nono: $(nono --version 2>/dev/null | head -1)" || echo "nono: not installed"
```

Display results with install hints:

| Tool | Linux | macOS |
|---|---|---|
| python3 | `sudo dnf install python3` / `sudo apt install python3.11` | `brew install python@3.11` |
| git | `sudo dnf install git` / `sudo apt install git` | `brew install git` |
| zellij | `sudo dnf install zellij` or github.com/zellij-org/zellij releases | `brew install zellij` |
| rustup | `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \| sh` | same |
| wasm32-wasip1 | `rustup target add wasm32-wasip1` | same |
| bubblewrap | `sudo dnf install bubblewrap` / `sudo apt install bubblewrap` | N/A (Linux only) |
| nono | `cargo install nono-cli` | `brew install nono` |

If a blocking prerequisite is missing (no sandbox backend on Linux, no rustup), warn and ask:
```
⚠ Missing required tools above. Continue anyway? [y/N]:
```

### Step 4A — Install mode

Run the lince quickstart installer:

```bash
bash <lince-path>/quickstart.sh
```

The interactive TUI handles all decisions (sandbox backend selection, agent selection, VoxCode, WASM build, aliases). Do not ask additional questions — let the installer drive.

### Step 4B — Update mode

Ask which components to update:

```
Components to update:
  1) agent-sandbox
  2) lince-dashboard
  3) both [default]

Choice [3]:
```

Run the appropriate updater(s):
- Choice `1` or `agent-sandbox`: `bash <lince-path>/sandbox/update.sh`
- Choice `2` or `lince-dashboard`: `bash <lince-path>/lince-dashboard/update.sh`
- Choice `3` or empty: run both in sequence

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
