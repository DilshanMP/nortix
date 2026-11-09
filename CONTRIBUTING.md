# Contributing

## Workflow

1. Pick an approved requirement from `docs/01-requirements/requirements-register.md`.
2. Create a branch: `feat/LV-004-annual-allocation`, `fix/LV-008-balance-rounding`, `docs/adr-0006-backups`.
3. Plan the change (see `docs/07-ai-engineering/ai-workflow.md`, steps 5 to 9).
4. Write tests first for every rule in scope.
5. Implement in small commits that each build and pass tests.
6. Run `pre-commit run --all-files` and the test suite locally.
7. Open a pull request using the template. Link requirement IDs.
8. Update the traceability matrix and any affected docs in the same pull request.
9. Merge only after CI passes and the review checklist is complete.

## Standards

- Engineering principles: `docs/06-standards/engineering-principles.md`
- Python and Frappe: `docs/06-standards/coding-standards-python.md`
- JavaScript: `docs/06-standards/coding-standards-javascript.md`
- Testing: `docs/06-standards/testing-standards.md`
- Documentation: `docs/06-standards/documentation-standards.md`
- Git and commits: `docs/06-standards/git-workflow.md`
- Code review: `docs/06-standards/code-review-checklist.md`
