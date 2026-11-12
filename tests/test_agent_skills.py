"""Tests for agent_skills.py: happy path plus the safety guarantees."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # import from repo root

import agent_skills


def write_skill(repo: Path, folder: str, name: str, body: str = "Body.\n") -> Path:
    """Create skills/<folder>/SKILL.md with the given frontmatter name; returns the folder."""
    d = repo / "skills" / folder
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Test skill.\n---\n\n{body}")
    return d


class CheckTest(unittest.TestCase):
    def test_check_flags_name_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write_skill(repo, "foo", "bar")
            errors = agent_skills.check_repo(repo)
            self.assertTrue(any("foo" in e and "bar" in e for e in errors), errors)
            write_skill(repo, "foo", "foo")  # fix the name
            self.assertEqual(agent_skills.check_repo(repo), [])


class InstallTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.repo = root / "repo"
        write_skill(self.repo, "alpha", "alpha")
        (self.repo / "working-style.md").write_text("Be concise.\n")
        self.t1, self.t2 = root / "t1", root / "t2"  # t1 links, t2 copies
        self.targets = [
            agent_skills.Target("t1", self.t1, root / "ws1.md", "link", ["*"]),
            agent_skills.Target("t2", self.t2, root / "ws2.md", "copy", ["*"]),
        ]

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def install(self) -> list[agent_skills.Action]:
        """Plan and apply a full install; returns the plan."""
        actions = agent_skills.plan_install(self.repo, self.targets, [])
        agent_skills.apply_actions(actions, self.repo)
        return actions

    def test_install_link_and_copy_then_idempotent(self) -> None:
        self.install()
        self.assertTrue((self.t1 / "alpha").is_symlink())
        self.assertTrue((self.t2 / "alpha" / agent_skills.MARKER).exists())
        again = agent_skills.plan_install(self.repo, self.targets, [])
        self.assertTrue(all(a.kind == "skip" for a in again), again)

    def test_clash_is_left_untouched(self) -> None:
        (self.t2 / "alpha").mkdir(parents=True)
        (self.t2 / "alpha" / "note.txt").write_text("mine")
        actions = self.install()
        self.assertEqual((self.t2 / "alpha" / "note.txt").read_text(), "mine")
        self.assertIn("clash", next(a.reason for a in actions if a.dest == self.t2 / "alpha"))

    def test_drifted_copy_is_not_overwritten(self) -> None:
        self.install()
        (self.t2 / "alpha" / "SKILL.md").write_text("hand edit")
        write_skill(self.repo, "alpha", "alpha", body="New body.\n")  # repo moves on
        self.install()
        self.assertEqual((self.t2 / "alpha" / "SKILL.md").read_text(), "hand edit")

    def test_uninstall_leaves_foreign_and_drifted(self) -> None:
        self.install()
        (self.t2 / "foreign").mkdir()
        (self.t2 / "foreign" / "note.txt").write_text("mine")
        (self.t2 / "alpha" / "SKILL.md").write_text("hand edit")
        actions = agent_skills.plan_uninstall(self.repo, self.targets, ["foreign", "alpha"])
        agent_skills.apply_actions(actions, self.repo)
        self.assertEqual((self.t2 / "foreign" / "note.txt").read_text(), "mine")
        self.assertEqual((self.t2 / "alpha" / "SKILL.md").read_text(), "hand edit")
        self.assertFalse((self.t1 / "alpha").exists())  # owned link is removed

    def test_uninstall_rejects_path_names(self) -> None:
        with self.assertRaises(ValueError):
            agent_skills.plan_uninstall(self.repo, self.targets, ["../t1/alpha"])


if __name__ == "__main__":
    unittest.main()
