#!/usr/bin/env python3
"""Install portable agent skills and a working-style doc into per-machine agent folders.

Stdlib only, Python 3.9+. Run `python3 agent_skills.py --help`.
"""

from __future__ import annotations

import argparse
import configparser
import hashlib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ABS_PATH_RE = re.compile(r"/(Users|home)/[A-Za-z0-9_.-]+")  # machine-specific home paths


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse single-line `key: value` pairs between leading `---` lines.

    :param text: file contents
    :returns: dict of keys to values; empty if no frontmatter
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return out
        if ":" in line and not line.startswith((" ", "\t")):
            key, _, value = line.partition(":")
            out[key.strip()] = value.strip().strip("\"'")
    return {}  # no closing fence


def repo_skills(repo: Path) -> dict[str, Path]:
    """Map skill folder names to their paths under skills/.

    :param repo: repo root
    :returns: {name: folder}, sorted by name
    """
    root = repo / "skills"
    if not root.is_dir():
        return {}
    return {p.name: p for p in sorted(root.iterdir()) if p.is_dir() and not p.name.startswith(".")}


def tracked_files(repo: Path) -> list[Path]:
    """List git-tracked plus untracked-but-not-ignored files; walk the tree if git is unavailable.

    :param repo: repo root
    :returns: absolute file paths
    """
    try:
        out = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=repo, capture_output=True, text=True, check=True,
        ).stdout
        return [repo / line for line in out.splitlines() if line and (repo / line).is_file()]
    except (OSError, subprocess.CalledProcessError):
        return [p for p in repo.rglob("*") if p.is_file() and ".git" not in p.parts]


def check_repo(repo: Path) -> list[str]:
    """Lint skills and scan for machine paths.

    :param repo: repo root
    :returns: error messages; empty means clean
    """
    errors: list[str] = []
    for name, folder in repo_skills(repo).items():
        files = {p.name for p in folder.iterdir()}
        if "SKILL.md" not in files:  # exact case, even on case-insensitive disks
            errors.append(f"skills/{name}: missing SKILL.md (exact case)")
            continue
        if not NAME_RE.match(name):
            errors.append(f"skills/{name}: folder name must be lowercase letters, digits, hyphens")
        meta = parse_frontmatter((folder / "SKILL.md").read_text())
        if meta.get("name") != name:
            errors.append(f"skills/{name}: frontmatter name '{meta.get('name', '')}' must equal folder name '{name}'")
        if not meta.get("description"):
            errors.append(f"skills/{name}: frontmatter needs a description")
        for p in folder.rglob("*"):
            if p.is_symlink():
                errors.append(f"skills/{name}: symlinks not allowed ({p.relative_to(folder)})")
    for f in tracked_files(repo):
        try:
            text = f.read_text()
        except (UnicodeDecodeError, OSError):
            continue  # skip binaries
        for i, line in enumerate(text.splitlines(), 1):
            if ABS_PATH_RE.search(line):
                errors.append(f"{f.relative_to(repo)}:{i}: machine-specific path; use ~ instead")
    return errors


def new_skill(repo: Path, name: str) -> Path:
    """Create skills/<name>/SKILL.md from templates/SKILL.md.

    :param repo: repo root
    :param name: skill name (lowercase-hyphen)
    :returns: the new folder
    :raises ValueError: bad name or skill already exists
    """
    if not NAME_RE.match(name):
        raise ValueError(f"'{name}' must be lowercase letters, digits, hyphens")
    folder = repo / "skills" / name
    if folder.exists():
        raise ValueError(f"skills/{name} already exists")
    template = (repo / "templates" / "SKILL.md").read_text()
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text(template.replace("{{name}}", name))
    return folder


# ---- installer ----

MARKER = ".agent-skills.json"
SOURCE_ID = "agent-skills"
WORKING_STYLE = "working-style"
IGNORED = {MARKER, ".DS_Store"}  # never hashed or copied
BLOCKING = {"clash", "drifted"}  # states the installer refuses to touch


@dataclass
class Target:
    """One place on this machine that receives skills."""

    name: str
    skills_dir: Path
    working_style: Path | None
    mode: str  # link | copy
    skills: list[str]  # ["*"] means all


@dataclass
class Action:
    """One planned change (or skip) for one entry in one target."""

    target: str
    name: str
    kind: str  # create | update | skip | remove
    reason: str
    src: Path
    dest: Path
    mode: str


def load_config(path: Path) -> list[Target]:
    """Read config.ini into targets.

    :param path: config file
    :returns: targets in file order
    :raises FileNotFoundError: no config file
    :raises ValueError: bad mode or missing skills_dir
    """
    if not path.is_file():
        raise FileNotFoundError(f"no config at {display(path)}; copy config.example.ini to config.ini and edit it")
    cp = configparser.ConfigParser(inline_comment_prefixes=(";", "#"))
    cp.read(path)
    default_mode = cp.get("defaults", "mode", fallback="link")
    targets: list[Target] = []
    for section in cp.sections():
        if not section.startswith("target:"):
            continue
        sec = cp[section]
        name = section.split(":", 1)[1].strip()
        if "skills_dir" not in sec:
            raise ValueError(f"[{section}] needs skills_dir")
        mode = sec.get("mode", default_mode)
        if mode not in ("link", "copy"):
            raise ValueError(f"[{section}] mode must be link or copy, not '{mode}'")
        ws = sec.get("working_style", "").strip()
        skills = [s.strip() for s in sec.get("skills", "*").split(",") if s.strip()]
        targets.append(Target(name, Path(sec["skills_dir"]).expanduser(), Path(ws).expanduser() if ws else None, mode, skills))
    return targets


def display(p: Path) -> str:
    """Show a path with the home folder as ~."""
    home = str(Path.home())
    s = str(p)
    return "~" + s[len(home):] if s == home or s.startswith(home + "/") else s


def marker_path(dest: Path, is_dir: bool) -> Path:
    """Folder entries keep the marker inside; single files get a sidecar next to them."""
    return dest / MARKER if is_dir else dest.with_name(dest.name + MARKER)


def tree_hash(path: Path) -> str:
    """Hash a folder by sorted relative paths and file contents (a single file by contents only).

    :param path: folder or file
    :returns: sha256 hex digest
    """
    if path.is_file():
        files = [("", path)]  # content only, so a renamed copy still matches
    else:
        files = sorted(
            (p.relative_to(path).as_posix(), p) for p in path.rglob("*") if p.is_file() and p.name not in IGNORED
        )
    h = hashlib.sha256()
    for rel, p in files:
        h.update(f"{rel}\0{hashlib.sha256(p.read_bytes()).hexdigest()}\n".encode())
    return h.hexdigest()


def read_marker(dest: Path, is_dir: bool) -> dict | None:
    """Return our marker data, or None if absent or not ours."""
    m = marker_path(dest, is_dir)
    try:
        data = json.loads(m.read_text())
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) and data.get("source") == SOURCE_ID else None


def is_within(p: Path, root: Path) -> bool:
    """True if p is root or inside it."""
    try:
        p.relative_to(root)
        return True
    except ValueError:
        return False


def entry_state(src: Path, dest: Path, mode: str, repo: Path) -> str:
    """Classify an installed entry.

    :param src: repo skill folder or file
    :param dest: where it goes in the target
    :param mode: link | copy
    :param repo: repo root, for symlink ownership
    :returns: missing | installed | outdated | drifted | clash
    """
    if dest.is_symlink():
        resolved = dest.resolve()
        if resolved == src.resolve():
            return "installed" if mode == "link" else "outdated"
        return "outdated" if is_within(resolved, repo.resolve()) else "clash"  # ours if it points into this repo
    if not dest.exists():
        return "missing"
    marker = read_marker(dest, src.is_dir())
    if marker is None:
        return "clash"
    if tree_hash(dest) != marker.get("sha256"):
        return "drifted"  # someone edited the installed copy
    if mode == "copy" and marker["sha256"] == tree_hash(src):
        return "installed"
    return "outdated"


def target_items(repo: Path, target: Target, names: list[str]) -> list[tuple[str, Path, Path]]:
    """List (name, src, dest) entries for a target, optionally limited to names.

    :raises ValueError: a name isn't a skill in this repo
    """
    skills = repo_skills(repo)
    selected = list(skills) if target.skills == ["*"] else target.skills
    wanted = names or selected + ([WORKING_STYLE] if target.working_style else [])
    unknown = [n for n in wanted if n not in skills and n != WORKING_STYLE]
    if unknown:
        raise ValueError(f"target '{target.name}': unknown skill(s): {', '.join(unknown)}")
    items: list[tuple[str, Path, Path]] = []
    for n in wanted:
        if n == WORKING_STYLE:
            if target.working_style:
                items.append((n, repo / "working-style.md", target.working_style))
        elif n in selected:
            items.append((n, skills[n], target.skills_dir / n))
    return items


def plan_install(repo: Path, targets: list[Target], names: list[str]) -> list[Action]:
    """Compute what install would do; changes nothing.

    :param repo: repo root
    :param targets: targets to plan for
    :param names: limit to these entries; empty means each target's selection
    :returns: one action per entry
    """
    today = date.today().strftime("%Y%m%d")
    actions: list[Action] = []
    for t in targets:
        for name, src, dest in target_items(repo, t, names):
            state = entry_state(src, dest, t.mode, repo)
            kind, reason = {
                "missing": ("create", "new"),
                "outdated": ("update", "repo or mode changed"),
                "installed": ("skip", "up to date"),
                "drifted": ("skip", "drifted: installed copy was edited; move it aside to reinstall"),
                "clash": ("skip", f"clash: not installed by agent-skills; to replace it: mv '{display(dest)}' '{display(dest)}.bak-{today}'"),
            }[state]
            actions.append(Action(t.name, name, kind, reason, src, dest, t.mode))
    return actions


def owned_state(dest: Path, repo: Path) -> str:
    """Ownership of an existing entry, without needing its repo source.

    :returns: missing | owned | drifted | clash
    """
    if dest.is_symlink():
        return "owned" if is_within(dest.resolve(), repo.resolve()) else "clash"
    if not dest.exists():
        return "missing"
    marker = read_marker(dest, dest.is_dir())
    if marker is None:
        return "clash"
    return "owned" if tree_hash(dest) == marker.get("sha256") else "drifted"


def find_orphans(repo: Path, target: Target) -> list[str]:
    """Owned entries in a target that the repo or config no longer selects.

    :param repo: repo root
    :param target: target to scan
    :returns: entry names, sorted
    """
    if not target.skills_dir.is_dir():
        return []
    skills = repo_skills(repo)
    selected = set(skills) if target.skills == ["*"] else set(target.skills) & set(skills)
    return sorted(
        p.name for p in target.skills_dir.iterdir()
        if p.name not in selected and (p.is_symlink() or p.is_dir()) and owned_state(p, repo) in ("owned", "drifted")
    )


def plan_uninstall(repo: Path, targets: list[Target], names: list[str]) -> list[Action]:
    """Plan removal of named entries; only owned, unedited ones are removed.

    :param repo: repo root
    :param targets: targets to plan for
    :param names: skills (or working-style) to remove
    :returns: one action per target and name
    :raises ValueError: a name isn't a plain skill name
    """
    bad = [n for n in names if not NAME_RE.match(n)]
    if bad:  # no paths, so removal stays inside each target
        raise ValueError(f"not a skill name: {', '.join(bad)}")
    actions: list[Action] = []
    for t in targets:
        for n in names:
            if n == WORKING_STYLE:
                if not t.working_style:
                    continue
                src, dest = repo / "working-style.md", t.working_style
            else:
                src, dest = repo / "skills" / n, t.skills_dir / n
            kind, reason = {
                "missing": ("skip", "not installed"),
                "owned": ("remove", "installed by agent-skills"),
                "drifted": ("skip", "drifted: installed copy was edited; remove it by hand if you're sure"),
                "clash": ("skip", "clash: not installed by agent-skills; left alone"),
            }[owned_state(dest, repo)]
            actions.append(Action(t.name, n, kind, reason, src, dest, t.mode))
    return actions


def git_commit(repo: Path) -> str | None:
    """Current commit, or None without git."""
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def remove_owned(dest: Path, is_dir: bool) -> None:
    """Delete an entry the installer owns (link, copied folder, or file + sidecar)."""
    if dest.is_symlink():
        dest.unlink()
    elif dest.is_dir():
        shutil.rmtree(dest)
    elif dest.exists():
        dest.unlink()
        marker_path(dest, False).unlink(missing_ok=True)


def apply_actions(actions: list[Action], repo: Path) -> None:
    """Carry out planned actions, re-checking ownership right before each write.

    :param actions: from plan_install / plan_uninstall
    :param repo: repo root
    """
    commit = git_commit(repo)
    for a in actions:
        if a.kind == "skip":
            continue
        if a.kind == "remove":
            if owned_state(a.dest, repo) == "owned":  # re-check right before deleting
                remove_owned(a.dest, a.dest.is_dir())
            else:
                print(f"  skipped {a.target}/{a.name}: changed since planning")
            continue
        is_dir = a.src.is_dir()
        if a.dest.exists() or a.dest.is_symlink():
            if entry_state(a.src, a.dest, a.mode, repo) in BLOCKING:  # changed since planning
                print(f"  skipped {a.target}/{a.name}: changed since planning")
                continue
            remove_owned(a.dest, is_dir)
        a.dest.parent.mkdir(parents=True, exist_ok=True)
        if a.mode == "link":
            a.dest.symlink_to(a.src.resolve())
            continue
        if is_dir:
            shutil.copytree(a.src, a.dest, ignore=shutil.ignore_patterns(*IGNORED))
        else:
            shutil.copy2(a.src, a.dest)
        marker = {"source": SOURCE_ID, "name": a.name, "commit": commit, "sha256": tree_hash(a.dest)}
        marker_path(a.dest, is_dir).write_text(json.dumps(marker, indent=2) + "\n")


def print_actions(actions: list[Action]) -> None:
    """Print a plan as aligned rows."""
    for a in actions:
        print(f"  {a.target:<10} {a.kind:<7} {a.name:<24} {display(a.dest)} ({a.mode})  {a.reason}")


def confirm(args: argparse.Namespace) -> bool:
    """Ask before changing anything, unless --yes."""
    if args.yes:
        return True
    try:
        return input("Proceed? [y/N] ").strip().lower() in ("y", "yes")
    except EOFError:
        return False


def selected_targets(args: argparse.Namespace) -> list[Target]:
    """Load config and apply --target."""
    targets = load_config(Path(args.config).expanduser())
    if args.target:
        targets = [t for t in targets if t.name == args.target]
        if not targets:
            raise ValueError(f"no target named '{args.target}' in config")
    return targets


def print_hookup(targets: list[Target]) -> None:
    """Print the instruction-file lines for installed working-style files; never edits them."""
    for t in targets:
        if t.working_style and (t.working_style.exists() or t.working_style.is_symlink()):
            p = display(t.working_style)
            print(f"\nworking-style for '{t.name}' is at {p}. Add one line to that agent's instruction file (not edited for you):")
            print(f"  Claude (CLAUDE.md):  @{p}")
            print(f"  Others (AGENTS.md):  Read and follow {p}.")


def cmd_status(args: argparse.Namespace) -> int:
    """Print the state of every entry; exit 1 if anything isn't installed."""
    try:
        targets = selected_targets(args)
        clean = True
        for t in targets:
            print(f"[{t.name}] {display(t.skills_dir)} ({t.mode})")
            for name, src, dest in target_items(REPO, t, []):
                state = entry_state(src, dest, t.mode, REPO)
                clean = clean and state == "installed"
                print(f"  {state:<10} {name}")
            for name in find_orphans(REPO, t):
                clean = False
                print(f"  {'orphan':<10} {name}  (no longer selected; run uninstall {name})")
    except (OSError, ValueError) as e:
        print(f"error: {e}")
        return 2
    return 0 if clean else 1


def cmd_install(args: argparse.Namespace) -> int:
    """Plan, confirm, and apply an install."""
    try:
        targets = selected_targets(args)
        actions = plan_install(REPO, targets, args.names)
    except (OSError, ValueError) as e:
        print(f"error: {e}")
        return 2
    print_actions(actions)
    blocked = any(a.reason.startswith(("clash", "drifted")) for a in actions)
    todo = [a for a in actions if a.kind != "skip"]
    if not todo:
        print("nothing to do")
    elif args.dry_run:
        print("dry run: nothing changed")
    elif confirm(args):
        apply_actions(todo, REPO)
        print(f"done: {len(todo)} change(s)")
        print_hookup(targets)
    else:
        print("cancelled")
    return 1 if blocked else 0


def cmd_uninstall(args: argparse.Namespace) -> int:
    """Plan, confirm, and apply removals of owned entries."""
    try:
        actions = plan_uninstall(REPO, selected_targets(args), args.names)
    except (OSError, ValueError) as e:
        print(f"error: {e}")
        return 2
    print_actions(actions)
    todo = [a for a in actions if a.kind == "remove"]
    if not todo:
        print("nothing to do")
    elif args.dry_run:
        print("dry run: nothing changed")
    elif confirm(args):
        apply_actions(todo, REPO)
        print(f"done: removed {len(todo)}")
    else:
        print("cancelled")
    return 1 if any(a.reason.startswith(("clash", "drifted")) for a in actions) else 0


def cmd_check(args: argparse.Namespace) -> int:
    """Run check_repo and print results."""
    errors = check_repo(REPO)
    for e in errors:
        print(e)
    print("check: ok" if not errors else f"check: {len(errors)} problem(s)")
    return 1 if errors else 0


def cmd_new(args: argparse.Namespace) -> int:
    """Scaffold a new skill."""
    try:
        folder = new_skill(REPO, args.name)
    except ValueError as e:
        print(f"error: {e}")
        return 2
    print(f"created {folder.relative_to(REPO)}/SKILL.md; edit it, then run check")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    p = argparse.ArgumentParser(prog="agent_skills.py", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="lint skills and scan for machine paths").set_defaults(func=cmd_check)
    n = sub.add_parser("new", help="scaffold skills/<name>/SKILL.md")
    n.add_argument("name")
    n.set_defaults(func=cmd_new)
    for cmd, func, help_ in (("status", cmd_status, "show what is installed where (read-only)"),
                             ("install", cmd_install, "plan, confirm, then link/copy skills into targets"),
                             ("uninstall", cmd_uninstall, "remove entries this tool installed")):
        c = sub.add_parser(cmd, help=help_)
        c.add_argument("--config", default=str(REPO / "config.ini"), help="config file (default: config.ini)")
        c.add_argument("--target", help="only this target")
        if cmd == "install":
            c.add_argument("names", nargs="*", help="limit to these skills (or working-style)")
        if cmd == "uninstall":
            c.add_argument("names", nargs="+", help="skills (or working-style) to remove")
        if cmd != "status":
            c.add_argument("--dry-run", action="store_true", help="print the plan and stop")
            c.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
        c.set_defaults(func=func)
    return p


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    :param argv: arguments (default sys.argv[1:])
    :returns: exit code
    """
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
