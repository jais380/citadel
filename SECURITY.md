# Security

## Reporting a vulnerability

Please report privately through GitHub: **Security → Report a vulnerability** on this
repository. Don't open a public issue. Expect an acknowledgement within 7 days.

Only the `main` branch is supported.

## Threat model

Citadel holds model provider keys, connects to personal and work accounts through n8n, and
runs code written by models. That shapes everything below.

### Assets

| Asset | Where it lives |
|---|---|
| Model provider keys | OmniRoute (encrypted at rest), `.env` |
| Account credentials (GitHub, Gmail, Slack, Jira, Telegram) | n8n credential store, encrypted with `N8N_ENCRYPTION_KEY` |
| Work data (employer code, messages, tickets) | Events and memory tables, tagged `scope=work` |
| Source repositories | Local disk, GitHub |
| The owner's identity | Anything that can send messages or push code as the owner |

### Threats and mitigations

| Threat | Mitigation | Status |
|---|---|---|
| **Prompt injection** via email, Slack, PR comments or web pages ("ignore your instructions and…") | Event content is passed to models as data; agents that read external content have no tools that act; every outward action needs human approval | Partial: Triage has no tools; approval gates arrive in Phase 3 |
| **Model-written code doing harm** when tests run | Tests run with an empty environment and a timeout; Phase 3 moves them into throwaway containers with no network and no mounted secrets | Partial |
| **Work data reaching third-party free models** | Scope routing enforced in code (`resolve_tier`), covered by tests | Enforced |
| **Secret leakage** in code, logs or commits | `.env` only; gitleaks in CI; secrets never logged or sent to models | Partial: gitleaks arrives with CI |
| **Exposed endpoints** | Orchestrator binds to localhost or the Tailscale IP only; `/events` requires a shared secret compared in constant time; OmniRoute and Postgres bound to 127.0.0.1 | Enforced |
| **Path traversal** from model-supplied file paths | Paths validated against the workspace root before writing | Enforced |
| **Supply chain** (malicious or vulnerable dependencies) | Locked dependencies (`uv.lock`); pip-audit / npm audit in the security gate; pinned image tags | Planned (Phase 3) |
| **Runaway spend** | Spend limit set in the Anthropic Console; per-run token logging | Partial |
| **Lost n8n encryption key** | Key backed up in a password manager, outside the server | Manual |

## Self-hosting checklist

- [ ] `.env` files never committed; `git check-ignore .env` prints `.env`
- [ ] Anthropic API key has a monthly spend limit
- [ ] Orchestrator `ORCH_BIND` is `127.0.0.1` or a Tailscale IP, never `0.0.0.0` on a public host
- [ ] VPS: non-root user, SSH keys only, root login and password auth disabled, firewall allows only 22/80/443
- [ ] `N8N_ENCRYPTION_KEY` backed up outside the server
- [ ] n8n workflows that send messages or change data stay inactive until reviewed
- [ ] Image tags pinned once the stack works
- [ ] Citadel's server is separate from any employer's infrastructure

See [docs/guardrails.md](docs/guardrails.md) for the rules enforced in code.
