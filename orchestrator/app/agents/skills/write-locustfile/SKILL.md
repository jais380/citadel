---
name: write-locustfile
description: Write a Locust load test that checks a spec's performance budget against staging, and judge the result. Use when a spec has a performance budget or a change touches a hot path.
---

# Write a Locust load test

## 1. Get the budget from the spec

A budget has four parts. If any is missing, ask instead of inventing one.

| Part | Example |
|---|---|
| Endpoint(s) and traffic mix | 70% `GET /orders`, 25% `GET /orders/{id}`, 5% `POST /orders` |
| Load | 200 concurrent users, spawn 20/s, hold 5 minutes |
| Latency | p95 < 300 ms per endpoint |
| Errors | failure rate < 0.5% |

## 2. Write `locustfile.py`

```python
import os
from locust import HttpUser, task, between

class ApiUser(HttpUser):
    wait_time = between(1, 3)          # think time; real users pause

    def on_start(self) -> None:
        # Test account from env, never hard-coded. Staging only.
        token = os.environ["LOAD_TEST_TOKEN"]
        self.client.headers.update({"Authorization": f"Bearer {token}"})

    @task(70)
    def list_orders(self) -> None:
        self.client.get("/orders?limit=20", name="GET /orders")

    @task(25)
    def get_order(self) -> None:
        self.client.get("/orders/1001", name="GET /orders/{id}")   # name groups stats

    @task(5)
    def create_order(self) -> None:
        with self.client.post("/orders", json={"sku": "TEST-1", "qty": 1},
                              name="POST /orders", catch_response=True) as r:
            if r.status_code != 201:
                r.failure(f"expected 201, got {r.status_code}")
```

Rules:
- Task weights match the traffic mix.
- `name=` on parametrized URLs so stats group per endpoint, not per ID.
- Validate responses with `catch_response=True`; a 200 with an error body is a failure.
- Test data is created for the test and cleaned up after; never reuse real customer data.

## 3. Run headless against staging

```bash
locust -f locustfile.py --headless -u 200 -r 20 -t 5m \
  --host https://staging.example.com --csv results --exit-code-on-error 1
```

**Never against production.** Refuse if the host looks like production.

## 4. Judge the result

Read `results_stats.csv`. For each endpoint row and the `Aggregated` row:
- `95%` column must be under the latency budget
- `Failure Count / Request Count` must be under the error budget

Report a gate result: passed or failed, with the p95 and failure rate per endpoint versus the
budget. On failure, point to the slowest endpoint and the likely cause class (N+1 queries,
missing index, no pagination, synchronous external call, no caching).

## Checklist

- [ ] Budget fully specified (mix, load, latency, errors)
- [ ] Host is staging; secrets from env
- [ ] Responses validated, URLs grouped by `name`
- [ ] Ran for long enough to warm up (≥ 3 minutes)
- [ ] Gate decided from the CSV, not from eyeballing
