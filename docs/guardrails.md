# Guardrails

A guardrail is a rule that must hold even when a model misbehaves. Every guardrail here is
enforced **in code** and covered by a test; prompts may repeat a rule but never replace the
code. If a guardrail can't be evaluated (missing config, unknown workspace), the action is
refused: guardrails fail closed.

Status: **Enforced** = in code and tested · **Partial** = in code, gaps listed · **Planned** = not built yet.

| ID | Rule | Why | Enforced in | Status |
|---|---|---|---|---|
| G1 | A call with `scope=work` only ever uses the `brain` or `private` tier | Employer data must not reach free third-party providers, many of which train on inputs | `llm.resolve_tier()` → moves to `policy.allowed_tiers()` | Partial: needs its test (foundation 1) |
| G2 | The `private` tier talks to Ollama directly, never through OmniRoute | A misconfigured router combo can't leak work data | `llm._client_and_model()` | Enforced in code; test pending |
| G3 | A reviewer "approve" is overridden to "revise" when tests didn't pass | Tests are ground truth; a model opinion can't outvote them | `pipeline_plain.run()` | Enforced in code; test pending |
| G4 | Model-supplied file paths must stay inside the task workspace | Prevents path traversal (`../`, absolute paths) | `pipeline_plain._safe_path()` | Enforced in code; test pending |
| G5 | `/events` and `/digest` require `X-Citadel-Secret`, compared in constant time | Only n8n may submit events | `main._check_secret()` | Enforced in code; test pending |
| G6 | Model-written tests run without the orchestrator's environment (no keys), with a timeout | Untrusted code must not read secrets or hang the system | `pipeline_plain.run_tests()` | Partial: same machine; container sandbox with no network in Phase 3 |
| G7 | No agent merges, pushes to a default branch, or deploys | Irreversible actions belong to the owner | No such capability exists; Phase 3 adds approval interrupts | Planned |
| G8 | No agent sends a message, email or comment as the owner without approval | Prevents impersonation and prompt-injection-driven actions | Notifications go only to the owner's own Telegram today | Partial |
| G9 | n8n workflows created by agents stay inactive until the owner activates them | A bad automation against live accounts is hard to undo | n8n MCP integration (Phase 4) | Planned |
| G10 | In `ai_assisted` workspaces, agents never write to the repository; they comment and suggest | Company code is written by engineers | `policy.can_write_code()` (foundation 4) | Planned |
| G11 | Every quality gate must pass before a task can be approved, in every workspace | Quality is enforced for humans and agents alike | `gate_results` + pipeline (Phase 3) | Planned |
| G12 | Secrets are never written to logs, prompts, `agent_runs`, memory or run folders | Logs and memory are widely read and get indexed | Code review + gitleaks in CI | Partial |
| G13 | External content (emails, messages, web pages, PR text) is treated as data, never as instructions | Prompt injection | Agents reading external content have no action tools; prompts state the rule | Partial |

## Prompt-level guidance (not guardrails)

These shape judgment and live in prompts or skills. They're allowed to fail occasionally:

- Prefer the simplest design that meets the spec.
- Ask instead of assuming when a requirement is ambiguous.
- Keep summaries short and specific.

## Changing a guardrail

1. Open an ADR explaining the change and the risk.
2. Change the code and its test in the same PR.
3. Update this table.
4. The owner approves explicitly. Agents never change this file or the code it points to on
   their own initiative.
