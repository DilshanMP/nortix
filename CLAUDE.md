# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Nortix: Engineering Instructions

## Role
Work as a senior software engineer on a Frappe/ERPNext product. Act as architect, business analyst, security engineer, UX engineer or test engineer as the task requires. The project owner makes every product, architecture and business decision.

## What this is
A multi-company business platform built on Frappe Framework (version-16), Frappe HR and ERPNext.
All custom code lives in the `nortix` app. Never edit frappe, erpnext or hrms core.
One site per customer organisation; many Companies inside a site.

The engineering baseline (docs, `.claude/`, CI, pre-commit) sits alongside the code that
`bench new-app nortix` generates (docs/09-delivery/getting-started.md). Keep the generated
files (`pyproject.toml`, `nortix/hooks.py`, `nortix/modules.txt`, `nortix/patches.txt`) and
merge rather than overwrite. `pyproject.toml` holds the ruff config that sets tab indentation;
without it `ruff-format` reformats to spaces.

## Source of truth
- Requirements and business rules: docs/01-requirements (IDs such as LV-004); open items in open-questions.md
- Decisions: docs/02-architecture/adr (approved ADRs are never edited; supersede with a new ADR)
- Standards: docs/06-standards; DocType conventions: docs/03-design/doctype-conventions.md
Do not invent business rules. If a rule is missing or two sources conflict, stop and ask.

## Commands
Frappe runs on Linux: run `bench` from `~/frappe-bench` inside WSL2 or the dev container
(docs/08-operations/dev-setup-windows.md). Sites: `dev.localhost` (developer_mode) and
`test.localhost` (allow_tests). Never point a command at any other site.

```bash
bench --site test.localhost run-tests --app nortix                                   # full suite
bench --site test.localhost run-tests --app nortix --module nortix.hr_leave.services.test_annual  # one module
bench --site test.localhost run-tests --doctype "Issued Item"                        # one DocType
bench --site dev.localhost migrate                                                   # after DocType JSON or patches change
bench build --app nortix                                                             # front-end assets
pre-commit run --all-files                                                           # ruff, ruff-format, gitleaks, yaml/json checks
```
CI (.github/workflows/ci.yml) runs pre-commit, gitleaks, semgrep on `nortix/`, and the test
suite on a fresh bench with erpnext and hrms installed.

## Architecture
Modular monolith inside one app (docs/02-architecture/architecture-overview.md):
- Modules under `nortix/<module>/`: `hr_leave`, `hr_attendance`, `localisation/lk`, `admin_assets`,
  `admin_renewals`, `it_network`, `finance_office`, `core`.
- Layering: DocType controllers and `api.py` only orchestrate; business rules live in
  `services/*.py` and are unit-tested there. Queries go in `services/queries.py` using `frappe.qb`.
- A module calls another only through its `services` functions, never by reading its tables.
- Extend core behaviour through `doc_events` and scheduler events in `hooks.py`, using standard
  DocTypes (e.g. Leave Allocation) so core balances and reports keep working.
- Customer values live in `Nortix ... Settings` single DocTypes (ADR-0004); country statutory
  rules sit behind a common interface in `localisation/<country>/` (ADR-0005).
- External systems go through adapters in `integrations/<system>.py`; data changes ship as
  `patches/` + `patches.txt`.
- Jobs and imports are idempotent via unique keys (e.g. employee, leave_type, period, source).
- Money, leave and payroll records are submittable; correct by cancel and amend, never `db_set`.
- Isolation (docs/02-architecture/multi-tenancy.md): every transactional DocType has a mandatory
  `company` field; every query, report and API applies the user's permissions. Tests must prove
  a Company A user cannot see Company B data by form, list, report, API or export.

Path-scoped rules in `.claude/rules/` load automatically for Python, JS, DocType JSON, tests and docs.
Hooks block production access, printing secrets, `--no-verify` and generated-by trailers, and
lint every edited `.py`/`.json` file.

## Workflow
Requirement → /analyze-requirements → /plan-feature (plan mode, engineer approves) →
/implement-feature (tests first) → /verify-feature → /review-security and review agents.
Full table with human gates: docs/07-ai-engineering/ai-workflow.md.
User-invoked only: /commit-message, /devlog (entries in docs/devlog), /release-readiness.

## Before changing code
Read the requirement, the related DocTypes, services and tests.
Use plan mode and wait for approval for anything that touches payroll, money,
permissions, data migration, multi-company isolation or architecture.

## Rules
- One feature per branch and pull request (`feat/<ID>-<short-name>`). Small, reversible changes.
- Customer-specific values live in settings DocTypes, never in code.
- Every business rule has a test. Never change a test only to make it pass.
- Tests cover valid, boundary (e.g. 31 Mar / 1 Apr), invalid, wrong role, other company and duplicate run.
- Enforce permissions on the server. Hiding a field or button is not security.
- No secrets or real personal data in code, tests, fixtures, prompts or logs.
- No new dependency without stating why and getting approval.
- Never run commands against production. Migrations and deploys need human approval.
- Follow docs/06-standards. Python uses tabs. Comments explain why, not what. No narration
  comments, no tool or assistant references in code, comments, commits or docs.

## Verify
bench --site test.localhost run-tests --app nortix
pre-commit run --all-files
Report the exact commands and real output. Work is not done until both pass.

## Commits
Do not commit unless asked. Use the format in docs/06-standards/git-workflow.md
(Conventional Commits, scope = module, `Refs: <ID>` footer).
No Co-Authored-By or generated-by trailers.

## Completion report
Requirement IDs covered, files changed, commands and results, security and
data-integrity notes, open questions, suggested next step.
