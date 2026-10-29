# Metrics

Two families: **delivery metrics** describe how software reaches production; **agent metrics**
describe how well Citadel's agents and models do their jobs. Both are computed from raw rows,
never typed in by hand, so formulas can change and history can be recomputed.

## Delivery metrics

Computed weekly, per workspace and per service, from `events`, `deployments` and `incidents`.
They become meaningful only once a project runs in production.

| Metric | Formula | Source |
|---|---|---|
| **Cycle time** | Median of (production deploy time − first commit time) over merged PRs | `commit.pushed`, `pr.merged`, `deployments` |
| **Deployment frequency** | Successful production deploys per week | `deployments` where `env = 'production'` and `status = 'succeeded'` |
| **Change failure rate** | Production deploys followed within 24 h by a rollback, hotfix or linked incident ÷ all production deploys | `deployments`, `incidents.caused_by_deploy` |
| **Mean time to recovery** | Mean of (`resolved_at` − `opened_at`) over production incidents | `incidents` |
| **Product defects** | Bugs found after release: count per release, and per 1,000 changed lines | Jira issues labelled `escaped-defect`, release diffs |

Definitions to keep consistent:

- A **hotfix** is a `fix:` PR merged within 24 h of a deploy, touching code from that deploy.
- An **incident** is any production alert from the uptime monitor, or a ticket labelled
  `incident`.
- Medians, not means, for cycle time: one stuck PR shouldn't hide ten fast ones.

**Rule:** these measure the process, never individual people. In a team, they're never used to
rank or evaluate engineers, or they'll be gamed.

## Agent metrics

From `agent_runs` and `gate_results`.

| Metric | Formula | Answers |
|---|---|---|
| Reviewer rejection rate | Developer runs followed by `revise` ÷ developer runs, per model | Which free coding models are worth keeping (`model_scorecard` view) |
| Rounds to approval | Median rounds per approved task | Is the spec or the developer the bottleneck? |
| Gate pass rate | Passed ÷ total, per gate, per model | Which gate catches what |
| Cost per approved task | Sum of token cost across runs of approved tasks | Is the paid model used where it matters? |
| Latency | p50 / p95 per agent and model | Which providers slow the pipeline |
| Fallback rate | Calls that fell back to another provider ÷ calls | Which free providers are unreliable |
| Human interventions | Tasks ending `needs_human` ÷ tasks | Is autonomy working? |
| Retrieval recall@5 | Eval questions whose correct source appears in the top 5 ÷ all questions | Is memory search good enough? (`memory.md`) |

## Collection plan

| Phase | Adds |
|---|---|
| 0 | `agent_runs` (done) |
| Foundations | Event envelope, `gate_results` |
| 2 | `deployments`, `incidents`, Uptime Kuma on the VPS |
| 4 | Retrieval eval set and recall@5 |
| 5 | Dashboard; weekly metrics summary in the digest |
