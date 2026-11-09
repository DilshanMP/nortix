---
title: "Devlog and Article Guide"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Devlog and Article Guide

The devlog is a dated record of real engineering decisions. It shows how the platform was designed and built, and it is the source material for articles and talks.

## Entry template (`docs/devlog/YYYY-MM-DD-<topic>.md`)

```markdown
---
title: <topic>
date: YYYY-MM-DD
refs: [ADR-0001, LV-006]
---

## Problem
What I was solving and for whom.

## What I considered
Options and the evidence I used.

## What I decided and why
The decision and the trade-off I accepted.

## What went wrong / what I learned

## Next
```

## Rules
- Write in your own words, the same day.
- Link commits, ADRs and requirement IDs.
- No personal data, no salaries, no confidential company figures.

## Turning devlogs into LinkedIn articles
Suggested series, each from real entries:
1. Why I replaced a leave spreadsheet with an ERP: the missed annual-leave case that started it.
2. Choosing a stack on a small budget: Frappe vs Odoo vs Laravel vs Spring Boot, with my scorecard.
3. Designing one product for many companies: site per customer, configuration over code.
4. Security for a small ERP: ASVS, PDPA and what I actually implemented.
5. How I use AI as an engineering assistant without losing control: plans, tests, reviews, evidence.

Before publishing: get employer approval for anything about internal systems; remove names, figures and screenshots with real data.
