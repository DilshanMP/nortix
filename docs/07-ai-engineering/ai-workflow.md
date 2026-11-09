---
title: "AI-Assisted Engineering Workflow"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# AI-Assisted Engineering Workflow

The engineer owns the problem, the rules, the architecture, the decisions and the review. The AI assistant drafts, searches, implements to an approved plan and checks. Steps 1, 5, 9 and 11 are human gates.

| # | Step | Who leads | Tool support | Output |
| --- | --- | --- | --- | --- |
| 1 | Discover the rule with the business owner | Engineer | /analyze-requirements | Requirement with ID, **gate: owner confirms** |
| 2 | Write acceptance criteria as examples | Engineer | /analyze-requirements | Criteria in `docs/01-requirements` |
| 3 | Decide architecture questions | Engineer | /architecture-review, /research-technology, /write-adr | ADR |
| 4 | Prototype screens with users | Engineer | /review-ui-ux | Journey notes in `docs/ux` |
| 5 | Plan the change | Engineer | /plan-feature in plan mode | **Gate: engineer approves plan** |
| 6 | Write tests first | Engineer + assistant | /implement-feature | Failing tests |
| 7 | Implement in small commits | Assistant to plan, engineer reviews each diff | /implement-feature, /build-doctype | Code |
| 8 | Verify | Assistant runs, engineer reads real output | /verify-feature | Evidence |
| 9 | Review | Engineer + review agents | /review-security, test-reviewer | **Gate: engineer approves PR** |
| 10 | Staging and reconciliation | Engineer + business owner | /migrate-data | Reconciliation report |
| 11 | Release | Engineer | /release-readiness | **Gate: owner sign-off** |
| 12 | Record | Engineer | /devlog, /commit-message | Devlog, changelog, traceability |

## Working rules
- Start every session from the repository, not from memory: CLAUDE.md, the requirement, the ADRs.
- One requirement per session where possible; `/clear` between unrelated tasks.
- Use plan mode for anything touching money, payroll, permissions, migration or architecture.
- Read every diff before accepting it. If you cannot explain a line, do not merge it.
- Never paste secrets or real personal data into prompts. Use synthetic examples.
- Every dependency the assistant proposes is checked: maintenance, licence, audit result.
- Keep the AI usage record (`ai-usage-record.md`) current.
