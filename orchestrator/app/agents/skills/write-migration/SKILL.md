---
name: write-migration
description: Write a safe, reversible database migration (Alembic, plain SQL) that doesn't lose data or lock tables for long. Use for any schema change.
---

# Write a migration

## Procedure

1. **Create it:** `uv run alembic revision -m "<imperative summary>"`. One concern per
   migration.
2. **Write `upgrade()` and `downgrade()`** with `op.execute("""...""")` plain SQL or Alembic
   ops. `downgrade()` must truly reverse `upgrade()`. If reversal would lose data, say so in a
   comment and make it raise instead of silently dropping data.
3. **Test both directions** on a copy of real-shaped data:
   `uv run alembic upgrade head`, `uv run alembic downgrade -1`, `uv run alembic upgrade head`.
4. **Update the docs** that describe the schema (`docs/memory.md`, `docs/metrics.md`, etc.).

## Safe patterns

**Adding a column**
- Nullable, or with a constant default (cheap in Postgres 11+).
- `NOT NULL` on existing data: add nullable → backfill in batches → add the constraint.

**Renaming or changing a column: expand → migrate → contract** (three releases, never one)
1. Expand: add the new column; code writes to both.
2. Migrate: backfill old → new in batches; code reads the new one.
3. Contract: drop the old column once nothing reads it.

**Indexes on large tables:** `CREATE INDEX CONCURRENTLY`, which can't run inside a transaction:

```python
with op.get_context().autocommit_block():
    op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS events_type_idx ON events (type)")
```

**Backfills:** batches of 1,000–10,000 rows by primary key range, never one giant `UPDATE`.

**Foreign keys:** add as `NOT VALID`, then `VALIDATE CONSTRAINT` separately to avoid long locks.

## Never

- Drop a column or table that code still reads
- Rename in place on a live table
- Mix schema changes and large data backfills in one migration
- Edit a migration that has already run anywhere; write a new one
- Put secrets or environment-specific values in migrations

## Checklist

- [ ] `upgrade` → `downgrade` → `upgrade` runs cleanly
- [ ] No data loss on upgrade; data-losing downgrades raise with an explanation
- [ ] No long locks on large tables (concurrent indexes, batched backfills, `NOT VALID` FKs)
- [ ] Multi-tenant tables keep their tenant column `NOT NULL` and indexed
- [ ] Schema docs updated
