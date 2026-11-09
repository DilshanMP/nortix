---
title: "Prompt Engineering Guide"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Prompt Engineering Guide

Good prompts here are short because the repository holds the context. Point to files; do not paste them.

## Structure (from the master guide, section 11)

| Part | What to write |
| --- | --- |
| Context | Module and requirement IDs; which docs to read |
| Objective | The one result needed now |
| Constraints | Stack, scope, what must not change, security rules |
| Inputs | File paths, DocTypes, existing tests |
| Method | Inspect → analyse → plan → (approval) → tests → implement → verify |
| Acceptance criteria | Measurable checks, copied from the requirement |
| Output | Files changed, commands and real output, risks, open questions |

## Habits that save time and tokens
- Reference, don't paste: "Read docs/01-requirements/leave-rules.md LV-006".
- Ask for a plan first; approve; then build.
- Give examples with numbers: "mark 2026-04-01 → 10 days".
- State the stop condition: "Stop and ask if a rule is missing."
- Ask for evidence: "Show the exact test command and its output."
- Keep sessions focused; start fresh for a new requirement.
- Save decisions in ADRs so research is not repeated.

## Phrases that prevent common problems
- "Do not invent business rules; list questions instead."
- "Read values from Nortix Leave Settings; no hard-coded numbers."
- "Check permissions server-side and test with another company's user."
- "Do not change tests to make them pass; report failures."
- "Follow docs/06-standards; comments explain why, no narration."
