# local/ — private overlays

Copy this folder to `local/` (`Copy-Item -Recurse local.example local`). `local/` is
git-ignored, so nothing in it is ever published.

Put here anything Citadel should know that must not be in a public repo:

| File | Contents |
|---|---|
| `workspaces/<slug>.md` | Rules for one workspace: who the employer or client is, their AI policy, channels to watch, people whose messages are urgent |
| `contacts.md` | Names and roles Triage should recognize ("PM: <name> — tickets from them are `now`") |
| `notes.md` | Anything else private and durable |

How Citadel uses it (Phase 3+): when a task or event belongs to a workspace, the orchestrator
appends `local/workspaces/<slug>.md` to the agent's context, after Citadel's defaults and the
project's `AGENTS.md`. Code guardrails still win over anything written here.

Rules:
- Still no secrets. Keys and tokens belong in `.env`, never in Markdown.
- Keep each file short; it's sent to models with every relevant task.
- Work workspaces are only ever sent to `brain` or `private` tiers (G1).
