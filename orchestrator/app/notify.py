"""Telegram: the single inbox. Falls back to stdout when no bot is configured."""
from __future__ import annotations

import logging
import sys

import httpx

from .config import settings

log = logging.getLogger("citadel.notify")


def telegram(text: str, *, silent: bool = False) -> bool:
    s = settings()
    if not (s.telegram_bot_token and s.telegram_chat_id):
        print(f"[telegram not configured] {text}", file=sys.stderr)
        return False
    try:
        r = httpx.post(
            f"https://api.telegram.org/bot{s.telegram_bot_token}/sendMessage",
            json={"chat_id": s.telegram_chat_id, "text": text[:4000],
                  "disable_web_page_preview": True, "disable_notification": silent},
            timeout=15,
        )
        r.raise_for_status()
        return True
    except Exception as exc:
        log.warning("telegram send failed: %s", exc)
        return False


if __name__ == "__main__":  # make notify-test
    ok = telegram("Citadel online. If you can read this, Telegram is wired up.")
    print("sent" if ok else "not sent (check TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID)")
