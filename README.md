# Citadel

A personal, Dockerized AI workstation that runs a solo developer's engineering pipeline —
PM, developer, QA, reviewer, documenter — with one paid model and many free or local ones,
and only pulls me in when a decision needs me.

> Code orchestrates, models work. Paid model judges, free models produce. Tests are the real reviewer.

## What's in here (Phase 0)

```
citadel/
├── docker-compose.yml        local stack: OmniRoute, Postgres+pgvector, Redis, orchestrator
├── .env.example              every local setting, commented
├── Makefile                  make up | smoke | notify-test | pipeline | scorecard
├── db/init.sql               events, tasks, agent_runs, memory + model_scorecard view
├── orchestrator/             Python 3.12, FastAPI
│   └── app/
│       ├── agents/roles.yaml agent definitions (tier + prompt + output contract)
│       ├── llm.py            tier routing + the work-data rule, JSON parsing, run logging
│       ├── triage.py         Triage agent → Telegram
│       ├── pipeline_plain.py spec → code → tests → review loop, no framework
│       ├── main.py           /health, /events, /digest
│       └── smoke.py          ping every tier
├── infra/vps/                Caddy + n8n + Postgres + portfolio, for the server
└── docs/adr/                 decision records
```

## Model tiers

| Tier | Goes to | For |
|---|---|---|
| `brain` | OmniRoute combo `citadel-brain` (Claude) | specs, review |
| `worker` | OmniRoute combo `citadel-worker` (free coders) | code, tests |
| `cheap` | OmniRoute combo `citadel-cheap` (small free) | triage, docs |
| `private` | Ollama directly | anything `scope=work` |

`scope=work` is forced onto `brain` or `private` in `llm.resolve_tier()` — in code, not in a prompt.

## Quick start (local)

Prereqs: Docker + Compose v2, Ollama running with `OLLAMA_HOST=0.0.0.0`, models pulled:

```bash
ollama pull qwen2.5-coder:7b && ollama pull llama3.1:8b && ollama pull nomic-embed-text
```

Then:

```bash
cp .env.example .env              # fill in secrets (openssl rand -hex 32)
docker compose up -d omniroute    # then open http://localhost:20128/dashboard
#   1. add providers: Anthropic key, 3-4 free providers, Ollama (http://host.docker.internal:11434)
#   2. create combos: citadel-brain, citadel-worker, citadel-cheap
#   3. create an endpoint API key -> OMNIROUTE_API_KEY in .env
make up
make smoke                        # all four tiers should answer "pong"
make notify-test                  # Telegram should buzz
make pipeline TASK="Write a Python function that validates Nigerian phone numbers, with tests"
make scorecard                    # reviewer rejection rate per developer model
```

Each pipeline run writes `runs/<timestamp>/`: `spec.md`, then `round-N/` with the code,
`_test_output.txt` and `_review.json`.

## VPS (n8n, portfolio)

```bash
# on the server, in infra/vps/
cp .env.example .env              # DOMAIN, ACME_EMAIL, secrets, CITADEL_URL
docker compose up -d
```

DNS A records for `@`, `n8n`, `tools` must point at the server first. Then open
`https://n8n.<domain>`, create the owner account, and create an API key under
**Settings → n8n API**.

### Connecting n8n to the laptop

1. Both machines on the same Tailscale tailnet.
2. Laptop: set `ORCH_BIND=<tailscale ip -4>` in `.env`, then `make up`.
3. VPS: `curl http://<laptop-tailscale-ip>:8000/health` → `ok`.
4. n8n workflow: **Webhook** → **HTTP Request**
   - `POST {{$env.CITADEL_URL}}/events`
   - header `X-Citadel-Secret: {{$env.CITADEL_SECRET}}`
   - JSON body: `{"source": "github", "scope": "personal", "title": "...", "body": "...", "url": "..."}`
   - on error → **Telegram** node with the raw title (laptop is off; nothing gets lost)
5. A **Schedule** workflow at 08:00 and 18:00 → `POST {{$env.CITADEL_URL}}/digest` with the same header.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `private` tier fails in `make smoke` | Ollama only listens on 127.0.0.1 by default. Set `OLLAMA_HOST=0.0.0.0` and restart Ollama. |
| `brain`/`worker`/`cheap` fail with 401 | `OMNIROUTE_API_KEY` missing or wrong; recreate it in the dashboard. |
| 404 model not found | `MODEL_*` in `.env` must match the combo names exactly. |
| OmniRoute won't start | Its required env vars change between versions; compare with the OmniRoute repo's `.env.example`. |
| n8n can't reach the laptop | Check `tailscale status` on both; confirm `ORCH_BIND` is the laptop's Tailscale IP; laptop may be asleep. |
| Schema changes not applied | `init.sql` only runs on an empty volume: `make down && docker volume rm citadel_pg-data && make up`. |

## Safety notes

- Model-written tests run in a subprocess with an empty environment and a timeout. That's a
  Phase 0 stand-in: Phase 3 moves them into throwaway containers with no network.
- Merges, activating n8n workflows, and anything sent as me always wait for my approval.
- Claude is reached with an Anthropic API key with a spend limit set in the Console.

## Roadmap

1. Lazy inbox — GitHub/Jira/Slack/Gmail → Triage → Telegram, with digests
2. Documenter — merges produce changelog/ADR PRs
3. Pipeline on LangGraph — worktrees, containerized tests, approval interrupts, Langfuse tracing
4. MCP servers in TypeScript — `citadel-tasks`, `citadel-memory`, n8n MCP
5. Dashboard, Retro agent, workspaces, public metrics

## License

MIT
