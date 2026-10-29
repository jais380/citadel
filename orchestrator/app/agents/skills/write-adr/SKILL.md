---
name: write-adr
description: Draft an Architecture Decision Record when a change makes a hard-to-reverse or cross-cutting choice. Use when a PR or discussion settles a design question someone will later ask "why?" about.
---

# Write an ADR

## When an ADR is needed

Yes:
- Choosing or replacing a framework, database, provider or protocol
- Changing a guardrail, the autonomy model, or data routing
- A schema or API shape that other parts depend on
- Accepting a known risk or trade-off on purpose

No: bug fixes, refactors that keep behavior, naming, formatting.

## Procedure

1. Copy `docs/adr/0000-template.md` to `docs/adr/NNNN-<kebab-title>.md` with the next number.
2. Fill it in:
   - **Context:** the forces and constraints, as facts. Quote the PR or discussion.
   - **Options:** at least two real alternatives, each with its main benefit and cost. "Do
     nothing" counts if it's genuinely viable.
   - **Decision:** the option and the one deciding reason.
   - **Consequences:** what gets easier, what gets harder, which risk is accepted and how
     it's mitigated, and what would make us revisit it.
3. Status is always **Proposed** when an agent writes it. Only the owner sets **Accepted**.
4. If it replaces an earlier ADR, set the old one to `Superseded by ADR NNNN` in the same PR,
   and link back.

## Rules

- Under one page. Specific beats thorough.
- Record what was decided and why, using only what the inputs show. If the reason isn't in the
  sources, leave a question instead of inventing one.
- ADRs are never edited after acceptance except their status line; a change of mind is a new ADR.
