---
title: "Multi-Company and Multi-Customer Design"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Multi-Company and Multi-Customer Design

Two levels of separation make the product reusable: a separate site (database) per customer organisation, and Companies with user permissions inside each site.

| Level | Mechanism | Example |
| --- | --- | --- |
| Customer organisation | One Frappe site and database each, on the same or separate servers | `akvora.nortix.example`, `customer2.nortix.example` |
| Legal entity | ERPNext Company record; every transactional DocType has a `company` field | Akvora International (Pvt) Ltd |
| Location | Branch, Warehouse | Head office, Udahamulla warehouse |
| Department | Department; workspace and roles | HR, Finance |
| User access | Roles + User Permissions on Company and Branch | An HR officer limited to one company |

## Rules
1. No query, report or API returns rows without applying the user's permissions.
2. Custom DocTypes holding company data include `company` (mandatory) and, where relevant, `branch`.
3. Customer differences are settings, fixtures or localisation, never code branches like `if customer == ...`.
4. Each customer site has its own backups, admin accounts and encryption key.
5. A new customer is onboarded by: create site, install apps, load fixtures, enter settings, import masters. Documented in `docs/08-operations/customer-onboarding.md`.

## Tests required
- User restricted to Company A cannot read Company B records by form, list, report, API or export.
- Settings changed in one site do not affect another site.
