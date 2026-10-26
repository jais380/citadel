"""Triage agent: classify one incoming event and decide whether to ping now."""
from __future__ import annotations

import logging

from . import db, llm, notify
from .roles import role

log = logging.getLogger("citadel.triage")

ICON = {"now": "🔴", "digest": "🟡", "ignore": "⚪"}


def triage_event(*, source: str, scope: str, title: str, body: str = "", url: str = "") -> dict:
    event_id = db.insert_event(source, scope, title, body, url)
    r = role("triage")
    user = f"Source: {source}\nTitle: {title}\nURL: {url or '-'}\n\nBody:\n{(body or '')[:4000]}"
    try:
        result, _ = llm.chat_json(
            [{"role": "system", "content": r.system}, {"role": "user", "content": user}],
            tier=r.tier, agent="triage", scope=scope,
        )
        priority = result.get("priority", "digest")
        if priority not in ICON:
            priority = "digest"
        summary = str(result.get("summary") or title)[:300]
    except Exception as exc:
        # Models down or rate-limited: never drop an event. Ping with the raw title.
        log.warning("triage failed, forwarding raw event: %s", exc)
        priority, summary = "now", f"(untriaged) {title}"

    notified = False
    if priority == "now":
        text = f"{ICON[priority]} [{source}] {summary}"
        if url:
            text += f"\n{url}"
        notified = notify.telegram(text)

    db.update_event(event_id, priority=priority, summary=summary, notified=notified)
    return {"event_id": event_id, "priority": priority, "summary": summary, "notified": notified}
