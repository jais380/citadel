# AGENTS.md — working on Citadel

Read this before changing anything in this repo. It applies to every coding agent (Claude Code,
Codex, Citadel's own agents) and to humans.

Citadel is a personal, Dockerized AI workstation that runs a solo developer's engineering
pipeline (PM → developer → QA → reviewer → documenter) with one paid model and many free or
local ones. Code orchestrates; models only act inside a step.

## Non-negotiables

1. **Guardrails live in code.** Never weaken, bypass or "temporarily disable" a check listed in
   [docs/guardrails.md](docs/guardrails.md). Changing a guardrail needs an ADR, a test, and the
   owner's explicit approval.
2. **`scope=work` never reaches the `worker` or `cheap` tiers.** Work data goes only to `brain`
   (Claude via API key) or `private` (local Ollama).
3. **No secrets anywhere but `.env`.** Not in code, prompts, logs, tests, fixtures, commit
   messages or docs. Use obviously fake values in examples (`sk-test-000`).
4. **Tests never call real models or the network.** Use the fake LLM fixture.
5. **Never** push to `main`, merge a PR, activate an n8n workflow, or send a message as the owner.
6. **Ask first** before: adding a dependency, changing the database schema, changing a
   guardrail, deleting files, or changing anything under `infra/`.
7. **Model output is untrusted input.** Parse it, validate it, bound it. Never `eval` it, never
   use a model-supplied path without the workspace check, never let it pick a tier.

## Repo map

```
citadel/
├── AGENTS.md                 ← you are here
├── docker-compose.yml        local stack: OmniRoute, Postgres+pgvector, Redis, orchestrator
├── Makefile                  task shortcuts (works in PowerShell with GNU make)
├── db/init.sql               schema (until Alembic migrations replace it)
├── orchestrator/             Python 3.12, managed with uv
│   ├── pyproject.toml, uv.lock
│   └── app/
│       ├── config.py         ALL settings; nothing else reads os.environ
│       ├── llm.py            the ONLY place that calls models: tier routing, JSON parsing, run logging
│       ├── db.py             Postgres helpers; parameterized SQL only
│       ├── roles.py          loads agents/roles.yaml
│       ├── triage.py         Triage agent
│       ├── pipeline_plain.py spec → code → tests → review loop (reference implementation)
│       ├── main.py           HTTP API: /health, /events, /digest
│       └── agents/
│           ├── roles.yaml    agent = tier + prompt + skills + output contract
│           ├── prompts/      system prompts, one file per agent
│           └── skills/       on-demand procedures (Agent Skills format)
├── docs/                     architecture, guardrails, events, metrics, memory, ADRs, runbooks
├── templates/project/        AGENTS.md template for repos Citadel works on
├── infra/vps/                server stack: Caddy, n8n, portfolio
└── local/                    git-ignored personal/workplace overlays (see local.example/)
```

## Commands

Run from the repo root unless noted. The owner develops on Windows (PowerShell); every command
here works there.

| Task | Command |
|---|---|
| Start / stop the stack | `make up` / `make down` |
| Follow logs | `make logs` |
| Ping every model tier | `make smoke` |
| Run the pipeline once | `make pipeline TASK="..."` |
| SQL shell | `make psql` |
| Install deps locally | `cd orchestrator; uv sync` |
| Tests | `cd orchestrator; uv run pytest` |
| Lint + format check | `cd orchestrator; uv run ruff check .; uv run ruff format --check .` |
| Types | `cd orchestrator; uv run mypy app` |
| Add a dependency (ask first) | `cd orchestrator; uv add <pkg>` then `make rebuild` |

Before any `docker` command, `docker context show` must print `desktop-linux`. Never run this
project against another context.

## How to make a change

1. **Read the doc for the area first.**

   | Touching | Read |
   |---|---|
   | Tiers, scope, autonomy, permissions | `docs/guardrails.md`, `docs/adr/0003-work-data-routing.md` |
   | Incoming events, n8n payloads | `docs/events.md` |
   | Metrics, `agent_runs`, deployments | `docs/metrics.md` |
   | Memory, search, embeddings | `docs/memory.md` |
   | Overall structure | `docs/architecture.md` |

2. **One concern per change.** A PR that fixes a bug and refactors a module is two PRs.
3. **Test first for behavior changes.** Write the failing test, then the code.
4. **Run the checks** (ruff, mypy, pytest) before saying a change is done.
5. **Update docs in the same change:** `CHANGELOG.md` for anything user-visible, an ADR for any
   decision someone might later ask "why?" about, `docs/guardrails.md` for any policy change.
6. **Commit with Conventional Commits** (see `CONTRIBUTING.md`).

## Code conventions

- Python 3.12, type hints on every function, mypy clean, ruff for lint and format.
- **Settings:** only through `config.settings()`.
- **Models:** only through `llm.chat()` / `llm.chat_json()`. Never construct an OpenAI client
  elsewhere; that's where routing, the scope rule and run logging live.
- **SQL:** parameterized only (`%s` placeholders). Never build SQL with f-strings or `+`.
- **Failure policy:** logging and metrics fail open (warn and continue). Policy checks fail
  closed (raise). If a guardrail can't be evaluated, the action doesn't happen.
- **Agents are config.** Prompts live in `agents/prompts/*.md`, not in Python strings.
- **Small functions, plain names, no cleverness.** This repo is also a learning project and a
  portfolio piece; code is read more than written.
- **Comments explain why, not what.**

## Adding an agent

1. Write `agents/prompts/<name>.md`. State the role, inputs, rules, and an exact output contract.
2. Add an entry to `roles.yaml` with `tier`, `prompt`, and optional `skills`.
3. Add a test with the fake LLM covering a valid reply and a malformed reply.
4. If it handles work data or takes actions, add its rules to `docs/guardrails.md`.

## Adding a skill

1. Create `agents/skills/<name>/SKILL.md` with frontmatter `name` (matches the folder) and
   `description` (one sentence: what it does and when to use it).
2. Keep the body a procedure plus a checklist, under ~150 lines. Free models have small context.
3. Reference it from the agents that need it in `roles.yaml`.

## Definition of done

- [ ] Tests added or updated; `uv run pytest` passes
- [ ] `ruff check`, `ruff format --check`, `mypy app` pass
- [ ] No secrets, employer names or internal URLs in the diff
- [ ] Docs updated (changelog / ADR / guardrails as applicable)
- [ ] Conventional commit message

## Known gotchas

- `db/init.sql` only runs on an empty volume. To re-apply: `make down`, `docker volume rm citadel_pg-data`, `make up`.
- Ollama must listen on `0.0.0.0` (`OLLAMA_HOST`) or the `private` tier fails from containers.
- Windows: `.env` saved as `.env.txt`; `curl` is an alias, use `curl.exe`; set
  `git config --global core.autocrlf input`; a Windows PostgreSQL install clashes with port 5432.
- OmniRoute's required env vars change between versions; compare with its own `.env.example`.

More in [docs/runbooks/local-setup.md](docs/runbooks/local-setup.md).
