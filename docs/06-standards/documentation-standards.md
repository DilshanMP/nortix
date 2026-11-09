---
title: "Documentation Standards"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Documentation Standards

## Every document
- Starts with front matter: `title`, `status` (Draft, Approved, Superseded), `owner`, `updated` (ISO date).
- Opens with its point in the first sentence: the decision, rule or result.
- Uses plain English, short sentences, active voice.
- Uses tables for items compared on several attributes, numbered lists for ordered steps, bullets for parallel items.
- Dates as `YYYY-MM-DD`; currency with code (`LKR 150,000`, `USD 25`).

## Identifiers
| Prefix | Use | Example |
| --- | --- | --- |
| LV | Leave requirement | LV-006 |
| AT | Attendance | AT-002 |
| PY | Payroll | PY-010 |
| AS | Assets and issued items | AS-003 |
| RN | Renewals | RN-001 |
| IT | IT and network | IT-004 |
| FN | Finance office | FN-002 |
| NFR | Non-functional (security, performance, availability) | NFR-SEC-003 |
| ADR | Architecture decision | ADR-0002 |

## Requirement format
Each requirement has: ID, title, rule statement, source (person or document), status, acceptance criteria, open questions.

## ADR format
Use `docs/02-architecture/adr/0000-template.md`. An ADR is never edited after approval; a new ADR supersedes it.

## Diagrams
Mermaid in Markdown so diagrams live in Git and change with the code. C4 levels: context, container, component where useful.

## Writing style for this project
- Write as the engineering team: "We store", "The system rejects".
- No filler, no marketing words, no emojis.
- Every claim about versions, prices or standards links to its source and date.
