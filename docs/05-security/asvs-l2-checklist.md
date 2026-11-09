---
title: "OWASP ASVS 5.0 Level 2 Checklist (custom code)"
status: "Draft"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# OWASP ASVS 5.0 Level 2 Checklist (custom code)

A working subset for the `nortix` app, grouped by ASVS 5.0 chapter. Confirm chapter numbers and requirement IDs against the current release at https://asvs.owasp.org before each review. Record evidence for each item per release.

| Chapter | Check for every feature | Evidence |
| --- | --- | --- |
| V1 Encoding and sanitisation | No raw SQL from input; framework escaping; no `frappe.db.sql` with string formatting | Code review, semgrep |
| V2 Validation and business logic | Server-side validation of every field and rule; limits on quantities and dates; business rules cannot be skipped by order of calls | Tests |
| V3 Web frontend security | No inline secrets in JS; framework CSP and cookie flags left on | Review |
| V4 API and web service | Whitelisted methods check permissions; no guest endpoints; rate limits where abuse is possible | Tests, review |
| V5 File handling | Uploads private by default; type and size limits; no execution of uploaded files | Config review |
| V6 Authentication | Password policy; 2FA for privileged roles; lockout and rate limiting | Settings screenshot |
| V7 Session management | Session expiry set; logout invalidates session | Settings |
| V8 Authorisation | Role and User Permission checks server-side; company isolation tests | Tests |
| V11 Cryptography | No custom crypto; Password fields for secrets; TLS only | Review |
| V12 Secure communication | HTTPS everywhere; HSTS; TLS to origin | Scan |
| V13 Configuration | Secrets outside Git; debug off in production; least-privilege service accounts | Config review |
| V14 Data protection | Sensitive fields at higher permlevel; excluded from logs and default exports | Review |
| V15 Secure coding and architecture | Dependency scan clean or accepted; no deprecated APIs; module boundaries kept | CI |
| V16 Logging and error handling | Security events logged; no personal data or secrets in logs; generic error messages | Review |
