---
name: verify-feature
description: "Map each acceptance criterion of a requirement to real test output and evidence, and list anything unverified. Use before marking a requirement Built or Verified."
argument-hint: "<requirement ID>"
---

# Verify a feature

1. Read the requirement's acceptance criteria.
2. Run the tests that cover them; capture the exact command and output.
3. Build a table: criterion → test name → result (pass/fail/not covered) → evidence location.
4. Any criterion without passing evidence is listed as unverified. Do not mark it done.
5. Update `docs/01-requirements/traceability.csv`.
