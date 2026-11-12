---
name: code-comments
description: Use after writing or changing code, before committing, and whenever the user gives feedback on code comments. Measures comment density, attacks each comment for truth and relevance, and grows a library of the user's before/after examples so their feedback compounds.
---

# Code comments

The goal is code a newcomer can follow by reading only the comments, top to bottom. Use many short comments of a few words each, every one about its own line. Aim for about **1 comment per 5 code lines** (imports and docstrings don't count). That's a guideline, not a quota.

Before starting, read `references/examples.md` in this skill's folder. It holds the user's own before/after pairs, and they outrank the general advice here.

Only code you wrote or changed is in scope. Don't re-comment untouched code unless asked.

## 1. Measure

For Python, run `python3 <this skill's folder>/scripts/comment_density.py <changed files>`. It reports three things:
- comments per code line, against the target;
- sparse functions;
- **gaps**: 8 or more code lines in a row with no comment.

For other languages, apply the same targets by eye.

## 2. Write

A good comment says something the line doesn't:
- **Why the line or value exists:** `# floor: no divide-by-zero if two points overlap`
- **What a number means, with units:** `# ~6px per character, plus padding`
- **The idea behind a step:** `# cool down: smaller moves each round so it settles`
- **An assumption or edge case:** `# ids are unique per map, not globally`

Put it at the end of the line when it fits, otherwise directly above the line or short block it explains. Use a few words, never more than one sentence, and no comment blocks.

Never:
- restate the syntax (`# loop over items`);
- explain a neighboring line;
- narrate history ("changed to fix the bug");
- leave a vague TODO.

## 3. Attack

Try to break every comment in the changed code:

1. **True?** Read the line. Does it do exactly what the comment says? A wrong comment is worse than none.
2. **About this line?** It should sit on or directly above the line it explains, not on a loop header or a neighbor.
3. **Adds something?** If deleting it loses nothing the code already says, rewrite it to say *why*.
4. **Specific?** If it would fit equally well on another line, it's too generic.
5. **Numbers explained?** Every non-obvious literal needs its meaning or unit.
6. **Story test:** read only the comments. Do they explain what the code does and why?

Fix whatever fails, then measure again.

For big changes (about 300+ changed lines or 20+ files), hand the changed code and these six questions to a fresh subagent if one is available. Otherwise, do the attack as a separate pass after writing.

## 4. Learn from feedback

When the user critiques comments (too vague, in the wrong place, too many or too few, wording):

1. Fix what they pointed at, and the same pattern elsewhere in the change.
2. Propose a new entry for `references/examples.md`: a generalized before/after plus a one-line lesson. Rename identifiers, and leave out private code, names, and data. Show it, and add it once they approve.
3. If the new entry duplicates or contradicts an existing one, merge or replace that one, with the newer lesson winning. Keep the file to about 20 entries.
4. If the feedback changes a rule (like the density target), propose an edit to this skill or the user's working-style doc instead.

This skill's folder may be a link into a git checkout. If it is, edit the checkout and commit, but don't push unless the user asks. If it's an installed copy, tell the user the change belongs in the source repo.

## Report

One line: density before → after, any gaps left, and any examples added.
