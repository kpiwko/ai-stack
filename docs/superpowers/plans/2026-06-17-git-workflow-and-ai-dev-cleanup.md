# Git Workflow Skill & ai-dev Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Codify git workflow conventions in AGENTS.md, create a `dev:git-workflow` skill for fork-aware PR-gated development (GitHub + GitLab), add evals, update README, and remove the ai-dev plugin. The AGENTS.md rules are written so that any skill (including superpowers like `finishing-a-development-branch`) naturally follows them — no prescriptive "use superpowers" directives in the git rules.

**Architecture:** Four repo changes + one user-side cleanup: (1) AGENTS.md section 7 with static git rules, (2) `dev:git-workflow` skill with two modes (`start` / `pr`), (3) evals for the new skill, (4) README update, (5) user disables ai-dev plugin themselves. The ai-dev plugin has zero footprint in this repo (not in `plugins.yaml`, `bootstrap.yaml`, or any reference file) — removal is purely a user settings change.

**Tech Stack:** Shell (git, gh, glab), Claude Code skills (SKILL.md format), promptfoo evals

---

## File Structure

| File | Responsibility |
|---|---|
| `AGENTS.md` | Static git conventions — remote naming, approval gates, commit rules |
| `plugins/dev/skills/git-workflow/SKILL.md` | Actionable workflow — branch setup, platform detection, PR creation with checkpoints |
| `plugins/dev/evals/promptfooconfig-git-workflow.yaml` | Eval scenarios for the skill |
| `plugins/dev/.claude-plugin/plugin.json` | Bump version, update description |
| `README.md` | Add git-workflow to capabilities list |
| `CLAUDE.md` | Add `/dev:git-workflow` to skill table |
| `plugins/ai-stack/reference/CLAUDE.md` | Add `/dev:git-workflow` to skill table (project-init template) |

User-side (not in repo):
| Action | How |
|---|---|
| Disable ai-dev plugin | `claude plugin uninstall ai-dev@ai-dev-marketplace` |
| Remove ai-dev marketplace | Remove `ai-dev-marketplace` from `extraKnownMarketplaces` in `~/.claude/settings.json` |

---

### Task 1: Add git workflow conventions to AGENTS.md

These are static rules that every agent and skill must follow — including superpowers skills like `finishing-a-development-branch` and `requesting-code-review`. By placing rules here, those skills naturally absorb them without needing to reference superpowers explicitly from the git rules.

**Files:**
- Modify: `AGENTS.md` (add new section 7 after section 6)

- [ ] **Step 1: Add section "7. Git Workflow" to AGENTS.md**

Insert after the existing section 6 (Skill Dev & Eval Workflow), before the closing of the file:

```markdown
---

## 7. Git Workflow

### Remotes

- The user's own repository (or fork) is always `origin`.
- If the repository is a fork, the original (upstream) repo is `upstream`.
- Never rename or reorder these. If the current setup doesn't match, flag it
  to the user rather than fixing silently.

### Branching

- All work happens on a feature branch, never directly on main/master/default.
- Feature branches are based on a freshly pulled default branch.
  - Single-remote: `git pull origin main`
  - Fork: sync `origin/main` with `upstream/main` first, then branch.
- Branch naming: `<type>/<short-description>` (e.g. `feat/git-workflow-skill`,
  `fix/auth-header`). Types match conventional commit types.

### Committing

- Follow Conventional Commits (section 5).
- Multiple small commits during work are fine — the user may reorganise them
  into logical groups before the PR (not necessarily a single squash).
- After completing work, always show `git diff <default-branch>..HEAD --stat`
  and the commit log, then wait for user acknowledgement before proceeding.

### Pushing & PRs

- **Never push or create a PR/MR without explicit user approval.**
- When ready to push, show a summary: branch name, commit count, diff stat.
- Before creating a PR/MR, show the proposed title and body for user review.
- PRs/MRs target `origin` by default (the user's remote), not `upstream`,
  unless the user explicitly says otherwise.
- Use `gh` for GitHub repos, `glab` for GitLab repos. Detect which platform
  by checking remote URLs (`git remote -v`).
```

- [ ] **Step 2: Verify the edit**

```bash
grep -n "## 7. Git Workflow" AGENTS.md
```

Expected: line found in AGENTS.md.

- [ ] **Step 3: Commit**

```bash
git add AGENTS.md
git commit -m "docs: add git workflow conventions to AGENTS.md"
```

---

### Task 2: Create the git workflow skill

This is the actionable skill that implements the full lifecycle. It's invoked when starting feature work or when preparing a PR/MR. It builds on the AGENTS.md rules but adds the step-by-step process with platform detection and user checkpoints.

**Files:**
- Create: `plugins/dev/skills/git-workflow/SKILL.md`

- [ ] **Step 1: Create the skill directory**

```bash
mkdir -p plugins/dev/skills/git-workflow
```

- [ ] **Step 2: Write the skill**

Create `plugins/dev/skills/git-workflow/SKILL.md` with this content:

````markdown
---
description: "Start feature work or prepare a PR/MR. Detects GitHub/GitLab, handles forks, enforces approval checkpoints."
argument-hint: "[start|pr]"
---

# /dev:git-workflow

## Synopsis

```
/dev:git-workflow start [branch-name]   # set up a feature branch
/dev:git-workflow pr                    # prepare and create PR/MR
```

Two modes: **start** sets up the working branch; **pr** prepares the pull/merge request.
If no argument is given, infer from context (no commits beyond default branch → start;
commits exist → pr).

**Announce at start:** "Using git-workflow to [set up a feature branch / prepare a PR]."

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

## Red Flags — Never Do

- Push without showing diff and getting approval
- Create PR/MR without showing the proposed message first
- Target `upstream` without explicit user request
- Commit directly to the default branch
- Force-push without explicit user request
- Assume platform — always detect from remotes
- Squash all commits into one without asking — user may want logical groups
````

- [ ] **Step 3: Verify the skill parses correctly**

```bash
head -5 plugins/dev/skills/git-workflow/SKILL.md
ls -la plugins/dev/skills/git-workflow/
```

Expected: frontmatter with `description:` and `argument-hint:` visible.

- [ ] **Step 4: Commit**

```bash
git add plugins/dev/skills/git-workflow/SKILL.md
git commit -m "feat(dev): add git-workflow skill for branch and PR lifecycle"
```

---

### Task 3: Add evals for the git-workflow skill

The dev plugin currently has no evals directory. Create one following the same pattern as `plugins/ai-stack/evals/`. The git-workflow skill runs in a real git repo, so evals need a temp repo with remotes configured.

**Files:**
- Create: `plugins/dev/evals/promptfooconfig-git-workflow.yaml`
- Modify: `tools/run-skill.py` (add `git-workflow` scenario setup and state collection)

- [ ] **Step 1: Read `tools/run-skill.py` to understand current scenario setup**

```bash
cat tools/run-skill.py
```

Understand the `setup_scenario()` and `collect_state()` functions, and how new skills are added.

- [ ] **Step 2: Add git-workflow scenarios to `tools/run-skill.py`**

Add to `setup_scenario()`:

```python
elif skill == "git-workflow":
    if scenario in ("start-single", "start-fork", "pr-single"):
        # Create a bare git repo to act as "origin"
        origin_bare = work_dir / "origin.git"
        subprocess.run(["git", "init", "--bare", str(origin_bare)], check=True)

        # Init the working repo
        subprocess.run(["git", "init", str(work_dir / "repo")], check=True)
        repo = work_dir / "repo"
        subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", str(origin_bare)], check=True)

        # Create an initial commit so we have a default branch
        (repo / "README.md").write_text("# Test repo\n")
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"], check=True)
        subprocess.run(["git", "-C", str(repo), "push", "-u", "origin", "main"], check=True)

    if scenario == "start-fork":
        # Add an upstream remote
        upstream_bare = work_dir / "upstream.git"
        subprocess.run(["git", "init", "--bare", str(upstream_bare)], check=True)
        repo = work_dir / "repo"
        subprocess.run(["git", "-C", str(repo), "remote", "add", "upstream", str(upstream_bare)], check=True)
        subprocess.run(["git", "-C", str(repo), "push", "upstream", "main"], check=True)

    if scenario == "pr-single":
        repo = work_dir / "repo"
        # Create a feature branch with a commit
        subprocess.run(["git", "-C", str(repo), "checkout", "-b", "feat/test-feature"], check=True)
        (repo / "feature.txt").write_text("new feature\n")
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "feat: add test feature"], check=True)
```

Add to `collect_state()`:

```python
if skill == "git-workflow":
    repo = work_dir / "repo"
    if repo.exists():
        branch = subprocess.run(
            ["git", "-C", str(repo), "branch", "--show-current"],
            capture_output=True, text=True
        ).stdout.strip()
        state["current_branch"] = branch

        remotes = subprocess.run(
            ["git", "-C", str(repo), "remote", "-v"],
            capture_output=True, text=True
        ).stdout.strip()
        state["remotes"] = remotes

        log = subprocess.run(
            ["git", "-C", str(repo), "log", "--oneline", "-5"],
            capture_output=True, text=True
        ).stdout.strip()
        state["git_log"] = log
```

- [ ] **Step 3: Create the eval config**

Create `plugins/dev/evals/promptfooconfig-git-workflow.yaml`:

```yaml
description: /dev:git-workflow skill evals

prompts:
  - '{{scenario}}'

providers:
  - 'exec: python3 ../../../tools/run-skill.py git-workflow'

defaultTest:
  assert:
    - type: javascript
      value: |
        try { JSON.parse(output); return true; }
        catch(e) { return { pass: false, score: 0, reason: 'runner did not emit valid JSON' }; }

tests:
  - description: "start mode (single remote): detects platform and creates feature branch"
    vars:
      scenario: start-single
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          if (!/single.*remote|single/i.test(r.output))
            return { pass: false, score: 0, reason: 'did not detect single-remote topology' };
          if (!r.state.current_branch || r.state.current_branch === 'main')
            return { pass: false, score: 0, reason: 'still on main — feature branch not created' };
          return { pass: true, score: 1, reason: 'ok' };

  - description: "start mode (fork): detects upstream remote"
    vars:
      scenario: start-fork
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          if (!/fork|upstream/i.test(r.output))
            return { pass: false, score: 0, reason: 'did not detect fork topology' };
          return { pass: true, score: 1, reason: 'ok' };

  - description: "pr mode: shows diff and commit log before proceeding"
    vars:
      scenario: pr-single
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          if (!/diff|changes|stat/i.test(r.output))
            return { pass: false, score: 0, reason: 'diff stat not shown to user' };
          if (!/feat.*test.feature|commit/i.test(r.output))
            return { pass: false, score: 0, reason: 'commit log not shown' };
          return { pass: true, score: 1, reason: 'ok' };
```

- [ ] **Step 4: Commit**

```bash
git add plugins/dev/evals/promptfooconfig-git-workflow.yaml tools/run-skill.py
git commit -m "test(dev): add evals for git-workflow skill"
```

---

### Task 4: Update README and CLAUDE.md references

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Modify: `plugins/ai-stack/reference/CLAUDE.md`

- [ ] **Step 1: Add git-workflow to README**

In the "Getting started with Claude Code" section of `README.md`, after the line about bootstrap creating `.env`, add a brief mention. Find the paragraph that starts with "Bootstrap creates `.env`" and after that paragraph, add:

```markdown
**Git workflow:**

The `dev` plugin includes `/dev:git-workflow` for branch-based development with
PR/MR gates. It detects GitHub (`gh`) or GitLab (`glab`) automatically, handles
fork topologies, and enforces approval checkpoints before pushing or creating PRs.

```bash
/dev:git-workflow start feat/my-feature   # create a feature branch
/dev:git-workflow pr                      # prepare and submit PR/MR
```
```

- [ ] **Step 2: Add `/dev:git-workflow` to CLAUDE.md skill table**

In the "Skills & Multi-Agent Coordination" table in `CLAUDE.md`, add a row:

```markdown
| `/dev:git-workflow` | Start feature branch or prepare PR/MR |
```

- [ ] **Step 3: Add `/dev:git-workflow` to reference CLAUDE.md**

Same change in `plugins/ai-stack/reference/CLAUDE.md` — add the same row to its skill table.

- [ ] **Step 4: Commit**

```bash
git add README.md CLAUDE.md plugins/ai-stack/reference/CLAUDE.md
git commit -m "docs: add git-workflow skill to README and CLAUDE.md"
```

---

### Task 5: Update dev plugin metadata

**Files:**
- Modify: `plugins/dev/.claude-plugin/plugin.json`

- [ ] **Step 1: Bump version and update description**

Change version from `0.1.1` to `0.2.0` and update description:

```json
{
  "name": "dev",
  "description": "Developer workflow tools: code review via CodeRabbit CLI, git workflow with PR gates, language coding agents.",
  "version": "0.2.0",
  "author": {
    "name": "Karel Piwko"
  },
  "repository": "https://github.com/kpiwko/ai-stack"
}
```

- [ ] **Step 2: Commit**

```bash
git add plugins/dev/.claude-plugin/plugin.json
git commit -m "chore(dev): bump to 0.2.0, add git-workflow to description"
```

---

### Task 6: Final verification

- [ ] **Step 1: Verify all files are in place**

```bash
# Skill exists with correct frontmatter
head -5 plugins/dev/skills/git-workflow/SKILL.md

# AGENTS.md has section 7
grep -c "## 7. Git Workflow" AGENTS.md

# Evals exist
ls plugins/dev/evals/promptfooconfig-git-workflow.yaml

# Plugin version bumped
python3 -c "import json; print(json.load(open('plugins/dev/.claude-plugin/plugin.json'))['version'])"

# README mentions git-workflow
grep -c "git-workflow" README.md

# CLAUDE.md mentions git-workflow
grep -c "git-workflow" CLAUDE.md
```

Expected: all checks return 1 or show expected content.

- [ ] **Step 2: Show final diff**

```bash
git diff main..HEAD --stat
git log --oneline main..HEAD
```

Present to user for review before any push or PR.
