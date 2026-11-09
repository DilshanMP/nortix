---
title: "Product Vision and Scope"
status: "Draft"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Product Vision and Scope

Nortix gives a multi-company organisation one place to run HR, admin, IT and finance office work by department, and grows into its ERP. It is built once and configured per customer, so the same product serves Akvora Group first and other companies later.

## Problem
- Leave, attendance and office records live in spreadsheets and a 20-year-old ERP.
- Rules are hidden in formulas; errors (such as missing annual leave) are found late.
- Each department keeps its own files; management has no cross-company view.

## Users
| Group | Needs |
| --- | --- |
| All staff | Apply for leave, check in, see balances and payslips on the phone |
| HR | Leave rules, attendance, payroll, employee records |
| Finance | Petty cash, cheques, utility bills, payroll postings, later full accounts |
| Admin and IT | Assets, insurance, items issued to staff, renewals, helpdesk, network register |
| Logistics, Sales | ERP stage: purchasing, stock, warehouses, sales distribution |
| Management | Approvals and cross-company dashboards |

## Product rules
1. Multi-company inside one customer site; one site per customer organisation.
2. Everything that differs between customers is configuration.
3. Country rules (statutory payroll, tax) live in a localisation module; Sri Lanka first.
4. Web for office work; installable phone app for staff.
5. White-label: each customer sees its own brand name and logo; Nortix appears only as "Powered by Nortix" (ADR-0006).

## Release scope
| Release | Scope |
| --- | --- |
| R1 | Leave balancing converted from the leave Sheet |
| R2 | Attendance (devices, office-network and GPS check-in) and payroll (Sri Lanka) |
| R3 | Assets and insurance, issued items, renewals, IT helpdesk and network register |
| R4 | Petty cash, cheque collection ledger, utility bills |
| ERP | Purchasing, stock, warehouses, sales distribution, accounts, audit, after the ERP gate |

## Out of scope until decided
POS, manufacturing, e-commerce, marketing automation.

## Success measures (to approve)
- Leave balances match approved figures for 100% of employees at go-live.
- HR spends less time on monthly leave reports (baseline to measure in discovery).
- Zero manual edits to submitted leave or payroll records.
