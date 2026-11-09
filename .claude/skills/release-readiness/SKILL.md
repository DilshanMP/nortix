---
name: release-readiness
description: "Check a release for CI status, migrations, backup, approvals, monitoring and rollback before deployment. Use before any staging-to-production release."
argument-hint: "<version>"
disable-model-invocation: true
---

# Release readiness

Work through docs/09-delivery/release-checklist.md and report each item as done, not done or not applicable, with evidence. A release is ready only when every mandatory item is done. Never run the deployment itself.
