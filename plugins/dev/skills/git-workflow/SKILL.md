---
description: "Start feature work, prepare a PR/MR, or review an existing PR/MR. Detects GitHub/GitLab, handles forks, enforces approval checkpoints."
argument-hint: "<start|pr|review> or describe what you need"
---

# /dev:git-workflow

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

**Prerequisites:** This skill requires AGENTS.md section 7 (Git Workflow) to be present
in the project. All remote naming, branching, and approval rules are defined there and
apply here.

---

## Step 0: Detect Environment

Run once at the beginning of either mode. Results are used throughout.

```bash
# Platform detection
REMOTES=$(git remote -v 2>/dev/null)

if echo "$REMOTES" | grep -q "github.com"; then
  PLATFORM="github"
  CLI="gh"
elif echo "$REMOTES" | grep -q "gitlab"; then
  PLATFORM="gitlab"
  CLI="glab"
else
  PLATFORM="unknown"
fi

# Fork detection
ORIGIN_URL=$(git remote get-url origin 2>/dev/null)
UPSTREAM_URL=$(git remote get-url upstream 2>/dev/null)

if [ -n "$UPSTREAM_URL" ]; then
  TOPOLOGY="fork"
else
  TOPOLOGY="single"
fi

# Default branch detection
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
if [ -z "$DEFAULT_BRANCH" ]; then
  DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | grep "HEAD branch" | awk '{print $NF}')
fi
if [ -z "$DEFAULT_BRANCH" ]; then
  DEFAULT_BRANCH="main"
fi
```

Report to user:

```
Platform:       {github|gitlab}     CLI: {gh|glab}
Topology:       {fork (origin + upstream) | single remote}
Default branch: {DEFAULT_BRANCH}
```

**If `PLATFORM` is `unknown`:** ask the user which platform this is.

**Sanity check:** if origin URL points to a well-known upstream org (not the user's
account), flag it — origin should be the user's fork, not the upstream repo.

---

## Mode: start

Set up a feature branch for new work.

### Step 1: Sync default branch

For single remote:

```bash
git checkout $DEFAULT_BRANCH
git pull origin $DEFAULT_BRANCH
```

For fork:

```bash
git checkout $DEFAULT_BRANCH
git fetch upstream
git merge upstream/$DEFAULT_BRANCH
git push origin $DEFAULT_BRANCH
```

### Step 2: Create feature branch

If branch name was provided as argument, use it. Otherwise, ask the user what
they're working on and suggest a name following `<type>/<short-description>`.

```bash
git checkout -b $BRANCH_NAME
```

### Step 3: Confirm ready

```
Branch '$BRANCH_NAME' created from '$DEFAULT_BRANCH'.
Ready to work.
```

---

## Mode: pr

Prepare and create a PR/MR with approval checkpoints.

### Step 1: Show diff for review

```bash
git diff $DEFAULT_BRANCH..HEAD --stat
git log --oneline $DEFAULT_BRANCH..HEAD
```

Present to user:

```
## Changes for review

**Branch:** $BRANCH_NAME → origin/$DEFAULT_BRANCH
**Commits:** N

[diff stat output]
[commit log]

Review the changes. Options:
  1. Continue to PR/MR creation
  2. Show full diff
  3. I need to make more changes
  4. Reorganise commits first
```

**Wait for user response before proceeding.**

If user picks option 4 (reorganise commits), help with interactive rebase. The
user may want to squash into logical groups — not necessarily a single commit.
Show the commit list and ask how they want to group them:

```bash
git log --oneline $DEFAULT_BRANCH..HEAD
```

Then guide the `git rebase -i $DEFAULT_BRANCH` accordingly.

### Step 2: Draft PR/MR message

Generate title and body from the commits and diff. Follow conventional commit
format for the title. Show to user:

```
## Proposed PR/MR

**Title:** <type>(<scope>): <description>

**Body:**
## Summary
<bullet points of what changed and why>

## Test plan
<how to verify the changes>

---

Edit the title/body, or approve to create the PR/MR.
```

**Wait for user approval before creating.**

### Step 3: Push and create PR/MR

```bash
git push -u origin $BRANCH_NAME
```

GitHub:

```bash
gh pr create --title "$TITLE" --body "$BODY" --base $DEFAULT_BRANCH
```

GitLab:

```bash
glab mr create --title "$TITLE" --description "$BODY" --target-branch $DEFAULT_BRANCH
```

PR/MR targets `origin` by default. If the user wants to target `upstream`
(e.g. contributing to an open-source project), they must say so explicitly —
then use `--repo` (gh) or `--repo` (glab) to target the upstream remote.

### Step 4: Report

```
PR/MR created: <URL>

Branch:  $BRANCH_NAME
Target:  origin/$DEFAULT_BRANCH
```

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

---

## Red Flags — Never Do

- Push without showing diff and getting approval
- Create PR/MR without showing the proposed message first
- Target `upstream` without explicit user request
- Commit directly to the default branch
- Force-push without explicit user request
- Assume platform — always detect from remotes
- Squash all commits into one without asking — user may want logical groups
- Submit a review or comment without showing it to the user first
- Check out a PR without telling the user which branch they were on
