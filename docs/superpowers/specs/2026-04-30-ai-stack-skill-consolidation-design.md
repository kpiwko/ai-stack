# Design: ai-stack Skill Consolidation

**Date:** 2026-04-30  
**Status:** Approved

## Problem

The ai-stack plugin has grown a set of overlapping skills that are hard to remember and partly redundant:

- `add-entry`, `add-service`, `add-workflow` — three separate "add something" skills
- `install-mcps`, `install-plugins`, `install-skills` — three separate install skills alongside `bootstrap`
- `mcp-atlassian` is registered as a local HTTP MCP but the official `atlassian` Claude plugin (cloud-hosted, no local server required) is now preferred

## Goals

1. Replace `mcp-atlassian` MCP with `atlassian@claude-plugins-official` plugin
2. Track all 4 LSP plugins in `plugins.yaml` (they are now official plugins, not CLI installs)
3. Consolidate registry management into a single `modify` skill (add/update/remove)
4. Consolidate all setup into `bootstrap` (absorb `install-mcps`, `install-plugins`, `install-skills`)
5. Delete obsolete skills: `add-service`, `add-workflow`, `install-mcps`, `install-plugins`, `install-skills`

## Out of Scope

- No changes to `sandbox` skill
- No changes to `mcp/` service directories
- No changes to other plugins (dev, track, quarterly)

---

## Section 1 — Registry changes

### `plugins/ai-stack/reference/plugins.yaml`

Add the following entries:

```yaml
# LSP plugins (replacing CLI-installed LSP servers)
- name: gopls-lsp
  source: claude-plugins-official
- name: pyright-lsp
  source: claude-plugins-official
- name: typescript-lsp
  source: claude-plugins-official
- name: rust-analyzer-lsp
  source: claude-plugins-official

# Atlassian (replaces mcp-atlassian MCP)
- name: atlassian
  source: claude-plugins-official
```

### `plugins/ai-stack/reference/mcps.yaml`

Remove the `mcp-atlassian` entry. All other entries remain unchanged.

---

## Section 2 — Skill deletions

Delete these skill directories entirely:

- `plugins/ai-stack/skills/install-mcps/`
- `plugins/ai-stack/skills/install-plugins/`
- `plugins/ai-stack/skills/install-skills/`
- `plugins/ai-stack/skills/add-service/`
- `plugins/ai-stack/skills/add-workflow/`

---

## Section 3 — `add-entry` → `modify`

Rename `plugins/ai-stack/skills/add-entry/` to `plugins/ai-stack/skills/modify/`.

### New synopsis

```
/ai-stack:modify plugin add      ← add a plugin to the registry
/ai-stack:modify plugin update   ← update an existing plugin entry
/ai-stack:modify plugin remove   ← remove a plugin entry
/ai-stack:modify skill add|update|remove
/ai-stack:modify mcp add|update|remove
/ai-stack:modify                 ← interactive: ask type then operation
```

### Operations

**add** — same as current `add-entry` behavior: gather fields, preview, write to YAML, bump minor version.

**update** — find existing entry by name, display current values, gather changed fields, show diff preview, write, bump patch version.

**remove** — find entry by name, display it, ask for confirmation, delete from YAML, bump patch version.

All three operations apply to all three registry types: `plugin`, `skill`, `mcp`.

### Built-in plugin table

The hardcoded ai-stack marketplace plugin table (previously in `install-plugins/SKILL.md`) moves inline into `modify/SKILL.md` since `install-plugins` is deleted.

### Duplicate detection

- **add**: if entry already exists, show it and ask: update it or cancel?
- **update/remove**: if entry not found, show error and exit.

### Version bumping

- New entry added → minor bump (e.g. `0.5.0` → `0.6.0`)
- Entry updated or removed → patch bump (e.g. `0.5.0` → `0.5.1`)

---

## Section 4 — `bootstrap` absorbs install-*

Bootstrap becomes the single "set this machine up" command covering all setup steps.

### New flow

1. **Prerequisites check** — `go`, `node` (fail fast if missing)
2. **Runtimes / package managers** — `uv`, `pnpm`, `rustup` (install if absent)
3. **LSP plugins** — `claude plugin install <name>@claude-plugins-official` for all 4 LSPs
4. **Plugins** — `claude plugin install` for each entry in `plugins.yaml`
5. **Skills** — sparse git checkout for each entry in `skills.yaml`
6. **MCPs** — `claude mcp add` for each entry in `mcps.yaml`
7. **Summary table** — one row per item, status: `ok` / `installed` / `already installed` / `FAILED`

### `bootstrap.yaml` changes

The `languages` section drops `install` commands for gopls, pyright, typescript-language-server, and rust-analyzer — those are now handled by the LSP plugin step.

Add three new top-level sections that reference the existing YAML files:

```yaml
plugins: plugins/ai-stack/reference/plugins.yaml
skills:  plugins/ai-stack/reference/skills.yaml
mcps:    plugins/ai-stack/reference/mcps.yaml
```

Bootstrap reads these files at runtime to know what to install/register.

### Scope handling

- Plugins and skills: always install at `user` scope (bootstrap is a machine-setup command, not project-scoped)
- MCPs: use the `scope` field from `mcps.yaml` (same as current `install-mcps` behavior)

### Failure handling

A failure in any step does not stop the rest. Each item is recorded individually in the summary. Prerequisites (`go`, `node`) are still fail-fast.

---

## Section 5 — `CLAUDE.md` skill table

Update the ai-stack skill table to:

| Skill | When to use |
|---|---|
| `/ai-stack:bootstrap` | Full machine setup (runtimes, LSPs, plugins, skills, MCPs) |
| `/ai-stack:modify` | Add, update, or remove a plugin/skill/MCP in the registry |
| `/ai-stack:sandbox` | Install or update the LINCE toolkit |

Remove rows for: `add-entry`, `add-service`, `add-workflow`, `install-plugins`, `install-skills`, `install-mcps`.

---

## Version bump

The plugin version in `plugins/ai-stack/.claude-plugin/plugin.json` gets a minor bump at the end:  
`0.5.0` → `0.6.0`

This covers: new entries in plugins.yaml, removal from mcps.yaml, skill renames/deletions, and CLAUDE.md update.
