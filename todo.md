# Todo

- Package as a Claude plugin marketplace (`.claude-plugin/marketplace.json`, topic-grouped like wshobson/agents) once there are ~10 skills.
- Add 2–3 eval cases per skill when one misbehaves (with vs. without the skill).
- Add `UPSTREAM.md` provenance (pinned commit + license) if a third-party skill is ever vendored.
- Write work-machine rollout notes after the first install there.

## CI

- Bump `actions/checkout@v4` / `actions/setup-python@v5` to their Node 24 releases (CI warns Node 20 is deprecated).

## Installer polish (from the v1 review)

- Catch `configparser.Error` in `load_config` so a malformed `config.ini` exits 2 cleanly instead of a traceback.
- `status`: print the suggested `mv` for clashes (install's plan already does), and tailor the orphan hint when the orphan is drifted (uninstall refuses those).
- Report a `working_style` file as orphan when it's removed from a target's config; today it must be deleted by hand.
- README: after moving the repo checkout, old links show as `clash`; note to delete them and reinstall.
- Store the planning `state` on `Action` instead of matching reason text in `cmd_install`/`cmd_uninstall`.
- Happy-path test: also assert every entry's state is `installed`.
