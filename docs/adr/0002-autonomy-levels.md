# ADR 0002: One system with per-workspace autonomy levels

- Status: Accepted
- Date: 2026-10-26

## Context

Citadel serves two futures. For personal projects, agents should do most of the building
(AI-led). For a future company, and for some employed or freelance work, engineers write the
code and AI assists: reviewing, testing, documenting, removing repetitive work. Quality,
reliability and security matter more than speed in both.

## Options

1. **Two systems.** A personal Citadel and a later company tool. Each fits its use exactly,
   but everything shared (events, memory, docs, gates, metrics) gets built twice and drifts.
2. **One system, autonomy as a setting.** Each workspace has `autonomy = ai_led | ai_assisted`.
   Shared parts are built once; only who writes code changes.

## Decision

Option 2. A `workspaces` table carries `autonomy` and `default_scope`, and every permission
decision goes through `policy.py` (`can_write_code`, `requires_human_merge`, `allowed_tiers`).

| | `ai_led` | `ai_assisted` |
|---|---|---|
| Writes code | Agents; owner approves | Engineers; agents suggest |
| Agents do | Spec, build, test, review, document | Second review, tests, docs, triage |
| Merge | Owner approval after all gates | Human code review required |
| Gates | Block | Block, for humans and agents alike |

For employed and freelance work, the employer's or client's AI policy sets the level, not the
owner's preference.

## Consequences

- The company starts with a working system: memory, docs, gates and metrics already proven.
- Every feature must ask "what does this do in `ai_assisted` mode?" — slightly more design
  work per feature.
- Permission logic must never be scattered; a check outside `policy.py` is a bug.
