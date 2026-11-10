# Nortix

A department-organised business platform for multi-company organisations, built on Frappe Framework, Frappe HR and ERPNext. One custom app (`nortix`) adds the rules, registers and reports that the standard apps do not cover. The first customer deployment is Akvora Group.

**Name.** Nortix is the product name in code, Git and documentation. Each customer site carries its own brand name and logo (for example "Akvora One"); see [ADR-0006](docs/02-architecture/adr/0006-white-label-branding.md).

## What it covers

| Workspace | Modules | Status |
| --- | --- | --- |
| HR | Leave balancing, attendance, payroll | Leave: discovery |
| Admin and IT | Assets and insurance, items issued to staff, renewals, IT helpdesk, network register | Planned |
| Finance | Petty cash, cheque collection ledger, utility bills | Planned |
| Logistics, Sales | Purchasing, stock, warehouses, sales distribution | ERP stage, after the ERP gate |
| Management | Cross-company dashboards | Planned |

## Principles

- Business correctness before novelty.
- Configuration over code: every customer-specific rule lives in settings, never in source.
- No edits to Frappe, ERPNext or Frappe HR core. All custom work lives in this app.
- Security, audit, backup and recovery are requirements, not add-ons.
- Every change is small, reviewed, tested and traceable to an approved requirement.

## Repository map

| Path | Contents |
| --- | --- |
| `CLAUDE.md` | Working rules for AI-assisted development |
| `docs/00-vision` | Product vision, scope, glossary |
| `docs/01-requirements` | Requirement register, business rules, traceability, open questions |
| `docs/02-architecture` | Architecture overview, multi-tenancy, integrations, ADRs |
| `docs/03-design` | Design patterns, DocType conventions, API design |
| `docs/04-data` | Database architecture, data dictionary, classification, migration |
| `docs/05-security` | Security architecture, threat models, ASVS checklist, PDPA, incident response |
| `docs/06-standards` | Engineering principles, coding, testing, documentation and Git standards |
| `docs/07-ai-engineering` | AI workflow, prompt library, tools, AI usage record |
| `docs/08-operations` | Environments, setup, deployment, backup, monitoring, upgrades |
| `docs/09-delivery` | Roadmap, definition of done, release checklist |
| `docs/ux`, `docs/testing` | Journeys and screen notes; test strategy and evidence |
| `docs/devlog` | Dated engineering journal of decisions |
| `.claude/` | Project rules, skills, review agents, hooks and settings |
| `nortix/` | Application code (created by `bench new-app`) |

## Getting started

Follow [docs/09-delivery/getting-started.md](docs/09-delivery/getting-started.md).

## Ownership and licence

Product owner and lead engineer: Pasindu Dilshan.

The `nortix` app is proprietary; see `license.txt` and decision D8 in `docs/01-requirements/open-questions.md`. Frappe Framework (MIT), ERPNext and Frappe HR (GPL-3.0) keep their own licences.
