---
name: implement-feature
description: "Implement an approved, bounded feature plan following project standards, tests first. Use only after /plan-feature output is approved."
argument-hint: "<requirement ID>"
---

# Implement a feature

1. Confirm the approved plan is in the conversation or in `docs/`. If not, run /plan-feature.
2. Create or switch to the branch `feat/<ID>-<short-name>`.
3. Write the tests from the plan first; run them and confirm they fail for the right reason.
4. Implement services, then controllers, hooks, DocType JSON, fixtures.
5. Run tests and `pre-commit run --all-files`; fix until both pass.
6. Follow docs/06-standards: thin controllers, settings for values, comments explain why, no tool references.
7. Stage changes in the commit sequence from the plan and propose commit messages in the format of docs/06-standards/git-workflow.md. Do not commit unless asked.
8. Update the traceability matrix row for the requirement.

Report: files changed, exact commands and output, open issues.
