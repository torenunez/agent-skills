# agent-skills

My portable agent skills, a working-style doc that tells agents how I like to work, and a small installer that puts both on each of my machines.

- **Skills** live in `skills/<name>/SKILL.md` (the [Agent Skills](https://agentskills.io) format). Claude, Codex, and other agents read them, and so do tools like `npx skills add torenunez/agent-skills`.
- **[working-style.md](working-style.md)** is my working agreement: communication, planning, testing, git, comments. Each machine's agent instruction file points to it.
- **[agent_skills.py](agent_skills.py)** installs them. It needs only Python 3.9+ with no extra packages.

Design and reasoning: [docs/design.md](docs/design.md).

## Skills

| Skill | Use it when |
|---|---|
| [pr-learning](skills/pr-learning/SKILL.md) | Starting and finishing a PR: learn the concepts behind the change, then get quizzed |
| [docs-drift](skills/docs-drift/SKILL.md) | Before or after a PR that changes behavior: find and fix docs that no longer match the code |
| [process-agent-feedback](skills/process-agent-feedback/SKILL.md) | Weighing review feedback from other agents or people |

## Quick start

```bash
git clone https://github.com/torenunez/agent-skills.git ~/Development/agent-skills
cd ~/Development/agent-skills
cp config.example.ini config.ini   # then edit for this machine
python3 agent_skills.py status
python3 agent_skills.py install --dry-run
python3 agent_skills.py install
```

`install` prints its plan and asks before changing anything.

### Link or copy?

| Mode | What happens | Good for |
|---|---|---|
| `link` | Symlinks into this repo. Edits here are live right away. | The machine where you write skills |
| `copy` | Copies files. A `git pull` changes nothing until you run `install` again. | Machines that only consume skills |

### Config

`config.ini` is gitignored, so each machine has its own. Each `[target:<name>]` section is one folder an agent reads skills from:

```ini
[defaults]
mode = link

[target:claude]
skills_dir = ~/.claude/skills
working_style = ~/.claude/working-style.md
skills = *                 ; or a comma list

[target:agents]            ; e.g. a work machine with other agents
skills_dir = ~/.agents/skills
mode = copy
skills = pr-learning, docs-drift
```

### Hook up the working style

After an install, the installer prints the line to add. It never edits your instruction files itself.

- Claude, in `~/.claude/CLAUDE.md`: `@~/.claude/working-style.md`
- Other agents, in their `AGENTS.md`: `Read and follow ~/.claude/working-style.md.`

Machine-specific rules (paths, preferred tools, budgets) stay in that machine's own file, which wins if the two conflict. Skills that need a local detail say so. For example, `pr-learning` reads its learning-record path and learning tool from your instructions.

### Optional: pr-learning hooks (Claude Code)

To make pr-learning's checkpoints hard to skip in a project, add this to that project's `.claude/settings.local.json` (personal and gitignored, so a public repo stays clean). Point `--record` at your learning record:

```json
{
  "hooks": {
    "PostToolUse": [{ "matcher": "Bash", "hooks": [{ "type": "command", "timeout": 10,
      "command": "python3 ~/.claude/skills/pr-learning/scripts/pr_learning_hook.py branch --record ~/path/to/record.md" }] }],
    "PreToolUse": [{ "matcher": "Bash", "hooks": [{ "type": "command", "timeout": 20,
      "command": "python3 ~/.claude/skills/pr-learning/scripts/pr_learning_hook.py gate --record ~/path/to/record.md" }] }]
  }
}
```

- **After `git checkout -b`, `git switch -c`, or `git worktree add -b`:** Claude is told to run the start checkpoint.
- **Before `gh pr create` or `gh pr merge`:** the command is blocked until the record has an end entry for that branch. Merging by PR number looks up the branch with `gh`; if that fails, you're asked instead.
- **A bug in the hook never blocks work:** it lets the command through and shows an error.

## Commands

| Command | What it does |
|---|---|
| `status` | Lists every entry as `installed`, `outdated`, `missing`, `drifted`, `clash`, or `orphan`. Read-only. Exits 1 if anything isn't installed. |
| `install [names…]` | Plans, confirms, then links or copies. Options: `--dry-run`, `--yes`, `--target T`. |
| `uninstall names…` | Removes entries this tool installed. |
| `new <name>` | Creates `skills/<name>/SKILL.md` from the template. |
| `check` | Checks skill names and frontmatter, and scans for machine-specific paths. |

### What it will never do

- **Overwrite something it didn't install.** A same-named folder that came from somewhere else (`clash`) is left alone, and the `install` plan prints a suggested `mv` for you to run.
- **Overwrite a copy you edited by hand.** A `drifted` copy is skipped.
- **Edit `CLAUDE.md` or `AGENTS.md`.**

There's no `--force`. You resolve clashes and drift yourself.

How it knows what it owns: in link mode, the symlink points into this repo. In copy mode, a `.agent-skills.json` marker records a hash of what was installed.

## Adding a skill

```bash
python3 agent_skills.py new my-skill   # edit skills/my-skill/SKILL.md
python3 agent_skills.py check
python3 agent_skills.py install my-skill
```

Rules for skill content are in [AGENTS.md](AGENTS.md). In short: describe capabilities, not tool names, and keep anything machine-specific out.

## Development

```bash
python3 -m unittest -v
python3 agent_skills.py check
```

CI runs both on macOS's built-in `python3` (3.9) and on Python 3.12, plus a [gitleaks](https://github.com/gitleaks/gitleaks) secret scan. To run the same checks before every commit, install [pre-commit](https://pre-commit.com) and then run `pre-commit install`.

Ideas for later: [todo.md](todo.md).

## License

MIT
