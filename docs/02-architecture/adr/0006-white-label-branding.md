---
title: "ADR-0006 White-label branding per customer site"
status: "Approved"
owner: Pasindu Dilshan
date: 2026-11-09
approvers: Pasindu Dilshan
---

# ADR-0006: White-label branding per customer site

## Context
The product is named Nortix. Customers want their staff to see their own name and logo (Akvora Group may call its site "Akvora One"). Renaming the code for each customer would break upgrades and the shared codebase.

## Options considered
| Option | Pros | Cons |
| --- | --- | --- |
| Brand per site through settings | One codebase; brand changes without a release | Some screens (phone app manifest, emails) need checking per release |
| Fork or rename the app per customer | Full control | Separate code per customer; upgrades multiply |

## Decision
The app and package name stay `nortix` everywhere in code. Each site sets its brand through settings:
- Website Settings and Navbar Settings: app name, app logo, favicon, splash and login images
- Letter Head per Company for print formats
- Email Account signature and footer
- `Nortix Branding Settings` (Single DocType, R1): brand name, short name, primary colour, "Powered by Nortix" toggle, used by custom pages, emails and reports

## Consequences
- Custom code never prints "Nortix" to end users directly; it reads the brand name from settings.
- The release checklist includes a branding check on a second test site with a different brand.
- The phone app name and icon are verified per Frappe HR release; an override is added only if needed.

## Review triggers
A customer requires its own domain-specific app store listing or native app.
