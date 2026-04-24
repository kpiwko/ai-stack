---
description: Install bare skills from ai-stack.yaml into user, project, or local scope.
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

## Process

1. Fetch `ai-stack.yaml` from
   `https://raw.githubusercontent.com/kpiwko/ai-stack/main/ai-stack.yaml`

2. Check installation status for each skill:
   - **user**: `~/.claude/skills/<name>` exists
   - **project/local**: `.claude/skills/<name>` exists in the current directory

3. Present skills with status:

   ```
   Available skills:
   1. template-slide-deck   [not installed]
   2. n8n-skills            [installed: user]
   ```

4. If an argument was provided, use it to select skills; otherwise ask the user
   which to install (numbers comma-separated, or `all`).

5. Ask for scope:
   - **user** — `~/.claude/skills/<name>` (available in all sessions)
   - **project** — `.claude/skills/<name>` in current directory (shared via git)
   - **local** — `.claude/skills/<name>` in current directory (personal, not committed)

6. For each selected skill, install via sparse git checkout:

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
   `.claude/skills/<name>` for project/local scope.

7. Confirm each skill installed, then remind the user that **local** scope
   skills should be added to `.gitignore` if they should not be committed.
