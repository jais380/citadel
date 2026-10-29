# Changelog

All notable changes to Citadel are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/). Entries come from Conventional Commit types
(see `CONTRIBUTING.md`).

## [Unreleased]

### Added
- Phase 0 starter: local Docker stack (OmniRoute, Postgres + pgvector, Redis, orchestrator).
- Orchestrator with four model tiers and scope-based routing for work data.
- Triage agent that classifies incoming events and pings Telegram for urgent ones.
- Plain spec → code → tests → review pipeline with run logging.
- VPS stack: Caddy, n8n with Postgres, portfolio site.
- Agent context files: `AGENTS.md`, prompts, skills, guardrails and architecture docs.

### Changed
- Python dependencies managed with uv (`pyproject.toml` + `uv.lock`).
