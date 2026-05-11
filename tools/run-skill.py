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
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def die(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)


def setup_scenario(skill: str, scenario: str, eval_dir: Path) -> None:
    key = f"{skill}/{scenario}"
    env_src = REPO_ROOT / ".env"
    compose_src = REPO_ROOT / "compose.yaml"
    env_example_src = REPO_ROOT / "plugins/ai-stack/reference/env.example"

    if key == "up/fresh":
        shutil.copy(env_src, eval_dir / ".env")
    elif key == "up/no-env":
        pass
    elif key == "up/existing-compose":
        (eval_dir / "compose.yaml").write_text("original")
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
        setup_scenario(skill, scenario, eval_dir)

        args = " force" if scenario == "force" else ""
        work_dir = REPO_ROOT if skill == "bootstrap" else eval_dir

        claude_cmd = [
            "claude", "-p", f"/ai-stack:{skill}{args}",
            "--dangerously-skip-permissions",
            "--add-dir", str(Path.home() / ".claude"),
        ]
        if skill == "bootstrap":
            claude_cmd += ["--add-dir", str(REPO_ROOT)]

        result = subprocess.run(
            claude_cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
        )
        claude_out = result.stdout + result.stderr

        state = collect_state(eval_dir)

    print(json.dumps({"output": claude_out, "state": state}))


if __name__ == "__main__":
    main()
