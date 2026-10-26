"""The pipeline as a plain Python loop — no framework.

    spec (PM, brain) -> code (Developer, worker) -> run tests -> review (Reviewer, brain)
                              ^                                        |
                              +----------- "revise" + reasons ---------+

Read this file end to end before Phase 3. LangGraph will replace exactly this loop, adding
checkpoints (resume after a crash) and interrupts (pause for your approval) on top.

Usage (inside the container):
    python -m app.pipeline_plain "Write a function that ... with tests" [--scope work]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path, PurePosixPath

from . import db, llm, notify
from .config import settings
from .roles import role


# ── helpers ──────────────────────────────────────────────────────────────────

def _safe_path(root: Path, rel: str) -> Path:
    """Model-supplied paths must stay inside the workspace."""
    p = PurePosixPath(rel)
    if p.is_absolute() or ".." in p.parts:
        raise ValueError(f"refusing unsafe path from model: {rel!r}")
    return root / p


def write_files(workspace: Path, files: list[dict]) -> list[str]:
    workspace.mkdir(parents=True, exist_ok=True)
    written = []
    for f in files:
        target = _safe_path(workspace, f["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f["content"])
        written.append(f["path"])
    return written


def run_tests(workspace: Path, timeout_s: int = 120) -> tuple[bool, str]:
    """Run pytest on model-written code.

    Phase 0 stand-in for a real sandbox: empty environment (no API keys visible), a timeout,
    and the workspace as cwd. Phase 3 moves this into a throwaway container with no network.
    """
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(workspace), "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider"],
            cwd=workspace, env=env, capture_output=True, text=True, timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        return False, f"pytest timed out after {timeout_s}s"
    output = (proc.stdout + proc.stderr)[-6000:]
    return proc.returncode == 0, output


def render_code(files: list[dict]) -> str:
    return "\n\n".join(f"### {f['path']}\n```\n{f['content']}\n```" for f in files)


# ── the pipeline ─────────────────────────────────────────────────────────────

def run(task: str, scope: str = "personal") -> dict:
    s = settings()
    run_dir = Path(s.runs_dir) / time.strftime("%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "task.txt").write_text(task)
    task_id = db.create_task(task[:200], scope, str(run_dir))
    print(f"run dir: {run_dir}  task_id: {task_id}")

    # 1. Spec
    db.update_task(task_id, state="spec")
    pm = role("pm")
    spec = llm.chat(
        [{"role": "system", "content": pm.system}, {"role": "user", "content": task}],
        tier=pm.tier, agent="pm", scope=scope, task_id=task_id,
    ).text
    (run_dir / "spec.md").write_text(spec)
    print("✓ spec written")

    dev, rev = role("developer"), role("reviewer")
    feedback: list[str] = []
    review: dict = {}

    for rnd in range(1, s.pipeline_max_rounds + 1):
        # 2. Code
        db.update_task(task_id, state="dev", rounds=rnd)
        dev_prompt = f"# Spec\n\n{spec}"
        if feedback:
            dev_prompt += "\n\n# Reviewer feedback to fix\n\n" + "\n".join(f"- {x}" for x in feedback)
        try:
            out, _ = llm.chat_json(
                [{"role": "system", "content": dev.system}, {"role": "user", "content": dev_prompt}],
                tier=dev.tier, agent="developer", scope=scope, task_id=task_id,
            )
            files = out["files"]
        except Exception as exc:
            feedback = [f"Your previous reply could not be used ({exc}). Return the required JSON with a 'files' list."]
            print(f"✗ round {rnd}: developer output unusable: {exc}")
            continue

        workspace = run_dir / f"round-{rnd}"
        written = write_files(workspace, files)
        print(f"✓ round {rnd}: wrote {', '.join(written)}")

        # 3. Tests (ground truth)
        passed, test_out = run_tests(workspace)
        (workspace / "_test_output.txt").write_text(test_out)
        print(f"{'✓' if passed else '✗'} round {rnd}: tests {'passed' if passed else 'failed'}")

        # 4. Review
        db.update_task(task_id, state="review", rounds=rnd)
        review_prompt = (
            f"# Spec\n\n{spec}\n\n# Code\n\n{render_code(files)}\n\n"
            f"# Test run (exit {'0' if passed else 'non-zero'})\n\n```\n{test_out}\n```"
        )
        review, _ = llm.chat_json(
            [{"role": "system", "content": rev.system}, {"role": "user", "content": review_prompt}],
            tier=rev.tier, agent="reviewer", scope=scope, task_id=task_id,
        )
        verdict = review.get("verdict", "revise")
        if verdict == "approve" and not passed:   # code rule beats model opinion
            verdict = "revise"
            review.setdefault("reasons", []).insert(0, "Tests did not pass.")
        db.set_last_verdict(task_id, verdict)
        (workspace / "_review.json").write_text(json.dumps(review, indent=2))
        print(f"{'✓' if verdict == 'approve' else '↺'} round {rnd}: reviewer says {verdict} — {review.get('summary', '')}")

        if verdict == "approve":
            db.update_task(task_id, state="approved", rounds=rnd)
            notify.telegram(f"✅ Pipeline approved in {rnd} round(s): {task[:120]}\n{workspace}")
            return {"status": "approved", "rounds": rnd, "workspace": str(workspace)}
        feedback = review.get("reasons") or ["Make the tests pass and cover every acceptance criterion."]

    db.update_task(task_id, state="failed", rounds=s.pipeline_max_rounds)
    notify.telegram(f"⚠️ Pipeline needs you after {s.pipeline_max_rounds} rounds: {task[:120]}\n"
                    f"Last review: {review.get('summary', '-')}\n{run_dir}")
    return {"status": "needs_human", "rounds": s.pipeline_max_rounds, "run_dir": str(run_dir)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Run the plain spec→code→test→review loop once.")
    ap.add_argument("task", help="What you want built, in plain words.")
    ap.add_argument("--scope", choices=["personal", "work"], default="personal")
    args = ap.parse_args()
    result = run(args.task, args.scope)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "approved" else 2


if __name__ == "__main__":
    raise SystemExit(main())
