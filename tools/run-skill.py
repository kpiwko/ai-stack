#!/usr/bin/env python3
"""tools/run-skill.py <skill> <scenario>

Outputs JSON to stdout for promptfoo exec provider:
  {"output": "<claude text>", "state": {<filesystem state>}}
"""
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CLAUDE_TIMEOUT = 300  # seconds


def run_claude(claude_cmd: list[str], work_dir: Path, retries: int = 2, retry_delay: int = 5) -> str:
    """Run claude, return combined stdout+stderr output.

    Retries only on the known transient condition: returncode 0 with no output,
    which happens when a prior Claude process hasn't released its session socket yet.
    Non-zero exit and timeout raise immediately without retrying.
    """
    for attempt in range(retries + 1):
        proc = subprocess.Popen(
            claude_cmd,
            cwd=work_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            stdout, _ = proc.communicate(timeout=CLAUDE_TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            raise RuntimeError(f"Claude timed out after {CLAUDE_TIMEOUT}s")

        output = stdout or ""

        if proc.returncode != 0:
            raise RuntimeError(f"Claude exited {proc.returncode}\n{output}")

        if output.strip():
            return output

        # returncode 0, no output — known transient; retry after a brief pause
        if attempt < retries:
            time.sleep(retry_delay)

    raise RuntimeError("Claude exited 0 but produced no output after retries")

REPO_ROOT = Path(__file__).resolve().parent.parent

SKILL_PLUGIN_MAP = {
    "git-workflow": ("dev", "dev"),
}

def die(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)


def setup_scenario(skill: str, scenario: str, eval_dir: Path) -> None:
    key = f"{skill}/{scenario}"
    env_src = REPO_ROOT / ".env"
    compose_src = REPO_ROOT / "compose.yaml"
    env_example_src = REPO_ROOT / "plugins" / "ai-stack" / "reference" / "env.example"

    def seed_dummy_cert(d: Path) -> None:
        certs_dir = d / "certs"
        certs_dir.mkdir(exist_ok=True)
        (certs_dir / "rds-combined-ca-bundle.pem").write_text("# dummy CA cert for eval\n")

    if key == "up/fresh":
        shutil.copy(env_src, eval_dir / ".env")
        seed_dummy_cert(eval_dir)
    elif key == "up/no-env":
        seed_dummy_cert(eval_dir)
    elif key == "up/existing-compose":
        sentinel = "# SENTINEL-existing-compose\n"
        (eval_dir / "compose.yaml").write_text(sentinel + compose_src.read_text())
        shutil.copy(env_src, eval_dir / ".env")
        seed_dummy_cert(eval_dir)
    elif key == "up/placeholder-env":
        shutil.copy(env_example_src, eval_dir / ".env")
        seed_dummy_cert(eval_dir)
    elif key == "down/has-compose":
        shutil.copy(compose_src, eval_dir / "compose.yaml")
        shutil.copy(env_src, eval_dir / ".env")
    elif key == "down/no-compose":
        pass
    elif key == "down/already-stopped":
        shutil.copy(compose_src, eval_dir / "compose.yaml")
        shutil.copy(env_src, eval_dir / ".env")
    elif key == "status/has-compose":
        shutil.copy(compose_src, eval_dir / "compose.yaml")
        shutil.copy(env_src, eval_dir / ".env")
    elif key == "status/no-compose":
        pass
    elif skill == "bootstrap":
        pass
    elif key == "project-init/empty":
        pass
    elif key == "project-init/existing-md":
        (eval_dir / "CLAUDE.md").write_text("existing content")
    elif key == "project-init/force":
        (eval_dir / "CLAUDE.md").write_text("old content")
    elif key == "project-init/optional-skill":
        pass
    elif skill == "git-workflow":
        _git = dict(check=True, capture_output=True)
        fake_gh = "https://github.com/test-user/test-repo.git"
        fake_upstream = "https://github.com/upstream-org/test-repo.git"
        if scenario in ("start-single", "start-fork", "pr-single", "review-list"):
            origin_bare = eval_dir / "origin.git"
            subprocess.run(["git", "init", "--bare", str(origin_bare)], **_git)

            repo = eval_dir / "repo"
            subprocess.run(["git", "init", str(repo)], **_git)
            subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", str(origin_bare)], **_git)

            (repo / "README.md").write_text("# Test repo\n")
            subprocess.run(["git", "-C", str(repo), "add", "."], **_git)
            subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"], **_git)
            subprocess.run(["git", "-C", str(repo), "push", "-u", "origin", "main"], **_git)

        if scenario == "start-fork":
            upstream_bare = eval_dir / "upstream.git"
            subprocess.run(["git", "init", "--bare", str(upstream_bare)], **_git)
            repo = eval_dir / "repo"
            subprocess.run(["git", "-C", str(repo), "remote", "add", "upstream", str(upstream_bare)], **_git)
            subprocess.run(["git", "-C", str(repo), "push", "upstream", "main"], **_git)

        if scenario == "pr-single":
            repo = eval_dir / "repo"
            subprocess.run(["git", "-C", str(repo), "checkout", "-b", "feat/test-feature"], **_git)
            (repo / "feature.txt").write_text("new feature\n")
            subprocess.run(["git", "-C", str(repo), "add", "."], **_git)
            subprocess.run(["git", "-C", str(repo), "commit", "-m", "feat: add test feature"], **_git)

        if scenario == "review-list":
            repo = eval_dir / "repo"
            subprocess.run(["git", "-C", str(repo), "checkout", "-b", "feat/other-work"], **_git)
            (repo / "other.txt").write_text("other work\n")
            subprocess.run(["git", "-C", str(repo), "add", "."], **_git)
            subprocess.run(["git", "-C", str(repo), "commit", "-m", "feat: other work"], **_git)
            subprocess.run(["git", "-C", str(repo), "push", "origin", "feat/other-work"], **_git)
            subprocess.run(["git", "-C", str(repo), "checkout", "main"], **_git)

        # After all local pushes, swap remote URLs to fake GitHub URLs so the
        # skill's platform detection sees "github.com" instead of a local path.
        if scenario in ("start-single", "start-fork", "pr-single", "review-list"):
            repo = eval_dir / "repo"
            subprocess.run(["git", "-C", str(repo), "remote", "set-url", "origin", fake_gh], **_git)
        if scenario == "start-fork":
            repo = eval_dir / "repo"
            subprocess.run(["git", "-C", str(repo), "remote", "set-url", "upstream", fake_upstream], **_git)
    else:
        die(f"Unknown scenario: {key}")


def collect_state(eval_dir: Path) -> dict:
    def read(path: Path) -> str:
        try:
            return path.read_text()
        except FileNotFoundError:
            return ""

    state = {
        "compose_exists":   (eval_dir / "compose.yaml").exists(),
        "env_exists":       (eval_dir / ".env").exists(),
        "certs_exists":     (eval_dir / "certs" / "rds-combined-ca-bundle.pem").exists(),
        "claude_md_exists": (eval_dir / "CLAUDE.md").exists(),
        "agents_md_exists": (eval_dir / "AGENTS.md").exists(),
        "skill_dir_exists": (eval_dir / ".claude" / "skills").is_dir(),
        "compose_content":  read(eval_dir / "compose.yaml"),
        "env_content":      read(eval_dir / ".env"),
        "claude_md_content": read(eval_dir / "CLAUDE.md"),
    }

    # Git workflow state
    repo = eval_dir / "repo"
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

    return state


def build_skill_prompt(skill: str, args: str) -> str:
    """Read SKILL.md from the repo and prepend the invocation context header.

    Passing the skill content directly as the -p prompt means evals work from
    local repo files without needing the plugin installed globally.
    """
    plugin_name, invocation_prefix = SKILL_PLUGIN_MAP.get(skill, ("ai-stack", "ai-stack"))
    skill_dir = REPO_ROOT / "plugins" / plugin_name / "skills" / skill
    skill_md = (skill_dir / "SKILL.md").read_text()
    invocation = f"/{invocation_prefix}:{skill}{args}"
    return f"Base directory for this skill: {skill_dir}\nInvoked as: {invocation}\n\n{skill_md}"


def main() -> None:
    if len(sys.argv) < 2:
        die("usage: run-skill.py <skill> [scenario]")

    skill = sys.argv[1]
    scenario = sys.argv[2] if len(sys.argv) > 2 else "default"

    with tempfile.TemporaryDirectory() as tmp:
        eval_dir = Path(tmp)

        setup_scenario(skill, scenario, eval_dir)

        scenario_args = {
            "force": " force",
            "start-single": " start feat/eval-test",
            "start-fork": " start feat/eval-test",
            "pr-single": " pr",
            "review-list": " review",
        }
        args = scenario_args.get(scenario, "")

        if skill == "bootstrap":
            # Bootstrap runs against real machine state. Pass SKILL.md directly
            # so evals work without the plugin installed globally.
            prompt = build_skill_prompt(skill, args)
            work_dir = REPO_ROOT
            claude_cmd = [
                "claude", "-p", prompt,
                "--dangerously-skip-permissions",
                "--add-dir", str(REPO_ROOT),
            ]
        else:
            # Non-bootstrap: pass SKILL.md content directly so evals work from local
            # repo files without the plugin being globally installed.
            # --add-dir eval_dir: file isolation (compose.yaml, .env, etc.)
            # --add-dir plugins/<plugin>: reference file access (../reference/ paths)
            prompt = build_skill_prompt(skill, args)
            work_dir = eval_dir
            # git-workflow runs inside the repo subdirectory
            if skill == "git-workflow":
                work_dir = eval_dir / "repo"
            plugin_name = SKILL_PLUGIN_MAP.get(skill, ("ai-stack",))[0]
            claude_cmd = [
                "claude", "-p", prompt,
                "--dangerously-skip-permissions",
                "--add-dir", str(eval_dir),
                "--add-dir", str(REPO_ROOT / "plugins" / plugin_name),
            ]

        try:
            claude_out = run_claude(claude_cmd, work_dir)
        except RuntimeError as e:
            claude_out = f"ERROR: {e}"

        state = collect_state(eval_dir)

    print(json.dumps({"output": claude_out, "state": state}))


if __name__ == "__main__":
    main()
