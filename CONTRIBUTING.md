# Contributing to Citadel

Citadel is a personal project shared in the open. Issues and pull requests are welcome; the
bar is that every change keeps the system safe, tested and understandable.

## Setup

See the [README](README.md) quick start and [docs/runbooks/local-setup.md](docs/runbooks/local-setup.md).
Then:

```bash
cd orchestrator
uv sync
uv run pytest
```

## Branches

`<type>/<ticket>-<short-slug>`, for example `feat/CIT-12-event-envelope` or
`fix/CIT-30-triage-timeout`. No ticket? Use `feat/event-envelope`.

## Commit messages: Conventional Commits

```
<type>(<optional scope>): <imperative summary, max 72 chars>

<optional body: why, not what>

<optional footer: Refs CIT-12, BREAKING CHANGE: ...>
```

| Type | Use for | Changelog section |
|---|---|---|
| `feat` | New behavior | Added |
| `fix` | Bug fix | Fixed |
| `perf` | Faster, same behavior | Changed |
| `refactor` | Restructure, same behavior | (not listed) |
| `docs` | Documentation only | (not listed) |
| `test` | Tests only | (not listed) |
| `build` / `ci` | Dependencies, Docker, CI | (not listed) |
| `chore` | Anything else | (not listed) |
| `security` | Security fix | Security |

The Documenter agent builds the changelog from these types, and cycle-time metrics read PR
history, so the format matters.

## Pull requests

- One concern per PR. Keep diffs reviewable (aim for under ~400 changed lines).
- Fill in the PR template. "Risk" is not optional.
- CI must be green: ruff, mypy, pytest, gitleaks.
- Behavior changes need tests. Policy changes need an ADR and a guardrail test.
- Update `CHANGELOG.md` under `[Unreleased]` for user-visible changes.

## Decisions: ADRs

Write an ADR in `docs/adr/` when a choice is hard to reverse, affects several modules, or will
prompt "why did we do it this way?" later. Copy `0000-template.md`, take the next number, and
start it as `Proposed`.

## Review expectations

Reviewers check, in this order: guardrails untouched or properly changed; tests cover the
behavior; correctness; security; simplicity; naming and docs. Nits are labelled `nit:` and
never block a merge.

## Security issues

Do not open a public issue. See [SECURITY.md](SECURITY.md).
