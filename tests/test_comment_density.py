"""Tests for the code-comments density script: the main report on a sample file."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "skills" / "code-comments" / "scripts" / "comment_density.py"
spec = importlib.util.spec_from_file_location("comment_density", SCRIPT)
density = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = density  # dataclasses on 3.9 look the module up here
spec.loader.exec_module(density)

# sparse(): 11 code lines incl. def, 1 comment, a 9-line uncommented stretch; dense(): 5 lines, 2 comments
SAMPLE = '''"""Module docstring."""


def sparse(xs):
    """Docstrings aren't comments or code."""
    total = 0  # running sum
    for x in xs:
        if x > 0:
            total += x
        else:
            total -= x
    y = total * 2
    z = y + 1
    s = "# not a comment"
    return z


def dense(xs):
    # keep positives
    ys = [x for x in xs if x > 0]
    n = len(ys)  # how many kept
    m = n * 2
    return m
'''


class DensityTest(unittest.TestCase):
    def test_report_counts_flags_sparse_function_and_gap(self) -> None:
        r = density.analyze(SAMPLE, gap=8)
        self.assertEqual((r.code_lines, r.comments), (16, 3))  # docstrings and "#" in strings excluded
        by_name = {f.name: f for f in r.functions}
        self.assertEqual((by_name["sparse"].code, by_name["sparse"].comments), (11, 1))
        self.assertEqual((by_name["dense"].code, by_name["dense"].comments), (5, 2))
        self.assertEqual([(g.start, g.end) for g in r.gaps], [(7, 15)])  # after "# running sum" to return
        imports = "import os\n" * 9 + "from sys import (\n    argv,\n)\n"
        self.assertEqual(density.analyze(imports).code_lines, 0)  # imports never need comments


if __name__ == "__main__":
    unittest.main()
