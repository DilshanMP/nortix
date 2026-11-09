---
title: "Code Review Checklist"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Code Review Checklist

## Correctness
- [ ] Implements the linked requirement exactly; nothing invented
- [ ] Boundaries and failure cases handled (dates, zero, negative, duplicates)
- [ ] Customer-specific values read from settings, not hard-coded

## Security and isolation
- [ ] Server-side permission checks on every new endpoint and action
- [ ] Company and branch isolation respected in queries and reports
- [ ] No raw SQL built from input; no secrets or personal data in code or logs
- [ ] New dependencies justified and scanned

## Data integrity
- [ ] Submitted documents are not edited; corrections use cancel/amend
- [ ] Jobs and imports are idempotent
- [ ] Patches are reversible or have a documented recovery path

## Tests and evidence
- [ ] Tests written for each acceptance criterion, including wrong role and other company
- [ ] CI passes; real output attached
- [ ] Traceability matrix updated

## Readability
- [ ] Names describe business meaning
- [ ] Controllers thin; logic in services
- [ ] Comments explain why; no narration or leftover debug code
- [ ] Docs and changelog updated
