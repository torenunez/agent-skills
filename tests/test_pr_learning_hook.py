"""Tests for the pr-learning hook script: command matching, and the PR gate's guarantee."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "skills" / "pr-learning" / "scripts" / "pr_learning_hook.py"
spec = importlib.util.spec_from_file_location("pr_learning_hook", SCRIPT)
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


class MatchTest(unittest.TestCase):
    def test_commands_and_record(self) -> None:
        self.assertEqual(hook.PR_RE.search("cd x && gh pr create --fill").group(1), "create")
        self.assertIsNone(hook.PR_RE.search("echo gh pr create"))  # only as a command
        self.assertEqual(hook.NEW_BRANCH_RE.search("git checkout -b v4.6-foo").group(1), "v4.6-foo")
        record = "## app v1 [b1] (2026-01-01)\nStart note: x\n## app v2 [b2] (2026-01-02)\n- Quiz: why: right\n"
        self.assertFalse(hook.has_end_entry(record, "b1"))  # start only
        self.assertTrue(hook.has_end_entry(record, "b2"))
        self.assertTrue(hook.has_end_entry(record + "## app v1 [b1] (2026-01-03)\n- Skipped: end\n", "b1"))


class GateTest(unittest.TestCase):
    def test_gate_blocks_until_end_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, record = Path(tmp) / "repo", Path(tmp) / "record.md"
            subprocess.run(["git", "init", "-q", "-b", "v9-test", str(repo)], check=True)
            payload = json.dumps({"cwd": str(repo), "tool_input": {"command": "gh pr create --fill"}})

            def run_gate() -> str:
                return subprocess.run([sys.executable, str(SCRIPT), "gate", "--record", str(record)],
                                      input=payload, capture_output=True, text=True, check=True).stdout

            out = json.loads(run_gate())["hookSpecificOutput"]
            self.assertEqual(out["permissionDecision"], "deny")  # no record at all
            record.write_text("## repo v9 [v9-test] (2026-01-01)\n- Quiz: why: right\n")
            self.assertEqual(run_gate(), "")  # end checkpoint recorded: allowed


if __name__ == "__main__":
    unittest.main()
