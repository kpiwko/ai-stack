#!/usr/bin/env python3
"""GIT_SEQUENCE_EDITOR script for cr-review multi-commit amendment.

Usage:
    GIT_SEQUENCE_EDITOR="python3 /tmp/cr_seq_editor.py" git rebase -i HEAD~N

The script is generated at review time with COMMIT_TO_TMPFILE populated.
It injects `exec git commit --amend -F <tmpfile>` after each matching pick line.
"""
import re
import shlex
import sys

# COMMIT_TO_TMPFILE maps short SHA prefixes to the temp file containing the new
# commit message. Populated by the cr-review skill at runtime.
# Example:
#   COMMIT_TO_TMPFILE = {
#       "a1b2c3d": "/tmp/cr_msg_a1b2c3d.txt",
#       "e4f5a6b": "/tmp/cr_msg_e4f5a6b.txt",
#   }
COMMIT_TO_TMPFILE: dict[str, str] = {}

content = open(sys.argv[1]).read()
lines = content.split("\n")
result = []

for line in lines:
    result.append(line)
    for sha, tmpfile in COMMIT_TO_TMPFILE.items():
        if re.match(rf"^pick {sha}", line):
            result.append(f"exec git commit --amend -F {shlex.quote(tmpfile)}")

open(sys.argv[1], "w").write("\n".join(result))
