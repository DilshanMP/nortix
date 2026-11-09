---
title: "AI Usage Record"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# AI Usage Record

Kept as recommended by section 17 of the master guide. This is an internal record of how AI assistance is used and controlled; it supports audits, client questions and handover.

| Area | Human responsibility | AI assistance | Control |
| --- | --- | --- | --- |
| Requirements and business rules | Gathered from HR/Finance and approved by the engineer and owners | Gap analysis, drafting | Owner confirmation per requirement |
| Architecture and technology choice | Decided by the engineer (ADR-0001 to ADR-0005) | Research, comparison drafts | ADRs with sources |
| Implementation | Engineer approves each plan and reviews each diff | Code and test drafting to approved plans | Tests, CI, review agents, code review |
| Security | Engineer owns the threat models and sign-off | Review checklists | ASVS checklist, scans, external test before ERP stage |
| Data | Engineer and HR run migrations | Transform scripts on synthetic samples | No real personal data in prompts |

## Data handling
- No secrets, credentials or real personal data are shared with AI tools.
- Production systems are never accessed by AI tools.

## Tools
| Tool | Version / plan | Since |
| --- | --- | --- |
| Claude Code | <plan> | 2026-11 |
