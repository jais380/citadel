"""make smoke — ping every tier once and show which model answered and how fast."""
from __future__ import annotations

from . import llm

PROMPT = [{"role": "user", "content": "Reply with exactly one word: pong"}]


def main() -> int:
    failures = 0
    print(f"{'tier':<9} {'status':<7} {'latency':>8}  model / error")
    print("-" * 70)
    for tier in llm.TIERS:
        try:
            r = llm.chat(PROMPT, tier=tier, agent="smoke")
            status = "ok" if "pong" in r.text.lower() else "odd"
            print(f"{tier:<9} {status:<7} {r.latency_ms:>6}ms  {r.model}  -> {r.text[:30]!r}")
        except Exception as exc:
            failures += 1
            print(f"{tier:<9} {'FAIL':<7} {'-':>8}  {type(exc).__name__}: {str(exc)[:120]}")
    print("-" * 70)
    print("all tiers reachable" if not failures else f"{failures} tier(s) failing — see README troubleshooting")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
