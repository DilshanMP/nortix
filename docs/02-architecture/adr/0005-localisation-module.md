---
title: "ADR-0005 Country rules in a localisation module"
status: "Approved"
owner: Pasindu Dilshan
date: 2026-11-09
approvers: Pasindu Dilshan
---

# ADR-0005: Country rules in a localisation module

## Context
Payroll and tax rules are country-specific. The first customer is in Sri Lanka (EPF, ETF, APIT).

## Decision
Country rules live in `nortix/localisation/<country code>/` behind a common interface (salary components, tax slabs, return file exporters). Sri Lanka (`lk`) is the first implementation.

## Consequences
- Adding a country does not change HR or payroll modules.
- Statutory rates are data with effective dates, verified against official sources before each payroll year.
