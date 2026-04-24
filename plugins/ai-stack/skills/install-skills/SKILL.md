---
description: Install bare skills into user or project scope.
argument-hint: "[skill-name|all]"
---

# /ai-stack:install-skills

## Synopsis

```
/ai-stack:install-skills                    ← interactive picker
/ai-stack:install-skills n8n-skills         ← install specific skill
/ai-stack:install-skills all                ← install all skills
```

---

## Available skills

Add entries to `plugins/ai-stack/reference/skills.yaml` to extend this list.

| Skill | Source | Version |
|---|---|---|
| `template-slide-deck` | `toddward/claude-skills-playground` @ `template-slide-deck` | `main` |
| `n8n-skills` | `czlonkowski/n8n-skills` | `main` |

---

## Process

1. Check installation status for each skill:
   - **user**: `~/.claude/skills/<name>` exists
   - **project**: `.claude/skills/<name>` exists in the current directory

2. Present skills with status:

   ```
   Available skills:
   1. template-slide-deck   [not installed]
   2. n8n-skills            [installed: user]
   ```

3. If an argument was provided, use it to select skills; otherwise present the
   numbered menu and ask the user to pick by number (comma-separated, `all`, or `none` to exit).

4. **Always ask for scope before installing** — even if only one skill is selected.
   Present this exact prompt to the user:

   ```
   Install scope:
     u) user    — available in all projects (default)
     p) project — committed to git and shared with the team

   Scope [u/p, default: u]:
   ```

   Map input: `u`/`user` → `user`, `p`/`project` → `project`.
   Empty input defaults to `user`.

5. For each selected skill, install via sparse git checkout:

   ```bash
   tmpdir=$(mktemp -d)
   git clone --depth 1 --filter=blob:none --sparse --branch <version> \
       https://github.com/<source> "$tmpdir"
   # if path is set:
   git -C "$tmpdir" sparse-checkout set <path>
   mkdir -p <target>
   cp -r "$tmpdir/<path>/." <target>/
   rm -rf "$tmpdir"
   ```

   Where `<target>` is `~/.claude/skills/<name>` for user scope, or
   `.claude/skills/<name>` for project scope.

6. Confirm each skill installed successfully.
