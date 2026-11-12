---
name: docs-drift
description: Use on /docs-drift, before opening a PR that changes behavior, after merging one, or when asked to check the docs. Finds documentation that no longer matches the code, attacks its own findings and edits, and fixes the drift while keeping docs as short as they were, or shorter.
---

# Docs drift

Docs rot quietly: a removed feature still described, a renamed step, two files that disagree. Find that drift for a range of changes and fix it, without making anything longer. Concise and minimal is the house style; a fix that adds three sentences where one word would do is a new problem.

## 1. Scope the change

- Default range: `git merge-base main HEAD..HEAD` on a branch; on `main`, since the last merge; or the range the user names.
- From the **code** diff (not the docs), list what behavior changed: features added or removed, renamed things, commands, options, defaults, limits, files.

## 2. Know the docs

- Read the repo's agent instructions (`AGENTS.md`, `CLAUDE.md`, or similar) for its docs list and its style and vocabulary rules.
- Check current-state docs only. History is exempt: dated decision logs, progress logs, archived plans, decisions marked "Replaced".

## 3. Find drift, both directions

- For each behavior change, grep the docs for claims about it.
- For each doc claim touching the changed areas, check it in the code.
- Classes:
  - **wrong:** says something the code doesn't do;
  - **stale:** a removed thing described as current;
  - **missing:** only where a reader needs the fact to use or run the thing;
  - **contradiction:** two docs disagree;
  - **broken:** a link or anchor that goes nowhere;
  - **numbers:** counts, limits, or versions that changed.

## 4. Attack it (adversarial pass)

- **Each finding:** verify it in the code, or drop it.
- **Each proposed edit:**
  - Is it true?
  - Is it the shortest fix? Replace or delete before adding.
  - Does the fact already live elsewhere? Link instead of repeating it.
  - Does it belong in this doc? Requirements live in PRDs, designs in specs, order in the roadmap, results in progress, boundaries in the architecture doc, files in the manifest.
- **Big ranges** (a release, or about 20+ changed files), or when the user asks: give the findings and edits to a fresh subagent to attack instead (or do a separate attack pass yourself if subagents aren't available).

## 5. Minimalism guard

- A file's word count shouldn't grow unless a missing fact demands it.
- No new sections for small facts, no history in current-state docs, no restating the code, no caveats nobody needs.
- Count words before and after (`wc -w`) for every file you touch.

## 6. Fix and report

- Make the edits and run the repo's checks (tests that read docs, such as a code manifest).
- Commit in the PR the change belongs to, or a small docs PR.
- Report in one short table: found · fixed · declined (why) · word change per file.

Never rewrite a doc's style wholesale, touch history, invent facts, or add tutorials.
