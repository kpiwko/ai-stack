#!/usr/bin/env python3
"""PostToolUse hook: open Google OAuth URL from workspace-mcp auth responses."""
import json
import platform
import re
import subprocess
import sys


def open_url(url: str) -> None:
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["open", url], check=False)
    elif system == "Linux":
        subprocess.run(["xdg-open", url], check=False)
    elif system == "Windows":
        subprocess.run(["start", "", url], shell=True, check=False)


def extract_text(tool_result: object) -> str:
    if isinstance(tool_result, str):
        return tool_result
    if isinstance(tool_result, dict):
        parts = []
        for item in tool_result.get("content", []):
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return " ".join(parts)
    return str(tool_result)


def main() -> None:
    data = json.load(sys.stdin)
    text = extract_text(data.get("tool_result", ""))
    match = re.search(r"https://accounts\.google\.com/o/oauth2[^\s'\")\]]+", text)
    if match:
        open_url(match.group(0))


if __name__ == "__main__":
    main()
