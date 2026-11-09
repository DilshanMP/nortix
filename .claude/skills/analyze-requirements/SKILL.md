---
name: analyze-requirements
description: "Review a requirement or business rule for gaps, ambiguity, missing stakeholders, conflicts and untestable acceptance criteria before design or build. Use when a new rule arrives or before planning a feature."
argument-hint: "<requirement ID or file>"
---

# Analyze requirements

1. Read `docs/01-requirements/` for the given ID, plus `open-questions.md` and related ADRs.
2. Check each rule for: clear trigger, inputs, outputs, boundaries (dates, quarters, zero), exceptions, approvals, data owner, company/branch scope, configuration values.
3. Compare with the source (Sheet, legacy ERP, owner statements); list conflicts.
4. Rewrite unclear acceptance criteria as concrete examples (input → expected result).
5. Do not invent answers. Every gap becomes a question with the owner who must answer.

Output:
- Findings table: ID, issue, why it matters, proposed question, owner
- Suggested acceptance criteria (marked "proposed")
- Requirements ready to plan vs blocked
