---
name: write-changelog
description: Turn Conventional Commits or a merged PR into Keep a Changelog entries written for users. Use when a PR merges or a release is cut.
---

# Write a changelog entry

## Procedure

1. **Collect** the commits (subject, body, SHA) and the PR title and description.
2. **Map types to sections:**

   | Commit type | Section |
   |---|---|
   | `feat` | Added |
   | `fix` | Fixed |
   | `perf`, user-visible `refactor` | Changed |
   | `security` | Security |
   | anything with `BREAKING CHANGE` | Changed, prefixed **Breaking:** |
   | removed features | Removed |
   | `docs`, `test`, `build`, `ci`, `chore`, internal `refactor` | Skip |

3. **Rewrite for the user,** one line each: what they can now do or what now works, not what
   files changed.
4. **Add under `## [Unreleased]`** in `CHANGELOG.md`, keeping section order: Added, Changed,
   Deprecated, Removed, Fixed, Security.
5. **Link** each line to its PR or commit.

## Examples

| Commit | Entry |
|---|---|
| `fix(refunds): round amounts with ROUND_HALF_UP` | Fixed: Refund amounts now round to the nearest kobo instead of truncating. ([#42](...)) |
| `feat(triage): add digest endpoint` | Added: Non-urgent notifications are collected into a morning and evening digest. ([#18](...)) |
| `refactor: extract policy module` | (skip: internal) |

## Rules

- Never invent a change that isn't in the commits.
- Merge several commits about one feature into one line.
- Breaking changes say what users must do: "**Breaking:** `/events` now requires `type`; update
  n8n workflows."
- No secrets, internal hostnames or customer names.
