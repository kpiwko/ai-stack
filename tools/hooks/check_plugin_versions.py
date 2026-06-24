#!/usr/bin/env python3
"""Pre-commit hook: verify plugin.json versions match marketplace.json."""
import json
import subprocess
import sys


MARKETPLACE = ".claude-plugin/marketplace.json"
PLUGIN_GLOB = "plugins/*/.claude-plugin/plugin.json"


def staged_files(pattern: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", pattern],
        capture_output=True, text=True, check=True,
    )
    return [f for f in result.stdout.strip().splitlines() if f]


def read_staged(path: str) -> str:
    result = subprocess.run(
        ["git", "show", f":{path}"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def main() -> int:
    staged_plugins = staged_files(PLUGIN_GLOB)
    if not staged_plugins:
        return 0

    if not staged_files(MARKETPLACE):
        print(f"ERROR: plugin.json staged but {MARKETPLACE} is not staged.")
        print("Staged plugin files:")
        for f in staged_plugins:
            print(f"  {f}")
        print(f"\nRun: git add {MARKETPLACE}")
        return 1

    marketplace = json.loads(read_staged(MARKETPLACE))
    versions_by_name = {p["name"]: p["version"] for p in marketplace["plugins"]}

    errors = 0
    for plugin_file in staged_plugins:
        plugin = json.loads(read_staged(plugin_file))
        name = plugin["name"]
        version = plugin["version"]
        marketplace_version = versions_by_name.get(name)

        if marketplace_version is None:
            print(f"ERROR: Plugin '{name}' not found in {MARKETPLACE}")
            errors += 1
        elif version != marketplace_version:
            print(f"ERROR: Version mismatch for '{name}':")
            print(f"  {plugin_file}: {version}")
            print(f"  {MARKETPLACE}:  {marketplace_version}")
            errors += 1

    if errors:
        print("\nFix the version mismatches above, then re-stage and commit.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
