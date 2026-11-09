---
title: "Git Workflow and Commit Standards"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Git Workflow and Commit Standards

## Identity
Commits are authored by the engineer who reviewed and accepts the change. Set your identity once per machine:

```bash
git config --global user.name "Pasindu Dilshan"
git config --global user.email "<your GitHub email>"
```

Signed commits are recommended: `git config --global commit.gpgsign true` with an SSH or GPG key registered on GitHub.

## Branches
- `main`: protected; always deployable; changes only through pull requests.
- Feature branches: `feat/<ID>-<short-name>`, `fix/<ID>-<short-name>`, `docs/<topic>`, `chore/<topic>`.

## Commit messages (Conventional Commits)

```text
<type>(<scope>): <summary in imperative, max 72 chars>

<why the change was made; what rule or problem it addresses>

Refs: LV-006
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`, `ci`, `build`, `security`.
Scopes: module names (`hr-leave`, `admin-assets`, `finance`, `core`, `ci`, `docs`).

Examples:
```text
feat(hr-leave): allocate first-year annual leave by quarter of 1-year mark

The leave Sheet only granted annual leave when a Permanent Date was set,
so staff who passed their 1-year mark received nothing. Allocation now
uses the confirmation date and the quarter amounts in Leave Settings.

Refs: LV-006
```

```text
test(hr-leave): cover 31 March and 1 April quarter boundaries

Refs: LV-006
```

## Rules
- One logical change per commit; the build and tests pass at every commit.
- Commit as you work. History should show the real order of the work: requirements, design, tests, implementation, fixes.
- Never rewrite history on `main`. Never force-push shared branches.
- No generated-by or co-author trailers; the author is the accountable engineer.
- No secrets, personal data or large binaries. Gitleaks runs in pre-commit and CI.

## Pull requests
- Title in commit format; description from `.github/pull_request_template.md`.
- Link requirement IDs; attach test output; note risks and rollback.
- Squash-merge feature branches unless the individual commits tell a useful story.

## Tags and releases
Semantic Versioning: `v0.1.0` first internal release; `CHANGELOG.md` updated in the release pull request.
