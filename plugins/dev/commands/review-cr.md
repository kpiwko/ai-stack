---
description: Run a CodeRabbit CLI review on committed changes, triage findings, apply fixes, and amend commits with review trailers.
argument-hint: "[N|branch]"
---

# /dev:review-cr

## Synopsis

```
/dev:review-cr [N | branch]
```

- Empty or `1` — review last 1 commit
- Integer `N` — review last N commits (base = `HEAD~N`)
- Branch name — use that branch as base (e.g. `/dev:review-cr main`)

Requires the `cr` CLI. Install from https://www.coderabbit.ai/cli if not found.

---

## Phase 1 — Run CodeRabbit

1. Parse `$ARGUMENTS` to determine base.
2. Show commits to be reviewed: `git log --oneline HEAD~N..HEAD`
3. Run: `cr review --type committed --base-commit HEAD~N --agent`
   - Branch base: `cr review --type committed --base <branch> --agent`
   - If `--agent` fails: retry with `--plain`

---

## Phase 2 — Present Findings

**Summary block:**
```
## CodeRabbit Review Summary
Files reviewed: <N>   Total findings: <N>
Severity: Critical <N>  High <N>  Medium <N>  Low/Info <N>
Overall: <one-line from CR output>
```

**Numbered findings** — attribute each to its originating commit:
```bash
git log --oneline -1 HEAD~N..HEAD -- <file>
```
If no commit in the range touched the file, attribute to HEAD.

```
## Findings

### [1] <severity> — <file>:<line>  [commit: <sha> <subject>]
**Issue:** <description>
**Suggestion:** <proposed fix>
```

After listing all findings, ask: which to fix? (`fix 1, 3` / `fix all` / `fix none`)

---

## Phase 3 — Apply Fixes

For each selected finding:
1. Read the file.
2. Apply the change precisely — no extra cleanup or refactoring.
3. Confirm: "Fixed [N]: <one-line description>."

Ask for clarification if a fix is ambiguous or conflicts with existing code.

---

## Phase 4 — Amend Commits

**Single commit (N = 1):** stage changed files and `git commit --amend`.

**Multi-commit (N > 1):** use the `GIT_SEQUENCE_EDITOR` rebase procedure with
`skills/review-cr/scripts/cr_seq_editor.py`. See `skills/review-cr/multi-commit-workflow.md`.

Append to each amended commit message:
```
CodeRabbit-Review: reviewed with coderabbit-cli
- [✅] fix - <description>
- [❌] skip - <reason>
- [👌] no issues identified
```

Each commit lists findings **attributed to that commit** — whether fixed in the
same commit or a later one. After amending, show: `git log --oneline HEAD~N..HEAD`

---

## Constraints

- Only amend commits within the reviewed range.
- Only apply fixes the user explicitly selected.
- Warn before staging if the working tree has unrelated uncommitted changes.
- Skip merge commits — cannot be rebased safely.
- Do not push to remote.
