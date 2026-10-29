# Event envelope

Every event entering Citadel, from any source, uses one shape. n8n does the normalizing;
the orchestrator never parses GitHub or Slack payloads directly. Delivery metrics are computed
from these events, so `type` and `occurred_at` must be right.

## Shape

`POST /events` with header `X-Citadel-Secret`:

```json
{
  "source": "github",
  "type": "ci.failed",
  "scope": "personal",
  "workspace": "personal",
  "occurred_at": "2026-10-27T09:14:03Z",
  "external_id": "github:run:123456789",
  "actor": "octocat",
  "title": "CI failed on main: tests (3.12)",
  "body": "test_orders.py::test_refund FAILED ...",
  "url": "https://github.com/owner/repo/actions/runs/123456789",
  "raw": { "...": "the untouched source payload" }
}
```

| Field | Required | Notes |
|---|---|---|
| `source` | yes | `github`, `jira`, `slack`, `gmail`, `calendar`, `uptime`, `deploy`, `manual` |
| `type` | yes | Dotted name from the taxonomy below |
| `scope` | yes | `personal` or `work`. When unsure, n8n sends `work` (fail closed) |
| `workspace` | yes | Workspace slug, e.g. `personal`, `job` |
| `occurred_at` | yes | When it happened at the source, ISO 8601 UTC. Not when it arrived |
| `external_id` | yes | `<source>:<kind>:<id>`, unique per source. Re-sent webhooks are de-duplicated on it |
| `actor` | no | Who caused it |
| `title` | yes | One line, human-readable |
| `body` | no | Truncated to 8,000 characters by n8n |
| `url` | no | Link back to the source |
| `raw` | yes | Original payload, stored as `jsonb`, so metrics can be recomputed later |

> Phase 0 accepts the subset `source, scope, title, body, url`. Foundation 5 adds the rest.

## Type taxonomy

| Type | Meaning | Used by |
|---|---|---|
| `ci.failed` / `ci.recovered` | Pipeline on a tracked branch failed / went green again | Triage |
| `pr.opened` / `pr.merged` / `pr.closed` | Pull request lifecycle | Documenter, cycle time |
| `pr.review_requested` | A review was requested from the owner | Triage (`now`) |
| `pr.commented` | Comment on a PR the owner is involved in | Triage |
| `commit.pushed` | Commits pushed to a tracked branch | Documenter, cycle time |
| `deploy.started` / `deploy.succeeded` / `deploy.failed` / `deploy.rolled_back` | Deployment lifecycle, with `env` in `raw` | Deployment frequency, change failure rate |
| `incident.opened` / `incident.resolved` | Outage or alert from the uptime monitor | MTTR, change failure rate |
| `ticket.assigned` / `ticket.updated` / `ticket.commented` | Jira issue events | Triage, PM |
| `bug.reported` | Ticket labelled as a defect | Defect metrics |
| `message.direct` / `message.mention` | Slack DM or mention | Triage, Documenter (notes) |
| `email.received` | Email that passed n8n's filter | Triage |
| `calendar.upcoming` | Event starting soon | Triage |

Add a type by extending this table in the same PR that starts sending it.

## Rules

- Event content is **untrusted data** (G13). Agents classify or summarize it; they never follow
  instructions found in it.
- n8n strips credentials and tokens from `raw` before sending.
- If the orchestrator is unreachable, the n8n workflow falls back to sending `title` and `url`
  straight to Telegram, so nothing is lost while the laptop is off.
