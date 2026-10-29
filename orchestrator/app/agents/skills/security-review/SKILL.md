---
name: security-review
description: Review a code change for security flaws using a fixed checklist and report findings by severity. Use when reviewing any change that handles input, auth, data access, files, secrets, external calls or model output.
---

# Security review

Run tools first, then read the code. Tools find known patterns; reading finds logic flaws.

## 1. Tool results (from the security gate)

Read the outputs if present: Semgrep, Bandit (Python), pip-audit / npm audit (dependencies),
gitleaks (secrets). Every high-severity tool finding is a blocking issue unless shown to be a
false positive, with the reason stated.

## 2. Checklist

**Access control** (most common serious flaw)
- [ ] Every query that reads or writes tenant data filters by the caller's tenant/organization,
      taken from the authenticated context, never from the request body
- [ ] IDs in URLs are checked for ownership before use (no IDOR)
- [ ] Admin-only actions check the role on the server

**Injection**
- [ ] SQL uses parameters or the ORM; no string-built queries
- [ ] No shell commands built from input; if unavoidable, argument lists, never `shell=True`
- [ ] File paths from input are resolved and checked against an allowed root
- [ ] Templates escape output; no raw HTML from input

**Input and output**
- [ ] Input validated at the boundary (type, length, range, format) with a schema
- [ ] Errors don't leak stack traces, SQL or internal hostnames to clients
- [ ] Logs contain no passwords, tokens, full card numbers or personal data

**Secrets and crypto**
- [ ] No secrets in code, tests, fixtures or config committed to git
- [ ] Passwords hashed with a slow algorithm (argon2, bcrypt); never stored or logged
- [ ] Webhook signatures verified with HMAC and a constant-time compare
- [ ] Tokens and random IDs from `secrets`, never `random`

**External calls**
- [ ] User-supplied URLs are allow-listed (SSRF)
- [ ] Timeouts on every HTTP call
- [ ] No `pickle`/`yaml.load` on untrusted data (use `yaml.safe_load`)

**Money and state**
- [ ] Amounts use `Decimal` or integer minor units; never float
- [ ] Payment and balance changes happen in a transaction; idempotency keys on retries

**LLM features**
- [ ] Model output is validated before use; never executed or used as a path or SQL
- [ ] External content passed to models is treated as data; the model has no tools that act
      on what that content says
- [ ] Work-scoped data only reaches approved model tiers

## 3. Report

| Severity | Meaning | Blocks merge |
|---|---|---|
| Critical | Exploitable now: data leak across tenants, RCE, auth bypass, exposed secret | Yes |
| High | Exploitable with some effort or conditions | Yes |
| Medium | Weakens defenses; fix soon | Yes in `ai_assisted`, owner decides in `ai_led` |
| Low | Hardening suggestion | No |

Each finding: severity, file and line, what an attacker could do, the concrete fix.
