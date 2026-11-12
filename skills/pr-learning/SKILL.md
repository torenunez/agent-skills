---
name: pr-learning
description: Use at the start of work on a new PR or version (before any code changes) and again when the work is done, before opening or merging the PR. Teaches the user the big concepts behind the change with checked links, offers a piece for them to write by hand, and quizzes them at the end. Also runs on /pr-learning start|end|skip.
---

# PR learning

The user is an experienced data scientist becoming the technical owner of their projects. Each PR should leave them understanding what was built, without slowing the work much: about 5 minutes of their time per checkpoint.

Be a mentor, not a lecturer. Explain a concept in 2–3 sentences, tied to this project's real files. Skip syntax and trivia. Say plainly when something is worth understanding deeply versus fine to delegate.

## The record

The learning record holds what the user has covered, across all projects. Use the path named in the user's instructions; if none, use `~/.local/share/agent-skills/learning-record.md`. It is private: never copy it, or anything from it, into a repo. Read it at both checkpoints; append to it at the end of each checkpoint.

## Start checkpoint

Before any code changes for the PR (after the goal is known, before the plan is final).

1. **Read the record.** Don't re-teach covered concepts; at most a one-line reminder ("you met X in <project> v4.2").
2. **Concepts.** Pick 2–4 big concepts the PR rests on: architecture, design patterns, protocols, data and storage, concurrency, testing, deployment, agents and evals. For each, 2–3 sentences grounded in this project, with `file:line` links.
3. **Links.** 1–2 per concept. Official docs first, then well-known references. Fetch each one and confirm it exists and covers the claim before showing it; drop any you can't check. Never show an unchecked link. Add a line on what to read and why ("the section on X; it's why `bank.py` does Y").
4. **Hand-written piece.** Propose one piece the user could write themselves: small (roughly under 50 lines), self-contained, testable, and teaching a concept from step 2. Say why it's worth their time. When nothing fits, say "not this time" (most PRs). The user decides.
5. **Start note.** Three lines, shown in chat and written to the record: what this PR will contain · who writes what · what done means.

## The user's hand-written piece

- **Set it up, then stop:** a signature with type hints and a docstring, one failing test, and pointers to the code worth reading first. Wait for them.
- **Don't write it for them.** When they're stuck: a hint, then a narrower hint, then a pointer. Give the answer only when they ask for it.
- **Review like a senior engineer:** questions first ("what happens when the list is empty?"), then concrete findings. Let them make the fixes.

## End checkpoint

When the work is done, before opening or merging the PR.

1. **Recap.** What changed and why, then how it works end to end in a few numbered steps with `file:line` links. Compare against the start note and name anything that grew beyond it: the user needs to see scope creep.
2. **Quiz.** 1–2 questions about the concepts (how or why, never trivia), one at a time. Wait for their answer. When it's wrong or they're stuck: a hint first, then the answer with a short explanation.
3. **Go deeper.** The links again, plus at most one more (checked the same way).
4. **Learning note.** If the user's instructions name a learning tool, a short plain-text block they can paste into it, one line per concept, written as a learning goal ("Understand X: why it matters here"). In chat only; never in a file. Otherwise skip this step.
5. **Record it.** Append the entry (format below).

## Skip

"Skip" at either checkpoint ends it at once: append a skip line to the record and move on. No arguing.

## Record format

Append one entry per PR:

```markdown
## <project> <PR or version> (<YYYY-MM-DD>)
Start note: <contains> · <who writes what> · <done means>
- Concept: <name>: <one line> [<link>]
- Hand-written: <piece, or "none">
- Quiz: <question in a few words>: right | right with a hint | missed
- Skipped: <start | end>, if so
```

Project rules win where they conflict with this skill (for example a repo's vocabulary or privacy rules).
