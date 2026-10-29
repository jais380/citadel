---
name: write-tests
description: Write deterministic pytest tests from a spec's acceptance criteria. Use whenever producing or fixing tests for new or changed behavior.
---

# Write tests

## Procedure

1. **Map criteria to tests.** Number every acceptance criterion. Plan at least one test each
   before writing any code.
2. **Add the cases the spec implies.** For each input, consider:
   - empty / missing / `None`
   - boundaries (0, 1, max, max+1, negative)
   - wrong type
   - duplicates
   - very large input
   - Unicode and whitespace in strings
   - money: rounding and currency precision (use `Decimal`, never float)
   - time: time zones, end of month, leap day
3. **Write each test as Arrange → Act → Assert**, one behavior per test.
4. **Name it after the behavior:** `test_<unit>_<condition>_<expected>`, e.g.
   `test_refund_amount_exceeds_paid_raises_value_error`.
5. **Run them.** A new test for new behavior should fail before the implementation exists.

## Rules

- **Deterministic.** No network, no real clock (inject time or freeze it), no unseeded
  randomness, no `sleep`.
- **Independent.** Tests don't depend on order or on each other's state. Use fixtures and
  `tmp_path` for files.
- **Test the interface,** not private helpers.
- **Errors are behavior.** Assert the exception type and a key part of the message:
  `with pytest.raises(ValueError, match="exceeds")`.
- **Parametrize** similar cases instead of copying tests:
  `@pytest.mark.parametrize("raw, expected", [...])`.
- **No real models in Citadel's own tests.** Use the fake LLM fixture returning scripted replies.
- **Multi-tenant code:** always include a test that one tenant can't read or change another
  tenant's data.

## Checklist

- [ ] Every acceptance criterion has a test that fails if the criterion breaks
- [ ] Invalid input and at least two edge cases covered
- [ ] No network, clock, randomness or sleep dependencies
- [ ] Names describe behavior; no `test_1`, `test_works`
- [ ] Suite runs in under a few seconds
