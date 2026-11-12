# Working in this repo

This is a public repo of portable agent skills, a working-style doc, and a small installer.

## Rules

- **Nothing machine-specific.** No absolute home paths, usernames, emails, or work/company names. Use `~` in examples. `check` scans for home paths.
- **Skills describe capabilities, not tools.** Write "fetch the page and confirm it exists", not a specific tool name. Agents other than Claude read these too.
- **Local details stay local.** When a skill needs a path or personal tool, give a neutral default and say "unless the user's instructions name a different one". The override goes in that machine's own `CLAUDE.md` / `AGENTS.md`, never here.
- **Skill format:** `skills/<name>/SKILL.md`, frontmatter `name` equal to the folder name (lowercase, hyphens) plus a `description` that says when to use it. Start a new one with `python3 agent_skills.py new <name>`.
- **Installer:** stdlib only, Python 3.9+. It must never overwrite or delete anything it didn't install. No `--force`.
- **Before committing:** run `python3 agent_skills.py check` and `python3 -m unittest`.
- Follow `working-style.md` for how to work with the owner.
