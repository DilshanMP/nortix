---
title: "Development Setup on Windows"
status: "Draft"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Development Setup on Windows

Frappe runs on Linux. On Windows use WSL2 (Option A) or Docker Desktop (Option B). Check the official Frappe installation docs for the exact versions required by the release in use.

## Option A: WSL2 Ubuntu with bench
1. In PowerShell (admin): `wsl --install -d Ubuntu`, restart, create the Linux user.
2. In Ubuntu, install prerequisites listed in the Frappe docs for your version (Python, Node, Yarn, MariaDB, Redis, wkhtmltopdf, uv/pip).
3. Install bench: `pip install frappe-bench` (or the method in current docs).
4. Create the bench:
   ```bash
   bench init --frappe-branch version-16 ~/frappe-bench
   cd ~/frappe-bench
   bench get-app --branch version-16 erpnext
   bench get-app --branch version-16 hrms
   bench new-site dev.localhost
   bench --site dev.localhost install-app erpnext hrms
   bench --site dev.localhost set-config developer_mode 1
   bench new-site test.localhost
   bench --site test.localhost install-app erpnext hrms
   bench --site test.localhost set-config allow_tests true
   bench start
   ```
5. Open VS Code with the WSL extension in `~/frappe-bench`.

## Option B: Docker
Use the official `frappe/frappe_docker` repository's development container guide, then run the same `bench` commands inside the container.

## Create the app and add this kit
See `docs/09-delivery/getting-started.md`.
