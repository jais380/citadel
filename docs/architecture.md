# Architecture

Events enter through n8n on the VPS; every model call, agent and file lives on the laptop; the
owner is pulled in through Telegram only when a decision needs him.

```
 GitHub ─┐                ┌──────── VPS ────────┐
 Jira ───┤  webhooks  →   │ Caddy → n8n         │
 Slack ──┤                │       → portfolio    │
 Gmail ──┘                └─────────┬───────────┘
                                    │ Tailscale · POST /events (X-Citadel-Secret)
                 ┌──────────────────▼──────── Laptop · Docker Compose ─────────┐
                 │  Orchestrator (FastAPI :8000)                                │
                 │    ├── OmniRoute :20128   brain / worker / cheap tiers       │
                 │    ├── Ollama (host) :11434   private tier, embeddings      │
                 │    ├── Postgres + pgvector   events, tasks, runs, memory    │
                 │    ├── Redis   queue, rate limits (Phase 3)                 │
                 │    └── Sandboxes   tests in throwaway containers (Phase 3)  │
                 └──────────────────┬───────────────────────────────────────────┘
                                    ▼
                         Telegram: alerts, approvals, digests
```

## Principles

1. **Code orchestrates, models work.** The pipeline is a deterministic state machine. Models
   act only inside a step and never choose what runs next.
2. **Paid model judges, free models produce.** `brain` writes specs and reviews; `worker` and
   `cheap` draft, test, summarize and document.
3. **Tests are the real reviewer.** Gates run before any model gives an opinion.
4. **Work data stays private.** See ADR 0003.
5. **Humans gate the irreversible.** See `guardrails.md`.
6. **Measure everything.** Every model call writes an `agent_runs` row.

## Model tiers

| Tier | Route | Used for |
|---|---|---|
| `brain` | OmniRoute combo → Claude (API key) | Specs, task breakdown, review, retros |
| `worker` | OmniRoute combo of free coding models, ordered fallback | Code, tests, research |
| `cheap` | OmniRoute combo of small free models | Triage, summaries, docs |
| `private` | Ollama directly | Anything with `scope=work` that isn't `brain` |

## Workspaces and autonomy

A workspace groups projects that share rules. Its `autonomy` decides who writes code
(ADR 0002):

| | `ai_led` | `ai_assisted` |
|---|---|---|
| Writes code | Agents, owner approves | Engineers; agents suggest and review |
| Merge | Owner approval after all gates | Human review required |
| Default scope | `personal` | `work` |

## Flows

**Event flow (Phase 0–1):** source webhook → n8n normalizes to the event envelope
(`events.md`) → `POST /events` → Triage (`cheap`, or `private` for work) → `now` pings
Telegram, `digest` waits for the scheduled `/digest` call, `ignore` is stored only.

**Pipeline flow (Phase 0 plain loop → Phase 3 LangGraph):** task → PM spec (`brain`) →
[approval, Phase 3] → developer (`worker`) in an isolated workspace → gates (lint, types,
tests, security, load) → reviewer (`brain`) → `revise` loops back with reasons, at most
`PIPELINE_MAX_ROUNDS` → [approval] → PR.

## Where state lives

| State | Store |
|---|---|
| Events, tasks, agent runs, gate results, deployments, incidents | Postgres |
| Memory and embeddings | Postgres + pgvector (`memory.md`) |
| Provider keys and router config | OmniRoute volume (SQLite, encrypted) |
| Account credentials | n8n on the VPS (encrypted) |
| Run artifacts (spec, code, test output, review) | `runs/<timestamp>/` |
| Specs, ADRs, runbooks (source of truth) | Git |

## Ports

| Service | Host binding |
|---|---|
| OmniRoute dashboard + API | `127.0.0.1:20128` |
| Orchestrator | `${ORCH_BIND}:8000` (localhost or Tailscale IP) |
| Postgres | `127.0.0.1:5432` (or 5433 if Windows PostgreSQL is installed) |
| Ollama | host `:11434`, reached from containers at `host.docker.internal` |
