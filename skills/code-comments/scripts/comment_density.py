#!/usr/bin/env python3
"""Report comment density for Python files: overall, per function, and long uncommented stretches.

Stdlib only, Python 3.9+. Usage: comment_density.py [--target 5] [--gap 8] FILE...
Imports and docstrings don't count as code; "#" inside strings isn't a comment.
"""

from __future__ import annotations

import argparse
import ast
import io
import math
import sys
import tokenize
from dataclasses import dataclass, field
from pathlib import Path

# tokens that are layout, not code
SKIP_TOKENS = {tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER, tokenize.ENCODING}
DEFS = (ast.FunctionDef, ast.AsyncFunctionDef)  # what counts as a function
SCOPES = (ast.Module, ast.ClassDef, *DEFS)  # what can carry a docstring


@dataclass
class Func:
    """One function's span and counts."""

    name: str
    start: int  # the def line
    end: int  # its last line
    code: int = 0
    comments: int = 0


@dataclass
class Gap:
    """A run of code lines with no comment, by first and last line."""

    start: int
    end: int


@dataclass
class Report:
    """Totals for one file."""

    code_lines: int
    comments: int
    functions: list[Func] = field(default_factory=list)
    gaps: list[Gap] = field(default_factory=list)


def span(node: ast.AST) -> range:
    """Every line a node covers, first to last."""
    return range(node.lineno, node.end_lineno + 1)


def not_code(tree: ast.AST) -> set[int]:
    """Lines that hold docstrings or imports, which never need comments.

    :param tree: parsed module
    :returns: set of 1-based line numbers
    """
    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            lines.update(span(node))  # includes multi-line "from x import (...)"
        elif isinstance(node, SCOPES) and node.body:
            first = node.body[0]
            # a docstring is a bare string as the first statement
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                lines.update(span(first))
    return lines


def analyze(source: str, gap: int = 8) -> Report:
    """Count code lines and comments, per file and per function, and find uncommented stretches.

    :param source: Python source text
    :param gap: flag runs of at least this many code lines with no comment
    :returns: the report
    """
    tree = ast.parse(source)
    skip = not_code(tree)
    code: set[int] = set()  # lines holding real code
    commented: set[int] = set()  # lines holding a comment (inline or alone)
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type == tokenize.COMMENT:
            if not (tok.start[0] == 1 and tok.string.startswith("#!")):  # shebang isn't a comment
                commented.add(tok.start[0])
        elif tok.type not in SKIP_TOKENS:
            # a multi-line string counts every line it covers
            code.update(n for n in range(tok.start[0], tok.end[0] + 1) if n not in skip)

    # walk lines in order; a comment, docstring, or new def/class ends the uncommented run
    starts = {node.lineno for node in ast.walk(tree) if isinstance(node, (*DEFS, ast.ClassDef))}
    gaps: list[Gap] = []
    run: list[int] = []  # code lines since the last comment

    def close_run() -> None:
        """Record the current run if it's long enough, then start over."""
        nonlocal run  # rebind the outer list, not a local copy
        if len(run) >= gap:
            gaps.append(Gap(run[0], run[-1]))
        run = []

    for n in range(1, max(code | commented | skip | {0}) + 1):
        if n in starts:
            close_run()  # don't let a stretch spill into the next function
        if n in code and n not in commented:  # an inline comment covers its own line
            run.append(n)
        if n in commented or n in skip:
            close_run()
    close_run()  # a stretch that runs to the end of the file

    # per function: nested functions count toward the outer one too
    funcs = sorted((Func(node.name, node.lineno, node.end_lineno) for node in ast.walk(tree) if isinstance(node, DEFS)),
                   key=lambda f: f.start)
    for f in funcs:
        lines = range(f.start, f.end + 1)
        f.code = sum(n in code for n in lines)  # True counts as 1
        f.comments = sum(n in commented for n in lines)
    return Report(len(code), len(commented), funcs, gaps)


def per(code: int, comments: int) -> str:
    """Format as '1 per N lines', or 'no comments'."""
    return f"1 per {code / comments:.1f} lines" if comments else "no comments"


def main(argv: list[str] | None = None) -> int:
    """CLI entry point; exits 1 if any file misses the target or has a gap.

    :param argv: arguments (default sys.argv[1:])
    :returns: exit code
    """
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("files", nargs="+", type=Path)
    p.add_argument("--target", type=float, default=5, help="aim for 1 comment per this many code lines")
    p.add_argument("--gap", type=int, default=8, help="flag this many code lines in a row without a comment")
    args = p.parse_args(argv)
    ok = True
    for path in args.files:  # one report per file
        r = analyze(path.read_text(), args.gap)
        need = max(0, math.ceil(r.code_lines / args.target) - r.comments)  # comments short of target
        print(f"{path}: {r.comments} comments, {r.code_lines} code lines "
              f"({per(r.code_lines, r.comments)}; target 1 per {args.target:g})"
              + (f", ~{need} more needed" if need else ""))
        for f in r.functions:
            # skip tiny functions; flag the rest if they miss the target
            if f.code >= args.target and (not f.comments or f.code / f.comments > args.target):
                print(f"  sparse  {f.name} (lines {f.start}-{f.end}): {per(f.code, f.comments)}")
        for g in r.gaps:
            print(f"  gap     lines {g.start}-{g.end}: no comment")
        ok = ok and not need and not r.gaps  # any miss fails the whole run
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
