# Git Workflow: Review Mode & Flexible Argument Hint

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the git-workflow skill more discoverable by accepting natural language arguments ("new feature", "review PR") alongside explicit modes, and add a `review` mode for checking out and reviewing someone else's PR/MR.

**Architecture:** Two changes to the existing skill: (1) broaden the argument hint and inference logic so free-form input triggers the right mode, (2) add a `review` mode that checks out a PR/MR, shows the diff, and guides the user through a review workflow. The review mode reuses Step 0 (environment detection) and the same platform CLI tools (gh/glab). One new eval scenario covers the review mode.

**Tech Stack:** Shell (git, gh, glab), Claude Code skills (SKILL.md format), promptfoo evals

---

## File Structure

| File | Responsibility |
|---|---|
| `plugins/dev/skills/git-workflow/SKILL.md` | Add review mode, update argument-hint and inference |
| `plugins/dev/evals/promptfooconfig-git-workflow.yaml` | Add review eval scenario |
| `tools/run-skill.py` | Add review scenario setup |

---

### Task 1: Update SKILL.md — argument hint, inference, and review mode

**Files:**
- Modify: `plugins/dev/skills/git-workflow/SKILL.md`

- [ ] **Step 1: Update frontmatter**

Change:

```yaml
description: "Start feature work or prepare a PR/MR. Detects GitHub/GitLab, handles forks, enforces approval checkpoints."
argument-hint: "[start|pr]"
```

To:

```yaml
description: "Start feature work, prepare a PR/MR, or review an existing PR/MR. Detects GitHub/GitLab, handles forks, enforces approval checkpoints."
argument-hint: "<start|pr|review> or describe what you need"
```

- [ ] **Step 2: Update synopsis and inference logic**

Replace the Synopsis section with:

````markdown
## Synopsis

```
/dev:git-workflow start [branch-name]   # set up a feature branch
/dev:git-workflow pr                    # prepare and create PR/MR
/dev:git-workflow review [PR-number|URL] # check out and review a PR/MR
```

Three modes: **start** sets up the working branch; **pr** prepares the pull/merge
request; **review** checks out an existing PR/MR for review.

If no explicit mode is given, infer from context:
- Free-form like "new feature", "start work", branch name → **start**
- "submit", "open PR", "send for review" → **pr**
- PR/MR number, URL, or "review", "check PR" → **review**
- No commits beyond default branch → **start**
- Commits exist beyond default branch → **pr**

**Announce at start:** "Using git-workflow to [set up a feature branch / prepare a PR / review PR #N]."
````

- [ ] **Step 3: Add Mode: review section**

Insert after the existing "Mode: pr" section (after Step 4: Report, before "Red Flags — Never Do"):

````markdown
---

## Mode: review

Check out an existing PR/MR and guide the user through reviewing it.

### Step 1: Identify the PR/MR

If a PR number or URL was provided as argument, use it. Otherwise, list open PRs
and ask the user which one to review:

GitHub:

```bash
gh pr list --limit 10
```

GitLab:

```bash
glab mr list --per-page 10
```

### Step 2: Show PR/MR details

GitHub:

```bash
gh pr view $PR_NUMBER
gh pr diff $PR_NUMBER --stat
```

GitLab:

```bash
glab mr view $MR_NUMBER
glab mr diff $MR_NUMBER --stat
```

Present to user:

```
## PR/MR #N: <title>

**Author:** <author>
**Branch:** <head> → <base>
**Status:** <status>

[diff stat]

Options:
  1. Check out locally and review
  2. Show full diff here
  3. Add a comment / approve / request changes
```

**Wait for user response.**

### Step 3: Check out locally (if requested)

GitHub:

```bash
gh pr checkout $PR_NUMBER
```

GitLab:

```bash
glab mr checkout $MR_NUMBER
```

After checkout, show:

```
Checked out PR/MR #N locally on branch '<branch-name>'.

You can now:
- Browse the code, run tests, try it out
- When done, tell me to leave feedback or return to your branch
```

### Step 4: Leave feedback (if requested)

Help the user draft review comments. Show proposed comment/review before
submitting:

GitHub:

```bash
gh pr review $PR_NUMBER --approve --body "$COMMENT"
gh pr review $PR_NUMBER --request-changes --body "$COMMENT"
gh pr review $PR_NUMBER --comment --body "$COMMENT"
```

GitLab:

```bash
glab mr approve $MR_NUMBER
glab mr note $MR_NUMBER --message "$COMMENT"
```

**Wait for user approval before submitting any review or comment.**

### Step 5: Return to previous branch

After review is complete:

```bash
git checkout -
```

```
Returned to branch '<previous-branch>'.
Review of PR/MR #N complete.
```
````

- [ ] **Step 4: Update Red Flags section**

Add to the "Red Flags — Never Do" list:

```markdown
- Submit a review or comment without showing it to the user first
- Check out a PR without telling the user which branch they were on
```

- [ ] **Step 5: Commit**

```bash
git add plugins/dev/skills/git-workflow/SKILL.md
git commit -m "feat(dev): add review mode and flexible argument hint to git-workflow"
```

---

### Task 2: Add review eval scenario

**Files:**
- Modify: `tools/run-skill.py`
- Modify: `plugins/dev/evals/promptfooconfig-git-workflow.yaml`

- [ ] **Step 1: Read current eval files**

Read `tools/run-skill.py` and `plugins/dev/evals/promptfooconfig-git-workflow.yaml` to understand the existing git-workflow scenario setup.

- [ ] **Step 2: Add review scenario to `setup_scenario` in `tools/run-skill.py`**

In the `elif skill == "git-workflow":` block, the first `if` checks for scenarios in a tuple. Add `"review-list"` to that tuple so the base repo is created. Then add a new block after the `pr-single` block:

```python
        if scenario == "review-list":
            # Create a second branch with a commit to simulate an open PR
            repo = eval_dir / "repo"
            subprocess.run(["git", "-C", str(repo), "checkout", "-b", "feat/other-work"], check=True)
            (repo / "other.txt").write_text("other work\n")
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-m", "feat: other work"], check=True)
            subprocess.run(["git", "-C", str(repo), "push", "origin", "feat/other-work"], check=True)
            subprocess.run(["git", "-C", str(repo), "checkout", "main"], check=True)
```

- [ ] **Step 3: Add review test to promptfooconfig**

Append to the `tests:` list in `plugins/dev/evals/promptfooconfig-git-workflow.yaml`:

```yaml
  - description: "review mode: lists PRs or shows review guidance"
    vars:
      scenario: review-list
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          if (!/review|PR|MR|pull.request|merge.request/i.test(r.output))
            return { pass: false, score: 0, reason: 'no review-related output detected' };
          return { pass: true, score: 1, reason: 'ok' };
```

- [ ] **Step 4: Commit**

```bash
git add tools/run-skill.py plugins/dev/evals/promptfooconfig-git-workflow.yaml
git commit -m "test(dev): add review eval scenario for git-workflow"
```
