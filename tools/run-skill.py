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

def die(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)


def setup_scenario(skill: str, scenario: str, eval_dir: Path) -> None:
    key = f"{skill}/{scenario}"
    env_src = REPO_ROOT / ".env"
    compose_src = REPO_ROOT / "compose.yaml"
    env_example_src = REPO_ROOT / ".claude/skills/ai-stack/reference/env.example"

    if key == "up/fresh":
        shutil.copy(env_src, eval_dir / ".env")
    elif key == "up/no-env":
        pass
    elif key == "up/existing-compose":
        # Seed with valid compose.yaml plus a sentinel comment so we can detect overwrites.
        # Using real compose so `compose up -d` succeeds and the skill can show UP summary.
        sentinel = "# SENTINEL-existing-compose\n"
        (eval_dir / "compose.yaml").write_text(sentinel + compose_src.read_text())
        shutil.copy(env_src, eval_dir / ".env")
    elif key == "up/placeholder-env":
        shutil.copy(env_example_src, eval_dir / ".env")
    elif key == "down/has-compose":
        shutil.copy(compose_src, eval_dir / "compose.yaml")
        shutil.copy(env_src, eval_dir / ".env")
    elif key == "down/no-compose":
        pass
    elif key == "down/already-stopped":
        shutil.copy(compose_src, eval_dir / "compose.yaml")
        shutil.copy(env_src, eval_dir / ".env")
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
    else:
        die(f"Unknown scenario: {key}")


def collect_state(eval_dir: Path) -> dict:
    def read(path: Path) -> str:
        try:
            return path.read_text()
        except FileNotFoundError:
            return ""

    return {
        "compose_exists":   (eval_dir / "compose.yaml").exists(),
        "env_exists":       (eval_dir / ".env").exists(),
        "claude_md_exists": (eval_dir / "CLAUDE.md").exists(),
        "agents_md_exists": (eval_dir / "AGENTS.md").exists(),
        "skill_dir_exists": (eval_dir / ".claude" / "skills").is_dir(),
        "compose_content":  read(eval_dir / "compose.yaml"),
        "env_content":      read(eval_dir / ".env"),
        "claude_md_content": read(eval_dir / "CLAUDE.md"),
    }


def main() -> None:
    if len(sys.argv) < 2:
        die("usage: run-skill.py <skill> [scenario]")

    skill = sys.argv[1]
    scenario = sys.argv[2] if len(sys.argv) > 2 else "default"

    with tempfile.TemporaryDirectory() as tmp:
        eval_dir = Path(tmp)

        # For non-bootstrap skills: copy .claude/skills into eval_dir so Claude
        # discovers the repo's skill files without also seeing REPO_ROOT's other
        # files (compose.yaml, .env, etc.) which would confuse existence checks.
        if skill != "bootstrap":
            shutil.copytree(
                str(REPO_ROOT / ".claude" / "skills"),
                str(eval_dir / ".claude" / "skills"),
                symlinks=False,
                dirs_exist_ok=True,
            )

        setup_scenario(skill, scenario, eval_dir)

        args = " force" if scenario == "force" else ""
        work_dir = REPO_ROOT if skill == "bootstrap" else eval_dir
        add_dir = REPO_ROOT if skill == "bootstrap" else eval_dir

        claude_cmd = [
            "claude", "-p", f"/ai-stack:{skill}{args}",
            "--dangerously-skip-permissions",
            "--add-dir", str(add_dir),
        ]

        try:
            claude_out = run_claude(claude_cmd, work_dir)
        except RuntimeError as e:
            claude_out = f"ERROR: {e}"

        state = collect_state(eval_dir)

    print(json.dumps({"output": claude_out, "state": state}))


if __name__ == "__main__":
    main()
