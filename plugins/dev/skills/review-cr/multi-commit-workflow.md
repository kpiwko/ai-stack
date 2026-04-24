# Multi-Commit Amendment Workflow

Used by Phase 4 of `/dev:review-cr` when N > 1 commits are in the review range.

## Overview

Each commit in the range gets its own `CodeRabbit-Review` trailer reflecting findings
**attributed to that commit**. The amendment uses interactive rebase driven by a
`GIT_SEQUENCE_EDITOR` script so each commit's message is updated atomically.

## Step-by-Step

### 1. Collect per-commit attribution

From Phase 2, each finding was attributed to a commit SHA via:
```bash
git log --oneline -1 HEAD~N..HEAD -- <file>
```

Build a map: `{sha → findings}` and `{sha → fixes applied}`.

### 2. Stage all modified files

```bash
git add <all files modified during Phase 3>
```

Warn the user if `git status` shows unstaged changes unrelated to the review.

### 3. Write per-commit message files

For each SHA in the range (oldest to newest):

1. Get original message: `git log --format=%B -n 1 <sha>`
2. Append trailer:
   ```
   <original message>

   CodeRabbit-Review: reviewed with coderabbit-cli
   - [✅] fix - <description>
   - [❌] skip - <reason>
   - [👌] no issues identified

   Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
   ```
3. Write to `/tmp/cr_msg_<sha>.txt`.

### 4. Generate the sequence editor script

Write `scripts/cr_seq_editor.py` to `/tmp/cr_seq_editor.py`, substituting
`COMMIT_TO_TMPFILE` with the actual `{sha: tmpfile}` pairs.

### 5. Run the rebase

```bash
GIT_SEQUENCE_EDITOR="python3 /tmp/cr_seq_editor.py" git rebase -i HEAD~N
```

### 6. Verify

```bash
git log --oneline HEAD~N..HEAD
git log --format=%B -n 1 HEAD~1
```

SHAs change after rebase — use relative refs or re-run `git log`.

## Attribution Rules

| Situation | Trailer line |
|---|---|
| Fix applied to originating commit's file | `[✅] fix - <description>` |
| Finding skipped | `[❌] skip - <reason>` |
| No findings for this commit | `[👌] no issues identified` |

## Error Handling

- **Merge commits in range**: skip — cannot be rebased safely.
- **Rebase conflict**: stop and tell the user; do not proceed.
- **Cleanup**: remove `/tmp/cr_msg_*.txt` and `/tmp/cr_seq_editor.py` after success.
