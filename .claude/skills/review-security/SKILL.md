---
name: review-security
description: "Review a change for authorisation, input handling, secrets, company isolation, data exposure and dependency risk against the project's ASVS checklist. Use before every pull request that touches code."
argument-hint: "<branch, diff or files>"
context: fork
agent: security-reviewer
---

# Security review

Review the diff against:
- docs/05-security/secure-coding.md
- docs/05-security/asvs-l2-checklist.md
- the module's threat model

Report findings as: severity, file:line, issue, exploit scenario, fix. Report "no findings" only after checking every whitelisted method, query, permission flag and new dependency in the diff.
