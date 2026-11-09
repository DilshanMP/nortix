---
paths:
  - "nortix/**/test_*.py"
---

# Test rules

- Follow docs/06-standards/testing-standards.md.
- Synthetic data only; no real names, NIC numbers, salaries or contacts.
- Cover valid, boundary, invalid, wrong role, other company and duplicate-run cases.
- Never weaken an assertion to make a test pass; report the failure.
