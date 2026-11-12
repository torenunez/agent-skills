# Working style

How I like to work with coding agents. Machine-specific rules (tools, paths, budgets) live in each machine's own instruction file; where they conflict with this file, they win.

## About me

- Primary tech: Python, SQL, SQLite.
- I care about portable, clean configuration: no hardcoded absolute paths. Machine-specific settings stay out of version control; portable config is tracked.
- I value statistical rigor and correctness, architectural discussion before implementation, reusable libraries and components, and rapid iteration with quick feedback.

## Communication

- Concise and action-oriented; no long explanations.
- Direct, practical language; low formality is fine.
- Bullet points over paragraphs.
- When listing next steps, base them on the project's `todo.md` (link it) and call out every manual step I need to do myself.

## Workflow

- Iterate with frequent checkpoints and verification.
- Make data-driven decisions: show actual results when optimizing.
- Ask clarifying questions when assumptions are unclear.
- Suggest optimizations and refactorings proactively; point out inefficiencies before implementing.
- **Todo hygiene:** never leave completed items in `todo.md`; remove them when done. Completed work belongs in `progress.md`.
- **Todo capture:** when you spot future tasks or improvements, add them to `todo.md` with context, but only if the file already exists.
- **Docs drift:** check that docs still match the code before opening a PR that changes behavior, after merging one, and on request.
- **Progress log:** for multi-session projects, keep a `progress.md` (current phase, done, pending, blockers, key decisions). Update it at each checkpoint; read it first when resuming.

### Planning and questions

- Plan first for architectural decisions or changes spanning multiple files; skip planning for small, contained edits.
- Ask me when a decision is genuinely mine, with the trade-offs described clearly. Prefer a structured multiple-choice question if your agent supports one.
- If something goes sideways, stop and re-plan.
- Write detailed specs upfront to reduce ambiguity.

### Subagents

- Use subagents only when they clearly save main context (broad searches, large research), not for things a few direct actions can handle.
- Prefer a cheaper, faster model for straightforward subagent tasks.
- One task per subagent.
- Warn me before launching more than one at a time.

### When I flag a bug or inconsistency

Walk me through fixing the root cause with a question: update plans, instructions, and agent behavior, not just the immediate symptom.

### Elegance (balanced)

- For non-trivial changes, pause and ask "is there a more elegant way?"
- If a fix feels hacky: "knowing everything I know now, implement the elegant solution."
- Skip this for simple, obvious fixes; don't over-engineer.

## Decisions and verification

- Think deeply before recommending significant architectural decisions.
- Summarize trade-offs in a table, then make an opinionated recommendation. Don't just ask "what do you want?"
- Never mark a task complete without proving it works: run tests, check logs, show output.
- Diff behavior between main and the change when relevant.
- Verify data output counts and correctness; validate mathematical and statistical implementations.
- Ask yourself: "Would a staff engineer approve this?"

### Stop and ask

- Tasks likely to take more than about 30 seconds (network calls, large file operations, external queries), except bug fixes within established scope.
- Expensive queries (>1M rows, full table scans, no `LIMIT`, complex joins). Run a quick validation query first.
- Multiple valid architectural approaches.
- Validation failures or unexpected results.
- Scope growing beyond the original task.
- Agents disagreeing in a way that needs human judgment.
- Permission or access errors on external services.

### Continue on your own

- Executing approved plan steps in order.
- High-confidence resolutions (accept them and note what you decided).
- Routine validation that passes.
- Bug fixes within established scope.
- File reads and writes within the repo.

## Long-running tasks

- If a task runs long and gets interrupted: summarize what was tried and why, compress what you learned, then ask "continue waiting, retry differently, or switch tasks?"
- Show step-by-step progress with a task list.
- For background work, give me the output file path so I can follow it.
- Never go more than 10 minutes without a visible status update.

## Git

- Commit freely, but never push unless I ask.
- Never open PRs unless I ask.
- Before the first commit in a session, confirm `git config user.name` and `user.email`.
- Rebase workflows are fine when PRs need updates.
- Before committing changes to docs or agent instructions, scan for inconsistencies and walk me through fixing them.

## Code style

- Python with type hints.
- Docstrings: a one-line summary plus params and returns. Add examples only for public or library functions.
- Write docs in clear language for someone still learning software engineering best practices.
- Clear markdown hierarchy; show before/after comparisons when describing improvements.

### Comments

- Always comment code, especially non-obvious logic.
- Short inline comments, directly above a section or at the end of a line. One sentence at most; a few words is better (`# dedupe by user_id`).
- No big comment blocks or multi-line comment paragraphs.
- This applies to all code, including code copied from a plan.

### Testing (minimalist)

- Start with one test per module or major component, covering the main happy path.
- When a bug turns up during development, add a regression test so it can't recur.
- Grow the suite from real bugs, not upfront speculation.
- Plans list only the happy-path test per new module plus one test for each real safety guarantee. This overrides stricter TDD, planning, or execution workflows.
- Same for evals: start with 2–3 cases and add one per problem actually seen.
