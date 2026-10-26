"""Tiny Postgres helpers. Logging must never crash the pipeline, so failures only warn."""
from __future__ import annotations

import logging

import psycopg

from .config import settings

log = logging.getLogger("citadel.db")


def _connect():
    url = settings().database_url
    if not url:
        return None
    return psycopg.connect(url, autocommit=True)


def execute(sql: str, params: tuple = ()) -> list[tuple] | None:
    try:
        conn = _connect()
        if conn is None:
            return None
        with conn, conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall() if cur.description else None
    except Exception as exc:
        log.warning("db error (continuing): %s", exc)
        return None


def log_run(*, agent, tier, model, scope, status, task_id=None, latency_ms=None,
            prompt_tokens=None, completion_tokens=None, verdict=None, error=None) -> None:
    execute(
        """INSERT INTO agent_runs (task_id, agent, tier, model, scope, latency_ms,
                                   prompt_tokens, completion_tokens, status, verdict, error)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (task_id, agent, tier, model, scope, latency_ms, prompt_tokens, completion_tokens, status, verdict, error),
    )


def set_last_verdict(task_id: int | None, verdict: str) -> None:
    """Stamp the reviewer's verdict on its most recent run row."""
    if task_id is None:
        return
    execute(
        """UPDATE agent_runs SET verdict = %s
           WHERE id = (SELECT max(id) FROM agent_runs WHERE task_id = %s AND agent = 'reviewer')""",
        (verdict, task_id),
    )


def create_task(title: str, scope: str, run_dir: str) -> int | None:
    rows = execute("INSERT INTO tasks (title, scope, run_dir) VALUES (%s,%s,%s) RETURNING id", (title, scope, run_dir))
    return rows[0][0] if rows else None


def update_task(task_id: int | None, *, state: str, rounds: int | None = None) -> None:
    if task_id is None:
        return
    execute("UPDATE tasks SET state=%s, rounds=COALESCE(%s, rounds), updated_at=now() WHERE id=%s",
            (state, rounds, task_id))


def insert_event(source, scope, title, body, url) -> int | None:
    rows = execute("INSERT INTO events (source, scope, title, body, url) VALUES (%s,%s,%s,%s,%s) RETURNING id",
                   (source, scope, title, body, url))
    return rows[0][0] if rows else None


def update_event(event_id, *, priority, summary, notified) -> None:
    if event_id is None:
        return
    execute("UPDATE events SET priority=%s, summary=%s, notified=%s WHERE id=%s",
            (priority, summary, notified, event_id))
