---
title: "Getting Started"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Getting Started

## 1. Confirm the product name (D7)
The product name is Nortix (app `nortix`). Before the first public use, confirm the `.com` domain, the WIPO Global Brand Database, Sri Lanka NIPO, GitHub and PyPI. The customer-facing brand is set per site (ADR-0006) and does not need a code change.

## 2. Set up the bench
Follow `docs/08-operations/dev-setup-windows.md`.

## 3. Create the app
```bash
cd ~/frappe-bench
bench new-app nortix          # answer the prompts; licence per decision D8
bench --site dev.localhost install-app nortix
bench --site test.localhost install-app nortix
```

## 4. Add this kit to the app repository
Copy everything from this kit into `apps/nortix/` (the app root). Keep the files `bench new-app` generated (`pyproject.toml`, `nortix/hooks.py`, its `.pre-commit-config.yaml` hooks). Merge `.pre-commit-config.yaml` and `.github/workflows/ci.yml` with the generated ones if versions differ.

## 5. Set your Git identity and make the first commit
```bash
cd apps/nortix
git config user.name "Pasindu Dilshan"
git config user.email "<your GitHub email>"
pre-commit install
git add .
git commit -m "docs: add engineering baseline (requirements, architecture, security, standards)"
```

## 6. Create the GitHub repository
Private repository; protect `main` (pull requests required, CI must pass, no force push). Replace `@YOUR_GITHUB_USERNAME` in `.github/CODEOWNERS`.

## 7. Open Claude Code in the app folder
Trust the folder, run `/` to check the project skills are listed, then start with Phase 1:
```text
/analyze-requirements LV-006
```
