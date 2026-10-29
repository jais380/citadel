@AGENTS.md

## Working agreement for Claude Code

This is a learning project. The owner wants to understand and improve the code himself, so
explaining matters as much as producing.

For any non-trivial task, follow this order and stop at each gate:

1. **Read first.** Read the relevant files and docs before proposing anything.
2. **Propose.** Describe the approach in a few bullets: files touched, why this design, what
   the alternatives were.
3. **Ask.** List open questions. Don't assume anything about requirements, naming or scope.
   Wait for answers.
4. **Implement.** Small diffs. Add inline comments where the *why* isn't obvious.
5. **Summarize.** What changed, how it was verified, what's left, and one thing worth learning
   from the change.

Additional rules:

- Use plan mode for anything touching guardrails, the database schema, `llm.py`, or `infra/`.
- Run `docker context show` before any docker command; it must be `desktop-linux`.
- Prefer showing the owner how to do a step over doing it, when he asks to learn something.
- Never claim a check passed without running it.
