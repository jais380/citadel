"""One place that talks to models.

Tiers:
  brain   -> OmniRoute combo with Claude       (specs, review)
  worker  -> OmniRoute combo of free coders    (code, tests, research)
  cheap   -> OmniRoute combo of small models   (triage, summaries, docs)
  private -> Ollama directly, never OmniRoute  (anything with scope=work)

The scope rule lives HERE, in code, not in prompts: a work-scoped call can
only ever go to `brain` or `private`.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from functools import lru_cache

from openai import OpenAI

from . import db
from .config import settings

TIERS = ("brain", "worker", "cheap", "private")
WORK_SAFE_TIERS = ("brain", "private")


@dataclass
class Reply:
    text: str
    tier: str
    model: str
    latency_ms: int
    prompt_tokens: int | None
    completion_tokens: int | None


@lru_cache
def _router() -> OpenAI:
    s = settings()
    return OpenAI(base_url=s.omniroute_base_url, api_key=s.omniroute_api_key or "none", timeout=180)


@lru_cache
def _ollama() -> OpenAI:
    return OpenAI(base_url=settings().ollama_base_url, api_key="ollama", timeout=600)


def resolve_tier(tier: str, scope: str) -> str:
    if tier not in TIERS:
        raise ValueError(f"unknown tier {tier!r}; expected one of {TIERS}")
    if scope == "work" and tier not in WORK_SAFE_TIERS:
        return "private"
    return tier


def _client_and_model(tier: str) -> tuple[OpenAI, str]:
    s = settings()
    if tier == "private":
        return _ollama(), s.model_private
    model = {"brain": s.model_brain, "worker": s.model_worker, "cheap": s.model_cheap}[tier]
    return _router(), model


def chat(
    messages: list[dict],
    *,
    tier: str,
    agent: str,
    scope: str = "personal",
    task_id: int | None = None,
    temperature: float = 0.2,
) -> Reply:
    tier = resolve_tier(tier, scope)
    client, model = _client_and_model(tier)
    start = time.perf_counter()
    try:
        resp = client.chat.completions.create(model=model, messages=messages, temperature=temperature)
    except Exception as exc:  # log the failure, then re-raise
        db.log_run(agent=agent, tier=tier, model=model, scope=scope, task_id=task_id,
                   latency_ms=int((time.perf_counter() - start) * 1000), status="error", error=str(exc)[:500])
        raise
    latency = int((time.perf_counter() - start) * 1000)
    usage = getattr(resp, "usage", None)
    reply = Reply(
        text=(resp.choices[0].message.content or "").strip(),
        tier=tier,
        model=getattr(resp, "model", None) or model,   # OmniRoute reports which model actually answered
        latency_ms=latency,
        prompt_tokens=getattr(usage, "prompt_tokens", None),
        completion_tokens=getattr(usage, "completion_tokens", None),
    )
    db.log_run(agent=agent, tier=tier, model=reply.model, scope=scope, task_id=task_id,
               latency_ms=latency, prompt_tokens=reply.prompt_tokens,
               completion_tokens=reply.completion_tokens, status="ok")
    return reply


_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


def parse_json(text: str) -> dict:
    """Free models wrap JSON in prose or code fences. Dig it out."""
    for candidate in [text, *_FENCE.findall(text)]:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError(f"no JSON object in model output: {text[:200]!r}")


def chat_json(messages: list[dict], *, retries: int = 1, **kw) -> tuple[dict, Reply]:
    """chat() that must return a JSON object; asks once more if parsing fails."""
    reply = chat(messages, **kw)
    for attempt in range(retries + 1):
        try:
            return parse_json(reply.text), reply
        except (ValueError, json.JSONDecodeError):
            if attempt == retries:
                raise
            messages = [*messages, {"role": "assistant", "content": reply.text},
                        {"role": "user", "content": "That was not valid JSON. Reply with ONLY the JSON object."}]
            reply = chat(messages, **kw)
    raise RuntimeError("unreachable")
