# agent-skills: design

Date: 2026-11-12 · Owner: torenunez · Status: approved 2026-11-12

## 1. Intent

A public GitHub repo, `torenunez/agent-skills`, that holds:

1. **Skills the owner writes himself**, in a portable format any agent can read.
2. **A working-style document**: how the owner likes to work with agents (communication, testing, git, comments), written for any agent, not just Claude.
3. **A small installer** that puts both onto a machine.

Why: the owner built `pr-learning` on their personal Mac and it's stuck there. They want the same skills and working style on their work Mac, which has its own setup (company-managed skills, its own skill manager, Codex), without depending on that setup.

Guiding phrase from the owner: **independent but compatible.** The repo works on its own, and nothing in it fights the work setup.

## 2. Goals, non-goals, anti-goals

**Goals**
- One source of truth for the owner's own skills and working style.
- Install on the personal Mac as user-scoped Claude skills (`~/.claude/skills`).
- Install on the work Mac into whatever folders that machine's agents read (e.g. `~/.agents/skills`, `~/.claude/skills`), chosen by local config.
- Skills readable by Claude primarily, and by non-Claude agents (Codex etc.).
- Adding a new skill is one command plus writing it.

**Non-goals (v1)**
- Replacing or integrating with the work Mac's own skill manager or company-managed skills.
- Claude plugin marketplace packaging (`.claude-plugin/marketplace.json`). Noted for later.
- Behavioral evals of skills. Noted for later.
- Syncing anything else in `~/.claude` (settings, hooks, agents, commands).
- Windows support.

**Anti-goals (failure even if it "works")**
- Any machine-specific absolute path, username, or work/company reference committed to the repo.
- The installer overwriting or deleting anything it didn't install (company skills, hand edits).
- Two-way mirroring or `--delete`-style sync of `~/.claude`.
- The installer editing `CLAUDE.md` / `AGENTS.md` (the work Mac's has a company-managed block).
- Needing anything beyond stock Python to install.

## 3. Constraints

- **Pushes happen only from the personal Mac.** The work Mac doesn't push to personal GitHub accounts; it only clones/pulls this public repo.
- **Python 3.9+, standard library only.** This Mac's default `python3` is 3.9.6; the work Mac's default also lacks `tomllib`. So config is INI (`configparser`), not TOML.
- **macOS/POSIX.** Both machines are Macs.
- Public from day one, MIT license.
- the owner's code style (from their global instructions): type hints, one-line docstrings with params/returns, short inline comments, no comment blocks. Minimal tests: one happy-path test per module plus one per real safety guarantee.

## 4. Repo layout (decided)

```text
agent-skills/
  README.md                 what this is, quick start for both machines, how to add a skill
  LICENSE                   MIT
  AGENTS.md                 rules for agents editing THIS repo (no machine paths, no work refs, run check before commit)
  CLAUDE.md                 one line: @AGENTS.md
  working-style.md          the owner's portable working agreement
  skills/
    pr-learning/SKILL.md
    docs-drift/SKILL.md
    process-agent-feedback/SKILL.md
  templates/
    SKILL.md                template used by `new`
  config.example.ini        committed example; real config.ini is gitignored
  agent_skills.py           the installer/CLI (single file)
  tests/test_agent_skills.py
  .github/workflows/check.yml
  .pre-commit-config.yaml   gitleaks
  .gitignore                config.ini, __pycache__, etc.
  todo.md                   deferred items (marketplace, evals, ...)
  docs/design.md            this document
```

Skill format: Agent Skills standard. `skills/<name>/SKILL.md` with YAML frontmatter `name` (must equal folder name, lowercase, hyphens) and `description`. Optional `references/`, `scripts/`, `assets/` subfolders. This is the shape `npx skills add torenunez/agent-skills`, Claude, Codex, and most skill managers read.

## 5. Portability rules for skill content (decided)

- Describe the capability, not the tool: "fetch the page and confirm it exists", not "use WebFetch".
- No machine paths and no personal tool names hardwired. Where a skill needs a local detail, it states a neutral default and says "unless the user's instructions name a different one". Per-machine overrides live in that machine's `CLAUDE.md`/`AGENTS.md`, which agents already read. No new override mechanism.
- Concretely for `pr-learning`:
  - Record path: "the learning record path named in the user's instructions; if none, use `~/.local/share/agent-skills/learning-record.md`". This Mac's `CLAUDE.md` gets a line keeping the existing `~/.claude/learning/record.md`.
  - The tool-specific paste note becomes a generic "learning note to paste into the user's learning tool, if their instructions name one". This Mac's `CLAUDE.md` names the tool.
  - "WebFetch, or the web-fetch agent" becomes "fetch it".
- `docs-drift` and `process-agent-feedback` were checked: no personal paths or names. Copy as-is apart from any tool-name references.

## 6. working-style.md (decided)

Built from the portable sections of the owner's current `~/.claude/CLAUDE.md`:

| Moves to `working-style.md` | Stays local in this Mac's `CLAUDE.md` |
|---|---|
| Communication style | Browser preference (Claude in Chrome) |
| Workflow (iteration, checkpoints, todo/progress hygiene, docs drift) | Budget-conscious warnings |
| Plan mode / asking questions / elegance | Memory & session continuity (where to store memories) |
| Decision making, verification, decision checkpoints | `.claude/agents/` file-management rule |
| Git & version control | "Works across multiple macOS machines" environment notes |
| Code style, comments, testing (minimalist) | |
| What I value | |
| Long-running tasks | |

Wording: agent-neutral ("the agent", not "Claude"); Claude-plugin-specific references (e.g. naming superpowers skills) become generic ("planning or TDD skills").

Hook-up: the installer installs `working-style.md` to a configured file path per target (like a skill). The machine's instruction file references it:
- Claude: `@~/.claude/working-style.md` line in `~/.claude/CLAUDE.md` (Claude Code supports `@` imports).
- Codex / others: a line in their `AGENTS.md`: "Read and follow `<path>`." (no import support assumed).

The installer **prints** the exact line to add and never edits those files. Removing the moved sections from this Mac's `CLAUDE.md` is a manual step the owner approves.

## 7. Installer: `agent_skills.py` (decided)

Single-file, stdlib-only CLI. Run as `python3 agent_skills.py <command>` from the repo root.

**Config** (`config.ini`, gitignored; `config.example.ini` committed with placeholders):

```ini
[defaults]
mode = link            ; link | copy

[target:claude]
skills_dir = ~/.claude/skills
working_style = ~/.claude/working-style.md
skills = *             ; * or comma list, e.g. pr-learning, docs-drift

[target:codex]
skills_dir = ~/.agents/skills
mode = copy            ; per-target override
skills = pr-learning, docs-drift
```

`~` is expanded at runtime; nothing absolute is committed. A target without `working_style` skips it.

**Modes**
- `link`: symlink from the target to the repo folder. Edits in the repo are live immediately. Default on the personal Mac.
- `copy`: copy the folder. A `git pull` does not change installed skills until you run `install` again. Default on the work Mac.

**Ownership and safety** (the guarantees that matter)
- The installer only ever touches entries it installed. It knows an entry is its own when:
  - link mode: the symlink points into this repo checkout;
  - copy mode: the folder contains a marker file `.agent-skills.json` with `{source, commit, sha256}` (sha256 over the installed files, excluding the marker).
- **Clash**: target already has `<name>` that isn't ours → refuse that entry, report it, continue with the rest. Never overwrite.
- **Drift**: an owned copy whose current files no longer match its recorded sha256 (someone edited the installed copy) → refuse to update it, report it. Never overwrite hand edits.
- No `--force`. Resolving a clash or drift is a manual step the user does.
- Mode change for an owned entry (link ↔ copy) is allowed, since it's ours and unmodified.

**Commands**
| Command | What it does |
|---|---|
| `status` | Per target and skill: `installed`, `outdated` (copy differs from repo), `missing`, `drifted`, `clash`. Read-only. Exit 0 if all clean, 1 otherwise. |
| `install [--target T] [names...]` | Computes the plan (create / update / skip + reason), prints it, asks `Proceed? [y/N]`. `--yes` skips the prompt; `--dry-run` prints and exits. Afterwards prints the instruction-file line(s) for `working_style`. |
| `uninstall [--target T] names...` | Removes only owned, undrifted entries. Same plan/confirm flow. |
| `new <name>` | Creates `skills/<name>/SKILL.md` from `templates/SKILL.md`, name validated. |
| `check` | Lints the repo: each skill folder has exactly-cased `SKILL.md`; frontmatter has `name` == folder and `description`; name is lowercase-hyphen; no absolute `/Users/` or `/home/` paths in tracked files. Exit 1 on any failure. Used by CI and pre-commit. |

Frontmatter parsing: minimal (the `---` block, `key: value` single-line scalars). No PyYAML.

**Tests** (`unittest`, stdlib; run with `python3 -m unittest`): all in temp dirs, never real home folders.
1. Happy path: install (link and copy) into a temp target, `status` reports clean.
2. Clash: pre-existing foreign `<name>` in target is left untouched and reported.
3. Drift: edited installed copy is not overwritten on re-install.
4. `check` flags a name/folder mismatch.

## 8. CI and secret hygiene (decided)

- `.github/workflows/check.yml`: on push and PR, run `agent_skills.py check` and the unit tests on Python 3.9 and 3.12 (ubuntu), plus the gitleaks action. Pinned action versions, read-only permissions.
- `.pre-commit-config.yaml`: gitleaks hook and `agent_skills.py check`. Installing `pre-commit` is a manual step for the owner (optional; CI covers it).

## 9. Rollout

1. Build in `~/Development/agent-skills` on the personal Mac, local git only. Commit; don't push until the owner says so.
2. Install on this Mac (link mode, target `claude`). The three skills already exist as real folders in `~/.claude/skills`, so the first `install` will report **clash** for them. the owner moves the originals aside (manual step, e.g. to a backup folder), then installs.
3. the owner adds the `@~/.claude/working-style.md` import and the pr-learning overrides to `~/.claude/CLAUDE.md` and trims the moved sections (manual, or with the agent on their OK).
4. Verify in a fresh Claude session: skills listed, `working-style.md` loaded.
5. the owner creates the public GitHub repo and pushes (on their explicit go-ahead).
6. Work Mac (later, by the owner): `git clone`, write `config.ini` (copy mode, targets for its agent folders), `status`, `install`. Must not collide with company-managed skills; the clash rule guarantees no overwrite.

## 10. Left to the builder

- Exact CLI output formatting and help text.
- README wording and structure.
- Template `SKILL.md` contents.
- The exact wording of `working-style.md`, as long as it follows section 6.
- Exit codes beyond those stated.

## 11. Later (goes in todo.md)

- `.claude-plugin/marketplace.json` packaging (wshobson/agents style) once there are ~10 skills.
- 2–3 eval cases per skill, added when a skill misbehaves (with/without comparison, samber style).
- `UPSTREAM.md` provenance if a third-party skill is ever vendored.
- Work Mac rollout notes once tried.

## 12. Builder-check answers and builder calls

Answered:
- **Skill sources:** copy from the current `~/.claude/skills/{pr-learning,docs-drift,process-agent-feedback}/SKILL.md` on the personal Mac (read and checked 2026-11-12: only `pr-learning` has personal references, listed in section 5).

Builder calls (owner can override):
- **Moving originals aside** stays manual. On a clash, `install`/`status` print a suggested `mv <path> <path>.bak-YYYYMMDD` but never run it.
- **working-style.md, unlisted sections:** Subagents (rewritten model-neutral: "prefer a cheaper model"), Self-Improvement, Continue Independently move. File Management (`.claude/agents/`) stays local. Tool names like AskUserQuestion become "ask the user with a structured question".
- **working_style ownership:** link mode = file symlink into the repo. Copy mode = file copy plus a sidecar marker `<file>.agent-skills.json` (same fields as the folder marker).
- **Hash definition:** sha256 over sorted relative POSIX paths, each as `path NUL sha256(bytes) LF`; file modes ignored; markers excluded; symlinks inside a skill are refused by `check`.
- **commit:** `git rev-parse HEAD` if available, else `null`.
- **Orphans:** an owned install whose skill was removed from the repo or from the target's `skills` list shows as `orphan` in `status`; `uninstall <name>` removes it. `install` never removes anything.
- **CI Python:** `actions/setup-python` with 3.9 and 3.12; pinned major versions.
- **Public-doc hygiene:** this doc ships as `docs/design.md`, so it names no company tools or private paths.
- **Commit identity (owner decision):** repo-local git config uses the GitHub noreply address (`<id>+torenunez@users.noreply.github.com`), never the global email.
