-- Citadel schema. Runs once, on the first start of an empty Postgres volume.
-- To re-run from scratch: make down && docker volume rm citadel_pg-data && make up

CREATE EXTENSION IF NOT EXISTS vector;

-- Every event that arrives from n8n (GitHub, Jira, Slack, Gmail, ...).
CREATE TABLE IF NOT EXISTS events (
    id          BIGSERIAL PRIMARY KEY,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    source      TEXT NOT NULL,                      -- github | jira | slack | gmail | manual
    scope       TEXT NOT NULL DEFAULT 'personal',   -- personal | work
    title       TEXT NOT NULL,
    body        TEXT,
    url         TEXT,
    priority    TEXT,                               -- now | digest | ignore (set by Triage)
    summary     TEXT,                               -- one line from Triage
    notified    BOOLEAN NOT NULL DEFAULT false
);
CREATE INDEX IF NOT EXISTS events_digest_idx ON events (priority, notified, received_at);

-- Units of work moving through the pipeline.
CREATE TABLE IF NOT EXISTS tasks (
    id          BIGSERIAL PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    scope       TEXT NOT NULL DEFAULT 'personal',
    title       TEXT NOT NULL,
    state       TEXT NOT NULL DEFAULT 'new',        -- new | spec | dev | review | approved | failed
    run_dir     TEXT,
    rounds      INT NOT NULL DEFAULT 0
);

-- One row per model call. This table is your evaluation data.
CREATE TABLE IF NOT EXISTS agent_runs (
    id                BIGSERIAL PRIMARY KEY,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    task_id           BIGINT REFERENCES tasks(id),
    agent             TEXT NOT NULL,
    tier              TEXT NOT NULL,
    model             TEXT NOT NULL,
    scope             TEXT NOT NULL,
    latency_ms        INT,
    prompt_tokens     INT,
    completion_tokens INT,
    status            TEXT NOT NULL,                -- ok | error
    verdict           TEXT,                         -- reviewer: approve | revise
    error             TEXT
);
CREATE INDEX IF NOT EXISTS agent_runs_agent_idx ON agent_runs (agent, model, created_at);

-- Project memory (Phase 4: citadel-memory MCP server). 768 dims = nomic-embed-text.
CREATE TABLE IF NOT EXISTS memory (
    id          BIGSERIAL PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    scope       TEXT NOT NULL DEFAULT 'personal',
    project     TEXT,
    kind        TEXT,                               -- note | adr | changelog | slack
    content     TEXT NOT NULL,
    embedding   vector(768)
);

-- Handy view: which models get rejected most by the Reviewer.
CREATE OR REPLACE VIEW model_scorecard AS
SELECT d.model,
       count(*)                                         AS dev_runs,
       count(*) FILTER (WHERE r.verdict = 'approve')    AS approved,
       round(100.0 * count(*) FILTER (WHERE r.verdict = 'revise') / NULLIF(count(*), 0), 1) AS reject_pct,
       round(avg(d.latency_ms))                         AS avg_latency_ms
FROM agent_runs d
JOIN LATERAL (
    SELECT verdict FROM agent_runs r
    WHERE r.task_id = d.task_id AND r.agent = 'reviewer' AND r.id > d.id
    ORDER BY r.id LIMIT 1
) r ON true
WHERE d.agent = 'developer'
GROUP BY d.model
ORDER BY reject_pct NULLS LAST;
