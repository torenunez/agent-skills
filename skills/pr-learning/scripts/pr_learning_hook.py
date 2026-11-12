#!/usr/bin/env python3
"""Claude Code hooks for pr-learning: a nudge when a branch is created, and a gate on opening or merging a PR.

- `branch` (PostToolUse, matcher Bash): after `git checkout -b` / `git switch -c` / `git worktree add -b`,
  tells the agent to run the start checkpoint.
- `gate` (PreToolUse, matcher Bash): blocks `gh pr create` / `gh pr merge` until the learning record has an
  end entry (a quiz result or an end skip) under a heading tagged `[<branch>]`.

Both read the hook's JSON on stdin. Standard library only, Python 3.9+. Setup: see the repo README.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

DEFAULT_RECORD = "~/.local/share/agent-skills/learning-record.md"
BASE_BRANCHES = {"main", "master", "production"}  # no PR is "for" these

_AT_CMD = r"(?:^|[;&|(])\s*"  # start of a command: line start or after a shell separator
NEW_BRANCH_RE = re.compile(_AT_CMD + r"git\s+(?:checkout\s+-[bB]|switch\s+-[cC]|worktree\s+add\s+-[bB])\s+([^\s;&|)]+)")
PR_RE = re.compile(_AT_CMD + r"gh\s+pr\s+(create|merge)\b([^;&|)]*)")
END_RE = re.compile(r"^- Quiz:|Skipped:.*\bend\b")  # what the end checkpoint writes


def sections_for(record_text: str, branch: str) -> list[list[str]]:
    """Collect the record sections whose `## ` heading is tagged `[branch]`.

    :param record_text: the learning record's contents
    :param branch: git branch name
    :returns: one list of body lines per matching section
    """
    found: list[list[str]] = []
    current: Optional[list[str]] = None
    for line in record_text.splitlines():
        if line.startswith("## "):
            current = [] if f"[{branch}]" in line else None
            if current is not None:
                found.append(current)
        elif current is not None:
            current.append(line)
    return found


def has_end_entry(record_text: str, branch: str) -> bool:
    """True when a section for this branch holds a quiz result or an end skip."""
    return any(END_RE.search(line) for body in sections_for(record_text, branch) for line in body)


def run(args: list[str], cwd: Optional[str], timeout: int = 5) -> Optional[str]:
    """Run a command; returns stripped stdout, or None on any failure."""
    try:
        out = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def pr_branch(action: str, rest: str, cwd: Optional[str]) -> Optional[str]:
    """Find the branch a `gh pr create|merge` command is about.

    :param action: "create" or "merge"
    :param rest: the command text after the action
    :param cwd: the session's working directory
    :returns: branch name, or None when it can't be told
    """
    target = next((t for t in rest.split() if not t.startswith("-")), None)
    if action == "merge" and target:  # a number, URL, or branch: ask GitHub
        return run(["gh", "pr", "view", target, "--json", "headRefName", "--jq", ".headRefName"], cwd, timeout=15)
    return run(["git", "branch", "--show-current"], cwd) or None


def emit(event: str, **fields: str) -> None:
    """Print the hook's JSON answer."""
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, **fields}}))


def gate(data: dict, record: Path) -> None:
    """PreToolUse: deny PR create/merge without an end checkpoint for the branch."""
    m = PR_RE.search(data.get("tool_input", {}).get("command", ""))
    if not m:
        return  # not a PR command
    branch = pr_branch(m.group(1), m.group(2), data.get("cwd"))
    if branch is None:
        emit("PreToolUse", permissionDecision="ask",
             permissionDecisionReason="pr-learning: couldn't tell which branch this PR is for, so the end-checkpoint check didn't run.")
        return
    if branch in BASE_BRANCHES:
        return
    text = record.read_text() if record.exists() else ""
    if has_end_entry(text, branch):
        return
    emit("PreToolUse", permissionDecision="deny", permissionDecisionReason=(
        f"pr-learning: no end checkpoint recorded for branch {branch} in {record}. "
        f"Run the pr-learning end checkpoint first (tag the record heading [{branch}]); "
        f"if the user says skip, record '- Skipped: end' under that heading. Then retry."))


def branch_nudge(data: dict, record: Path) -> None:
    """PostToolUse: after a new branch, remind the agent to run the start checkpoint."""
    m = NEW_BRANCH_RE.search(data.get("tool_input", {}).get("command", ""))
    if not m:
        return
    name = m.group(1)
    if record.exists() and sections_for(record.read_text(), name):
        return  # already started
    emit("PostToolUse", additionalContext=(
        f"pr-learning: branch {name} was just created. Before any code changes, run the pr-learning "
        f"start checkpoint (the user can say skip). Tag its record heading [{name}]."))


def main() -> int:
    """Entry point; never blocks work because of its own bug."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=["gate", "branch"])
    p.add_argument("--record", default=DEFAULT_RECORD, help="learning record path")
    a = p.parse_args()
    try:
        data = json.load(sys.stdin)
        record = Path(a.record).expanduser()
        (gate if a.mode == "gate" else branch_nudge)(data, record)
    except Exception as e:  # fail open, but say so
        print(json.dumps({"systemMessage": f"pr-learning hook error ({a.mode}): {e}"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
