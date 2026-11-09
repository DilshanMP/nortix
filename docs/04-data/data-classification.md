---
title: "Data Classification and Retention"
status: "Draft"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Data Classification and Retention

| Class | Examples | Access | Storage rules | Retention (to approve) |
| --- | --- | --- | --- | --- |
| Restricted personal | NIC, date of birth, salary, bank account, medical leave reasons | HR, Payroll, the employee | Higher permlevel; never in logs, tests, prompts or exports by default | Employment + 7 years |
| Personal | Name, phone, email, designation, leave records | HR, managers for their team, the employee | Company and branch permissions | Employment + 7 years |
| Confidential business | Accounts, cheques, contracts, renewals, network register | Finance, Admin and IT | Role permissions; network secrets stay in the password manager | 7 years (financial) |
| Internal | Workspaces, settings, reports | Staff by role | Standard | While in use |

## PDPA (Sri Lanka, from 2027-01-01)
- Record the purpose and legal basis for each personal data class.
- Support access and correction requests from employees.
- Notify breaches as required; see `docs/05-security/incident-response.md`.
- Hosting outside Sri Lanka needs a cross-border transfer review (decision D3).
