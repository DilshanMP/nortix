---
title: "ADR-0003 All customisation in the nortix app; no core edits"
status: "Approved"
owner: Pasindu Dilshan
date: 2026-11-09
approvers: Pasindu Dilshan
---

# ADR-0003: All customisation in the nortix app; no core edits

## Context
Edits to Frappe, ERPNext or Frappe HR source are lost or conflict on upgrade.

## Decision
Custom DocTypes, custom fields, hooks, scripts, reports, print formats and workspaces live in the `nortix` app and are exported as fixtures where needed. Server and client scripts created in the UI are moved into the app before release.

## Consequences
- Upgrades stay predictable.
- Some behaviour needs overrides through `hooks.py` (`doc_events`, `override_doctype_class`); each override is documented in the module README.

## Review triggers
A required change cannot be made through hooks or overrides; propose an upstream contribution first.
