---
title: "Prompt Library"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Prompt Library

Copy, fill the `<...>` parts, and run. Each prompt matches a step in `ai-workflow.md`.

## 1. Requirement review
```text
/analyze-requirements LV-<n>
Source: docs/01-requirements/leave-rules.md. Compare with the leave Sheet rule I describe here: <rule in my words>.
List gaps as questions for HR. Do not answer them yourself.
```

## 2. Architecture question
```text
/architecture-review
Question: <e.g. how should renewals reminders be built: Notification on a custom DocType or a scheduled job?>
Constraints: ADR-0001 to ADR-0005. Prefer standard Frappe features. Give two options and trade-offs; draft an ADR if a decision is needed.
```

## 3. Plan a feature (plan mode)
```text
/plan-feature LV-<n>
Read: the requirement, docs/04-data/data-dictionary-leave.md, nortix/hr_leave/.
Include tests for: <boundaries>. Include the commit sequence. Wait for my approval.
```

## 4. Implement an approved plan
```text
/implement-feature LV-<n>
Follow the plan we approved above. Tests first. Run:
bench --site test.localhost run-tests --app nortix --module <module path>
and pre-commit. Show real output. Do not commit; propose messages with /commit-message.
```

## 5. New DocType
```text
/build-doctype "<DocType Name>" <module>
Fields: <field list>. Submittable: <yes/no>. Roles: <roles>. Company isolation required.
```

## 6. Security review
```text
/review-security
Scope: changes on this branch compared with main. Use the leave threat model.
```

## 7. Test review
```text
Use the test-reviewer agent on LV-<n>. Report criteria without passing tests.
```

## 8. Verify
```text
/verify-feature LV-<n>
Update traceability.csv with test names and evidence paths.
```

## 9. Data migration
```text
/migrate-data "Leave Sheet" "Employee, Leave Application"
Work only with column names and synthetic sample rows. Build a dry-run mode and an error report without personal values.
```

## 10. Bug fix
```text
Bug: <what happened, expected, actual> in <module>. Requirement: <ID>.
First write a failing test that reproduces it, then fix, then run the module's tests.
```

## 11. Release
```text
/release-readiness v<x.y.z>
```

## 12. End of session
```text
/devlog
```
