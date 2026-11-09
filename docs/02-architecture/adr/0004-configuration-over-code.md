---
title: "ADR-0004 Customer rules as configuration"
status: "Approved"
owner: Pasindu Dilshan
date: 2026-11-09
approvers: Pasindu Dilshan
---

# ADR-0004: Customer rules as configuration

## Context
Leave amounts, thresholds, approval routes and statutory rates differ between customers and change over time. The leave Sheet broke because a rule depended on a hidden field.

## Decision
Every customer-specific value is stored in a settings DocType (for example `Nortix Leave Settings`) or a configuration DocType. Code reads values from settings; tests set them explicitly.

## Consequences
- HR changes a rule without a release.
- Settings changes are tracked (change history on).
- Defaults ship as fixtures and are reviewed per customer at onboarding.
