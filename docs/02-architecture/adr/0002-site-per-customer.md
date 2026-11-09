---
title: "ADR-0002 One site per customer organisation"
status: "Approved"
owner: Pasindu Dilshan
date: 2026-11-09
approvers: Pasindu Dilshan
---

# ADR-0002: One site per customer organisation

## Context
The product must serve Akvora Group and other companies. Customer data must never mix.

## Options considered
| Option | Pros | Cons |
| --- | --- | --- |
| One site (database) per customer | Strongest isolation; independent backups, upgrades, settings | More sites to operate |
| All customers in one site as Companies | Fewer sites | One permission mistake exposes another customer's data; shared admins |

## Decision
One Frappe site per customer organisation. Companies inside a site are for that customer's own legal entities.

## Consequences
- Onboarding a customer is a repeatable runbook.
- Upgrades are applied per site; a bench can host several sites.

## Review triggers
Hundreds of small customers where per-site cost becomes the main constraint.
