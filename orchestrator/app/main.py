"""Citadel orchestrator HTTP API.

GET  /health          -> "ok"   (used from the VPS to check the Tailscale link)
POST /events          -> n8n sends normalized events here; triaged in the background
POST /digest          -> send the pending digest to Telegram now (n8n calls it on a schedule)
"""
from __future__ import annotations

import hmac
import logging
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from . import db, notify
from .config import settings
from .triage import triage_event

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
app = FastAPI(title="Citadel orchestrator", version="0.1.0")


class Event(BaseModel):
    source: str = Field(examples=["github"])
    scope: Literal["personal", "work"] = "personal"
    title: str
    body: str = ""
    url: str = ""


def _check_secret(given: str | None) -> None:
    expected = settings().citadel_secret
    if not given or not hmac.compare_digest(given, expected):
        raise HTTPException(status_code=401, detail="bad or missing X-Citadel-Secret")


@app.on_event("startup")
def _ready() -> None:
    logging.getLogger("citadel").info("orchestrator ready")


@app.get("/health", response_class=PlainTextResponse)
def health() -> str:
    return "ok"


@app.post("/events", status_code=202)
def receive_event(event: Event, background: BackgroundTasks,
                  x_citadel_secret: str | None = Header(default=None)) -> dict:
    _check_secret(x_citadel_secret)
    background.add_task(triage_event, **event.model_dump())
    return {"accepted": True}


@app.post("/digest")
def send_digest(x_citadel_secret: str | None = Header(default=None)) -> dict:
    _check_secret(x_citadel_secret)
    rows = db.execute(
        """UPDATE events SET notified = true
           WHERE priority = 'digest' AND notified = false
           RETURNING source, summary, url"""
    ) or []
    if rows:
        lines = [f"• [{src}] {summary}" + (f" — {url}" if url else "") for src, summary, url in rows]
        notify.telegram("🟡 Digest\n\n" + "\n".join(lines), silent=True)
    return {"sent": len(rows)}
