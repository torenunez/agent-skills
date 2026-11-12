# agent-skills v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A public-ready repo of portable skills, a portable working-style doc, and a stdlib installer that links/copies them into per-machine agent folders without touching anything it didn't install.

**Architecture:** Plain `skills/<name>/SKILL.md` folders plus `working-style.md`. One file, `agent_skills.py`, reads a gitignored `config.ini`, computes a plan of actions per target, prints it, confirms, applies. Ownership is proven by symlink target (link mode) or a `.agent-skills.json` marker (copy mode).

**Tech Stack:** Python 3.9+ stdlib only (`configparser`, `argparse`, `dataclasses`, `hashlib`, `shutil`, `unittest`), GitHub Actions, gitleaks, pre-commit.

**Spec:** `docs/design.md`

## Global Constraints

- Python **3.9+**, standard library only; `from __future__ import annotations` for `list[str]` hints.
- Config is INI via `configparser`; `config.ini` gitignored, `config.example.ini` committed.
- No absolute `/Users/` or `/home/` paths, usernames, or company/work tool names in any tracked file.
- Never overwrite or delete an entry the installer doesn't own. No `--force`.
- Never edit `CLAUDE.md` / `AGENTS.md`; print the line to add instead.
- Skill names: lowercase letters, digits, hyphens; frontmatter `name` == folder name.
- Code style: type hints, one-line docstrings with params/returns, short inline comments, no comment blocks.
- Tests: `unittest`, temp dirs only, never real home folders. Owner rule: one happy-path test per module plus one per real safety guarantee (overrides broader TDD/Review-Focus test lists).
- Commits use the repo-local noreply identity already configured. Do not push.

## Review Focus

Owner's minimal-testing rule limits tests to happy path + safety guarantees, so these are handled in code and checked by hand in Task 6 rather than each getting a test:

1. Target `skills_dir` (or `working_style` parent) doesn't exist yet → created, not a crash.
2. Config selects a skill name not in `skills/` → error naming it, exit 2, nothing written for that target.
3. A symlink into the repo whose skill was deleted (dangling) → `orphan`, not a crash.
4. No `config.ini` → message pointing at `config.example.ini`, exit 2.
5. Running `install` twice → second run reports "nothing to do" (asserted inside the happy-path test).

---

### Task 1: Repo scaffold and skill linting (`check`, `new`)

**Files:**
- Create: `LICENSE` (MIT, "torenunez", 2026), `.gitignore` (`config.ini`, `__pycache__/`, `*.pyc`, `.DS_Store`), `AGENTS.md`, `CLAUDE.md` (single line `@AGENTS.md`), `README.md` (stub: one paragraph + "see docs/design.md"), `todo.md` (design §11 items), `templates/SKILL.md`, `agent_skills.py`, `tests/test_agent_skills.py`

**Interfaces:**
- Produces:
  - `NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")`
  - `parse_frontmatter(text: str) -> dict[str, str]` — single-line `key: value` between leading `---` lines; `{}` if none.
  - `repo_skills(repo: Path) -> dict[str, Path]` — folder name → folder, for dirs under `skills/`.
  - `check_repo(repo: Path) -> list[str]` — error strings; empty = clean.
  - `new_skill(repo: Path, name: str) -> Path` — copies template, substitutes `{{name}}`; raises `ValueError` on bad/existing name.
  - `main(argv: list[str] | None = None) -> int` with argparse subcommands (`check`, `new` now; others added later).

`AGENTS.md` content: rules for agents editing this repo — no machine paths/usernames/work references; skills describe capabilities not tool names; machine-specific details go in the machine's own instruction file; run `python3 agent_skills.py check` and `python3 -m unittest` before committing; follow `working-style.md`.

`check_repo` rules: each `skills/*` dir has exact-case `SKILL.md`; frontmatter has `name` == folder and non-empty `description`; name matches `NAME_RE`; no symlinks inside skill folders; no `/Users/` or `/home/` in any git-tracked text file (use `git ls-files`; fall back to walking the repo minus `.git` when git is unavailable).

- [ ] **Step 1: Write the failing test**

```python
class CheckTest(unittest.TestCase):
    def test_check_flags_name_mismatch(self):
        # temp repo with skills/foo/SKILL.md whose frontmatter says name: bar
        errors = agent_skills.check_repo(tmp_repo)
        self.assertTrue(any("foo" in e and "bar" in e for e in errors))
        # fix the name → clean
        self.assertEqual(agent_skills.check_repo(tmp_repo_fixed), [])
```

- [ ] **Step 2:** Run `python3 -m unittest -v` → FAIL (module/function missing).
- [ ] **Step 3:** Implement the Produces functions and the scaffold files.
- [ ] **Step 4:** Run `python3 -m unittest -v` → PASS. Run `python3 agent_skills.py new demo-skill && python3 agent_skills.py check` → exit 0; then delete `skills/demo-skill`.
- [ ] **Step 5: Commit** `feat: scaffold repo with check and new commands` (include `docs/`).

### Task 2: Port the three skills

**Files:**
- Create: `skills/pr-learning/SKILL.md`, `skills/docs-drift/SKILL.md`, `skills/process-agent-feedback/SKILL.md` (source: `~/.claude/skills/<name>/SKILL.md`)

**Interfaces:** Consumes `check_repo` (Task 1).

Edits to `pr-learning` (design §5), nothing else changes:
- Record path → "the learning record path named in the user's instructions; if none, `~/.local/share/agent-skills/learning-record.md`".
- Project-specific example → a generic example ("you met X in <project> v4.2").
- Tool-specific paste-note step → "Learning note: if the user's instructions name a learning tool, a short plain-text block to paste into it…; otherwise skip."
- "WebFetch, or the web-fetch agent" → "fetch it".

`docs-drift` and `process-agent-feedback`: copy verbatim, then replace any agent-specific tool names with capability wording.

- [ ] **Step 1:** Copy and edit the three files.
- [ ] **Step 2:** `grep -rniE 'lerni|webfetch|/Users/|claude' skills/` → only intentional hits (review each).
- [ ] **Step 3:** `python3 agent_skills.py check` → exit 0.
- [ ] **Step 4: Commit** `feat: add pr-learning, docs-drift, process-agent-feedback skills`.

### Task 3: working-style.md

**Files:**
- Create: `working-style.md` (source: `~/.claude/CLAUDE.md`)

Follow design §6 table plus §12 calls: move Communication, Workflow, Plan mode/questions, Subagents (model-neutral), Self-Improvement, Elegance, Decision making/checkpoints/continue-independently, Long-running tasks, Git, Code style/comments/testing, What I value. Leave out: browser preference, budget warnings, memory-location rule, `.claude/agents/` rule, machine-environment notes. Agent-neutral wording ("the agent"); named Claude tools/skills → generic phrasing. Open with one line: "How I like to work with coding agents. Machine-specific rules live in each machine's own instruction file."

- [ ] **Step 1:** Write the file.
- [ ] **Step 2:** `grep -niE 'claude|askuserquestion|haiku|superpowers|chrome|budget' working-style.md` → no hits.
- [ ] **Step 3:** `python3 agent_skills.py check` → exit 0.
- [ ] **Step 4: Commit** `docs: add portable working-style.md`.

### Task 4: Installer — config, status, install

**Files:**
- Modify: `agent_skills.py`, `tests/test_agent_skills.py`
- Create: `config.example.ini` (design §7 example, `~` paths only)

**Interfaces:**
- Consumes: `repo_skills`, `main` (Task 1).
- Produces:
  - `MARKER = ".agent-skills.json"`; sidecar for a file `f` is `f.with_name(f.name + ".agent-skills.json")`.
  - `@dataclass class Target: name: str; skills_dir: Path; working_style: Path | None; mode: str; skills: list[str]` (`["*"]` = all).
  - `load_config(path: Path) -> list[Target]` — sections `target:<name>`; `mode` falls back to `[defaults] mode`, then `link`; `~` expanded; raises `ValueError` on bad mode.
  - `tree_hash(path: Path) -> str` — design §12 algorithm (sorted relative POSIX paths, `path\0sha256\n`, markers excluded); a single file hashes as one record named by its file name.
  - `entry_state(src: Path, dest: Path, mode: str, repo: Path) -> str` — one of `missing | installed | outdated | drifted | clash`.
  - `@dataclass class Action: target: str; name: str; kind: str; reason: str; src: Path; dest: Path; mode: str` — `kind` in `create | update | skip | remove`.
  - `plan_install(repo: Path, targets: list[Target], names: list[str]) -> list[Action]` — `names` empty = each target's selection; working style included as name `working-style`.
  - `apply_actions(actions: list[Action], repo: Path) -> None`
  - CLI: `status [--config PATH]`, `install [--config PATH] [--target T] [--dry-run] [--yes] [names...]`.

State rules (`entry_state`):
- `dest` absent (and not a symlink) → `missing`.
- `dest` is a symlink resolving to `src` → `installed` if mode is link, else `outdated`.
- `dest` is a symlink into this repo but not to `src` → `outdated`; symlink elsewhere → `clash`.
- `dest` real dir/file with marker: current `tree_hash(dest)` ≠ marker `sha256` → `drifted`; else marker `sha256` == `tree_hash(src)` and mode is copy → `installed`; else `outdated`.
- `dest` exists without marker → `clash`.

Plan: `missing`/`outdated` → `create`/`update`; `installed` → skip "up to date"; `drifted`/`clash` → skip with reason, and for clash the suggested `mv <dest> <dest>.bak-YYYYMMDD` (printed, never run). `apply_actions` creates parent dirs, replaces owned entries, writes marker `{"source": "agent-skills", "name", "commit", "sha256"}` in copy mode (`commit` from `git rev-parse HEAD`, else `null`). After applying, print for each target with `working_style`: the Claude import line `@<path with ~>` and the generic `Read and follow <path>.` line.

Exit codes: `status` 0 clean / 1 anything not `installed`; `install` 0 success / 1 if any skip was drifted or clash; config/usage errors 2.

- [ ] **Step 1: Write the failing tests**

```python
class InstallTest(unittest.TestCase):
    def test_install_link_and_copy_then_idempotent(self):
        # temp repo with skills/alpha + working-style.md; targets t1 (link) and t2 (copy) in temp dirs
        apply_actions(plan_install(repo, targets, []), repo)
        self.assertTrue((t1 / "alpha").is_symlink())
        self.assertTrue((t2 / "alpha" / MARKER).exists())
        again = plan_install(repo, targets, [])
        self.assertTrue(all(a.kind == "skip" for a in again))

    def test_clash_is_left_untouched(self):
        # t2/alpha pre-exists as a foreign folder containing note.txt
        actions = plan_install(repo, targets, [])
        apply_actions(actions, repo)
        self.assertEqual((t2 / "alpha" / "note.txt").read_text(), "mine")
        self.assertIn("clash", next(a.reason for a in actions if a.dest == t2 / "alpha"))

    def test_drifted_copy_is_not_overwritten(self):
        # install copy, edit t2/alpha/SKILL.md, change repo skill, plan again
        apply_actions(plan_install(repo, targets, []), repo)
        self.assertEqual((t2 / "alpha" / "SKILL.md").read_text(), "hand edit")
```

- [ ] **Step 2:** `python3 -m unittest -v` → the three new tests FAIL.
- [ ] **Step 3:** Implement the Produces items and `config.example.ini`.
- [ ] **Step 4:** `python3 -m unittest -v` → all PASS.
- [ ] **Step 5:** Review Focus 1, 2, 4 by hand with a temp `--config`: missing target dir is created; unknown skill name exits 2; missing config exits 2 with the example hint.
- [ ] **Step 6: Commit** `feat: add status and install with ownership, clash, drift guards`.

### Task 5: uninstall, orphans, CI, pre-commit, README

**Files:**
- Modify: `agent_skills.py`, `README.md`
- Create: `.github/workflows/check.yml`, `.pre-commit-config.yaml`

**Interfaces:**
- Consumes: `Target`, `Action`, `entry_state`, `apply_actions` (Task 4).
- Produces:
  - `find_orphans(repo: Path, target: Target) -> list[str]` — owned entries in `skills_dir` (symlink into this repo, or marker with `source == "agent-skills"`) whose name isn't in the target's selection or no longer exists in `skills/`.
  - `plan_uninstall(repo: Path, targets: list[Target], names: list[str]) -> list[Action]` — `remove` only for owned, non-drifted entries; skip otherwise with reason.
  - `status` prints orphans as `orphan`; CLI `uninstall [--config PATH] [--target T] [--dry-run] [--yes] names...`.

CI (`check.yml`): on push + pull_request; `permissions: contents: read`; matrix python `["3.9", "3.12"]` on `ubuntu-latest` with `actions/checkout@v4`, `actions/setup-python@v5`, run `python agent_skills.py check` and `python -m unittest -v`; separate job `gitleaks/gitleaks-action@v2` with `fetch-depth: 0`.
Pre-commit: `gitleaks` hook (pinned `rev`) + local hook `python3 agent_skills.py check`.
README: what it is; quick start for this Mac (link) and a work machine (copy, clone-only); config explanation; commands table; how to add a skill (`new` → edit → `check` → `install`); hooking up `working-style.md`; secret-scan setup.

- [ ] **Step 1:** Implement `find_orphans`, `plan_uninstall`, CLI wiring.
- [ ] **Step 2:** By hand in temp dirs: install, remove `alpha` from the target's `skills` list → `status` shows `orphan`; `uninstall alpha --yes` removes it; a dangling repo symlink also shows `orphan` (Review Focus 3).
- [ ] **Step 3:** `python3 -m unittest -v` and `python3 agent_skills.py check` → PASS / exit 0.
- [ ] **Step 4:** Write CI, pre-commit, README. If `gitleaks` is installed locally, run `gitleaks detect --source .` → no leaks; otherwise note it as not run.
- [ ] **Step 5: Commit** `feat: add uninstall, orphan reporting, CI, pre-commit, README`.

### Task 6: Install on this Mac and verify (owner in the loop)

- [ ] **Step 1:** Write local `config.ini`: `[target:claude] skills_dir = ~/.claude/skills`, `working_style = ~/.claude/working-style.md`, `mode = link`, `skills = *`.
- [ ] **Step 2:** `python3 agent_skills.py status` → expect `clash` for the three existing skills, `missing` for working-style.
- [ ] **Step 3 (owner):** Owner approves moving the three originals to `~/.claude/skills-backup-20261112/` (outside the skills dir so they aren't loaded twice).
- [ ] **Step 4:** `python3 agent_skills.py install --dry-run`, show plan, then `install --yes`; `status` → exit 0.
- [ ] **Step 5 (owner):** Owner approves the `~/.claude/CLAUDE.md` edit: add `@~/.claude/working-style.md`, a line keeping the learning record at `~/.claude/learning/record.md` and naming the learning tool, and remove the sections that moved.
- [ ] **Step 6:** Fresh-session check (owner runs a new Claude session): the three skills are listed and working-style rules are visible in loaded memory. Record result in `todo.md`/README if anything is off.
- [ ] **Step 7 (owner):** On explicit go-ahead only: `gh repo create torenunez/agent-skills --public --source . --push`.
