---
name: architecture-review
description: "Compare architecture options, module boundaries, data ownership, failure modes and ADR quality for a proposed change. Use before any change that adds a module, DocType family, integration, dependency or deployment component."
argument-hint: "<proposal or ADR file>"
---

# Architecture review

1. Read `docs/02-architecture/architecture-overview.md`, the ADRs and the proposal.
2. Check fit with ADR-0001 to ADR-0005: platform-first, site per customer, no core edits, configuration over code, localisation module.
3. Evaluate at least two options, including "use the standard Frappe/ERPNext feature".
4. Examine data ownership, company isolation, transactions, idempotency, failure and retry, upgrade impact, operational cost.
5. If a decision is needed, draft an ADR from `adr/0000-template.md` with status Proposed.

Output: options table, recommendation with trade-offs, risks, review triggers, draft ADR if needed.
