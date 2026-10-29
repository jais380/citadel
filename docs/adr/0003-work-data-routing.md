# ADR 0003: Work data routes only to the paid model or local models

- Status: Accepted
- Date: 2026-10-26

## Context

Citadel uses free model providers to keep costs down. Many free tiers may use submitted data
for training or keep it for review. Citadel also handles employer data: code, tickets, Slack
messages. Sending that to free providers could breach the employer's confidentiality rules.

## Options

1. **Rule in prompts.** Tell agents not to send work data to free models. Models can't see
   where their output goes, and a prompt can't enforce routing. Rejected.
2. **Rule in router config.** Separate OmniRoute combos for work. One misconfigured combo
   leaks data silently. Rejected as the only control.
3. **Rule in orchestrator code.** Every call carries `scope`; the code forces `scope=work` onto
   `brain` (Claude via a paid API key) or `private` (Ollama), whatever the agent config says.
   The `private` tier bypasses OmniRoute entirely.

## Decision

Option 3, enforced in `resolve_tier()` (moving to `policy.allowed_tiers()`), with tests.
Events whose scope n8n can't determine are sent as `work` (fail closed).

## Consequences

- Work tasks are slower or cost more: local models are weaker; Claude costs money.
- Before connecting any employer system, check the employer's policy on AI tools; the paid
  provider may also need approval.
- Retrieval follows the same rule: work memory is only returned to `brain` or `private`
  callers, and all embeddings are computed locally.
