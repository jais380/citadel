<!--
  Template: copy this file to the root of each repository Citadel works on (your SaaS, a
  freelance project, a side project). Citadel reads it at the start of every task, the same way
  a new engineer reads the README. Fill in every <...>; delete sections that don't apply.
  Never put secrets, client names you can't share, or internal URLs here if the repo is public.
-->

# AGENTS.md — <project name>

<One or two sentences: what this project is and who uses it.>

## Citadel settings

| Setting | Value |
|---|---|
| Workspace | `<personal | job | client-slug>` |
| Scope | `<personal | work>` |
| Autonomy | `<ai_led | ai_assisted>` |
| Default branch | `main` |
| Staging URL (for load tests) | `<https://staging.example.com or none>` |

## Stack

- Language / runtime: <e.g. TypeScript 5, Node 20>
- Framework: <e.g. NestJS 10>
- Database: <e.g. PostgreSQL 16 via TypeORM>
- Validation: <e.g. Zod>
- Auth: <e.g. BetterAuth, JWT>

## Commands

| Task | Command |
|---|---|
| Install | `<npm ci>` |
| Unit tests | `<npm test>` |
| Integration tests | `<npm run test:e2e>` |
| Lint | `<npm run lint>` |
| Type check | `<npx tsc --noEmit>` |
| Run locally | `<npm run start:dev>` |
| Migrations | `<npm run migration:run>` |

## Layout

```
<src/modules/<feature>/   controller, service, entity, dto per feature>
<test/                    e2e tests>
```

## Conventions

- <Service return shape, e.g. `{ message, data }`>
- <Error handling, e.g. throw Nest HTTP exceptions, never return error objects>
- <Soft deletes via `deletedAt`>
- <Naming: kebab-case files, PascalCase classes>

## Hard rules (never break)

- <Tenant isolation: every query on tenant data filters by the caller's institution from the
  auth context, never from the request body>
- <Money: integer minor units or Decimal; discounts never change `amountPaid`>
- <No raw SQL outside repositories>

## Quality budgets

| Budget | Value |
|---|---|
| p95 latency, main endpoints | <300 ms at 200 users> |
| Error rate under load | <0.5%> |
| Minimum test coverage on changed lines | <80%> |

## Protected paths (agents never modify)

- <`src/migrations/` — humans write migrations>
- <`.github/workflows/`>
- <`infra/`>

## Ask before

- Adding a dependency
- Changing a public API or database schema
- Anything touching payments or auth
