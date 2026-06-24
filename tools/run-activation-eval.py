#!/usr/bin/env python3
"""tools/run-activation-eval.py <eval-name>

Activation eval runner — tests whether Claude would invoke the right skill
given a natural language prompt.

Outputs JSON to stdout for promptfoo exec provider:
  {"output": "<claude text>", "invoked_skill": "<skill name or none>"}

Unlike run-skill.py (which tests skill *execution*), this tests skill
*activation*: does the model recognise when a skill should be invoked?
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

CLAUDE_TIMEOUT = 120
REPO_ROOT = Path(__file__).resolve().parent.parent


def run_claude(claude_cmd: list[str], retries: int = 2, retry_delay: int = 5) -> str:
    for attempt in range(retries + 1):
        proc = subprocess.Popen(
            claude_cmd,
            cwd=REPO_ROOT,
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

        if attempt < retries:
            time.sleep(retry_delay)

    raise RuntimeError("Claude exited 0 but produced no output after retries")


def die(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)


def discover_skills() -> dict[str, str]:
    """Read all SKILL.md frontmatter descriptions from the repo.

    Returns a dict mapping "plugin:skill" to description.
    """
    skills: dict[str, str] = {}
    plugins_dir = REPO_ROOT / "plugins"
    for plugin_dir in sorted(plugins_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue
        skills_dir = plugin_dir / "skills"
        if not skills_dir.is_dir():
            continue
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            desc = extract_description(skill_md)
            if desc:
                skill_name = f"{plugin_dir.name}:{skill_dir.name}"
                skills[skill_name] = desc
    return skills


def extract_description(path: Path) -> str:
    """Extract the description field from SKILL.md YAML frontmatter."""
    text = path.read_text()
    if not text.startswith("---"):
        return ""
    end = text.find("---", 3)
    if end == -1:
        return ""
    frontmatter = text[3:end]
    # Handle both single-line and multi-line (folded '>-') YAML descriptions
    match = re.search(r"^description:\s*>-\s*\n((?:\s+.+\n?)+)", frontmatter, re.MULTILINE)
    if match:
        lines = match.group(1).strip().splitlines()
        return " ".join(line.strip() for line in lines)
    match = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return ""


def build_prompt(user_message: str, skills: dict[str, str]) -> str:
    """Build the activation-test prompt."""
    listing = "\n".join(f"- {name}: {desc}" for name, desc in skills.items())
    return (
        "You are an AI assistant with the following skills available:\n\n"
        f"{listing}\n\n"
        "A user sends you this message:\n\n"
        f'"{user_message}"\n\n'
        "Which ONE skill would you invoke to handle this request? "
        "Reply with ONLY the skill name (e.g. track:jira) on a single line. "
        "If no skill applies, reply with: none"
    )


def extract_skill(output: str) -> str:
    """Extract the skill name from Claude's response."""
    cleaned = output.strip().lower()
    # Look for a plugin:skill pattern anywhere in the output
    match = re.search(r"\b([a-z][\w-]*:[a-z][\w-]*)\b", cleaned)
    if match:
        return match.group(1)
    if "none" in cleaned:
        return "none"
    return "unknown"


def main() -> None:
    if len(sys.argv) < 2:
        die("usage: run-activation-eval.py <eval-name> [scenario]")

    scenario = sys.argv[2] if len(sys.argv) > 2 else "default"

    # The scenario var is the user message, passed by promptfoo
    user_message = scenario

    skills = discover_skills()
    if not skills:
        die("No skills discovered — check plugins/*/skills/*/SKILL.md")

    prompt = build_prompt(user_message, skills)

    claude_cmd = [
        "claude", "-p", prompt,
        "--dangerously-skip-permissions",
    ]

    try:
        raw_output = run_claude(claude_cmd)
    except RuntimeError as e:
        raw_output = f"ERROR: {e}"

    invoked = extract_skill(raw_output)

    print(json.dumps({"output": raw_output, "invoked_skill": invoked}))


if __name__ == "__main__":
    main()
