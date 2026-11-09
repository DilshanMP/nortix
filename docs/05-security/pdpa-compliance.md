---
title: "Sri Lanka PDPA Readiness"
status: "Draft"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Sri Lanka PDPA Readiness

The Personal Data Protection Act No. 9 of 2022 core duties become operative on 2027-01-01 (Gazette 2498/16, reported by Daily FT). Confirm details with the Data Protection Authority and legal advice; this is an engineering checklist, not legal advice.

| Duty | What the platform does | Owner |
| --- | --- | --- |
| Lawful processing and purpose | Record of processing per data class | Management, HR |
| Data minimisation | Collect only fields with a stated purpose; review custom fields yearly | Product owner |
| Accuracy and correction | Employees can view their data; HR corrects through tracked changes | HR |
| Security | Controls in `security-architecture.md` | Product owner |
| Retention | Periods in `data-classification.md`; deletion or anonymisation job after the period | HR, product owner |
| Data subject requests | Procedure to export an employee's data within the legal time limit | HR |
| Breach notification | Steps in `incident-response.md` | Management |
| Processors | Written agreement with the hosting provider | Management |
| Cross-border transfer | Review before hosting outside Sri Lanka (decision D3) | Management, legal |
| Data Protection Officer | Appoint if required | Management |
