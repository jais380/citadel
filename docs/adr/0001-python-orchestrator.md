# ADR 0001: Orchestrator in Python (LangGraph from Phase 3), MCP servers in TypeScript

- Status: Accepted
- Date: 2026-10-26

## Context

Citadel needs an orchestrator that runs a multi-agent pipeline with durable state and
human-approval pauses. I write NestJS/TypeScript and Django/Python, and I'm moving toward
ML engineering.

## Options

1. **NestJS + BullMQ, hand-built state machine.** Fastest for me on day one. I would build
   checkpointing and resume-after-approval myself.
2. **Python + LangGraph.** Durable checkpoints and interrupts for human approval are built in.
   Python is the working language of ML and agent tooling.

## Decision

Python for the orchestrator. Phase 0–2 use a plain loop (`pipeline_plain.py`) so I understand
the mechanics first; Phase 3 moves it onto LangGraph. Custom MCP servers (`citadel-tasks`,
`citadel-memory`) are written in TypeScript with the official MCP SDK.

## Consequences

- Builds Python agent and ML-adjacent skills that match where I'm heading.
- The portfolio shows both: an AI orchestration layer in Python and solid services in TypeScript.
- Risk: LangGraph abstracts a lot. Mitigation: the plain loop exists first and stays in the repo
  as the reference implementation.
