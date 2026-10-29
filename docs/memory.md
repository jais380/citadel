# Memory and docs

Citadel's agents need context they didn't see happen: why a decision was made, what changed
last week, what the owner said in a DM. This doc defines how that context is stored and found.
A system that retrieves stale or wrong context confidently is worse than one with none, so
correctness beats coverage.

## Truth versus recall

| | Docs (truth) | Memory (recall) |
|---|---|---|
| What | Specs, ADRs, runbooks, API references, `AGENTS.md` | Events, Slack notes, run logs, review comments, summaries |
| Where | Git, next to the code they describe | `memory` table (Postgres + pgvector) |
| Written by | Humans, or agents via reviewed PRs | Agents and n8n, automatically |
| Authority | Authoritative once `approved` | Never authoritative; a pointer to go check |

When docs and memory disagree, the approved doc wins, and the conflict is reported.

## Every item carries metadata at write time

| Field | Values |
|---|---|
| `workspace` | Workspace slug |
| `scope` | `personal` / `work` (work items are embedded with the local model only) |
| `project` | Repository or product name |
| `kind` | `spec`, `adr`, `runbook`, `changelog`, `note`, `slack`, `review`, `incident` |
| `status` | `draft`, `approved`, `superseded` |
| `source_url` | Link to the original (commit, PR, message, doc) |
| `created_at` | When the original happened |
| `superseded_by` | ID of the replacing item |
| `content_hash` | SHA-256 of the content; duplicates are rejected |

Categorization happens when an item is stored, not guessed at search time.

## Writing

- Docs are indexed by chunking on headings (one chunk per section, ~300–800 tokens), with the
  doc title and section heading prepended to each chunk.
- Short items (messages, events) are one chunk each.
- Embeddings use `nomic-embed-text` via Ollama (768 dimensions) for all scopes, so work data
  never leaves the machine for embedding.
- **Supersede, don't overwrite.** A replaced decision keeps its row, gets
  `status = superseded` and a `superseded_by` link.

## Searching

Hybrid search, always filtered by workspace (and by scope when the caller is a free-tier agent):

1. Vector similarity (pgvector) finds meaning: "how do we handle refunds?"
2. Full-text search (Postgres `tsvector`) finds exact names: `CIT-42`, `resolve_tier`.
3. Merge with reciprocal rank fusion.
4. Rank boost: `approved` docs above notes; recent above old; `superseded` items only when
   asked for history.

## Using results

- **Cite or don't claim.** Any answer built from memory includes the `source_url` of each item
  used.
- If nothing relevant is found, the agent says so instead of guessing.
- Memory content is data (G13), even when it was written by an agent.

## Measuring retrieval

`docs/evals/retrieval.yaml` (Phase 4) holds about 30 real questions, each with the source that
should answer it. Every change to chunking, embeddings or ranking reruns the set and reports
recall@5. Target: ≥ 0.8.

## Privacy

- Work items are only returned to `brain` or `private` callers (G1 applies to retrieval too).
- Secrets are never stored (G12); n8n strips tokens before events arrive.
- Deleting a source deletes its memory rows; nothing is kept "just in case".
