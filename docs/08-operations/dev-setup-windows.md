---
title: "Development Setup on Windows"
status: "Draft"
owner: Pasindu Dilshan
updated: 2026-11-10
---

# Development Setup on Windows

We develop in WSL2 Ubuntu 24.04 with a native bench on Frappe version-16; the steps below were run and checked on a Windows 11 machine on 2026-11-09.

Frappe runs on Linux only. Option B (Docker) remains available through the official `frappe/frappe_docker` development container guide; the rest of this document covers Option A.

## Versions

Versions follow the test job in `.github/workflows/ci.yml`. Check the official Frappe installation docs for the release in use before changing them.

| Component | Version | Source |
| --- | --- | --- |
| Ubuntu (WSL2) | 24.04 LTS | `wsl --install` |
| Python | 3.14 | `uv python install` |
| Node | 24 | NodeSource APT repository |
| Yarn | 1.22 | `npm install -g yarn` |
| MariaDB | 11.8 | MariaDB APT repository (Ubuntu 24.04 ships 10.11) |
| Redis | 7.0 | Ubuntu package |
| wkhtmltopdf | 0.12.6 | Ubuntu package |
| frappe-bench | 5.x | `uv tool install` |
| Frappe, ERPNext, HRMS | `version-16` branch | `bench init`, `bench get-app` |

## Who runs what

| Marker | Meaning |
| --- | --- |
| PowerShell | Run in a Windows PowerShell window |
| Ubuntu | Run inside Ubuntu (`wsl -d Ubuntu-24.04`) as `pasindu` |
| Ubuntu root | Run with `sudo`, or from PowerShell with `wsl -d Ubuntu-24.04 -u root -- ...` |
| Engineer only | Involves a password; never paste it into a prompt, file or log |

## Phase 1: Ubuntu in WSL2

1. PowerShell: install Ubuntu without launching it.
   ```powershell
   wsl --install -d Ubuntu-24.04 --no-launch
   ```
2. Ubuntu root: create the Linux user and make it the default.
   ```bash
   useradd -m -s /bin/bash -G sudo pasindu
   ```
3. Ubuntu root: write `/etc/wsl.conf`. Systemd runs MariaDB and Redis as services. Without `appendWindowsPath=false`, Windows Node, Python and PHP leak into the Linux PATH and break bench.
   ```ini
   [user]
   default=pasindu
   [boot]
   systemd=true
   [interop]
   appendWindowsPath=false
   ```
4. PowerShell: restart the distribution so the settings apply.
   ```powershell
   wsl --terminate Ubuntu-24.04
   ```
5. PowerShell, engineer only: set the Linux password used by `sudo`.
   ```powershell
   wsl -d Ubuntu-24.04 -u root passwd pasindu
   ```

## Phase 2: System packages

1. Ubuntu root: base packages.
   ```bash
   apt-get update
   apt-get install -y git curl wget ca-certificates gnupg build-essential pkg-config \
     redis-server libmariadb-dev xvfb libfontconfig1 libxrender1 libxext6 fontconfig cron \
     python3-dev python3-pip pipx wkhtmltopdf
   ```
2. Ubuntu root: add the MariaDB 11.8 and Node 24 repositories with their signing keys. We do not pipe remote setup scripts into a root shell.
   ```bash
   install -d -m 0755 /etc/apt/keyrings
   curl -fsSL https://mariadb.org/mariadb_release_signing_key.pgp -o /etc/apt/keyrings/mariadb-keyring.pgp
   cat > /etc/apt/sources.list.d/mariadb.sources <<EOF
   Types: deb
   URIs: https://deb.mariadb.org/11.8/ubuntu
   Suites: noble
   Components: main
   Signed-By: /etc/apt/keyrings/mariadb-keyring.pgp
   EOF
   curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
   echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_24.x nodistro main" \
     > /etc/apt/sources.list.d/nodesource.list
   apt-get update
   apt-get install -y mariadb-server mariadb-client nodejs
   npm install -g yarn
   systemctl enable --now mariadb redis-server
   ```
3. Ubuntu root: set the character set Frappe requires in `/etc/mysql/mariadb.conf.d/99-frappe.cnf`, then `systemctl restart mariadb`.
   ```ini
   [mysqld]
   character-set-client-handshake = FALSE
   character-set-server = utf8mb4
   collation-server = utf8mb4_unicode_ci

   [mysql]
   default-character-set = utf8mb4
   ```
4. PowerShell, engineer only: set the MariaDB root password. Answer: Enter (blank current password), `n` to unix_socket, `Y` to change the root password, `Y` to the rest. Keep the password in a password manager.
   ```powershell
   wsl -d Ubuntu-24.04 -u root mariadb-secure-installation
   ```

## Phase 3: Python and bench

Ubuntu:
```bash
pipx install uv
pipx ensurepath
uv python install 3.14
uv tool install --python 3.14 frappe-bench
bench --version
```

## Phase 4: Bench with Frappe, ERPNext and HRMS

Ubuntu (15 to 30 minutes):
```bash
cd ~
bench init --frappe-branch version-16 --python "$(uv python find 3.14)" frappe-bench
cd frappe-bench
bench get-app --branch version-16 erpnext
bench get-app --branch version-16 hrms
```
Warnings `Cannot connect to redis_cache` during the asset build are expected; bench's own Redis is not running yet.

## Phase 5: Sites

Bench's own Redis (queue on port 11000, cache on 13000) must be running first: the erpnext and hrms install hooks enqueue jobs and fail with `Error 111 connecting to 127.0.0.1:11000` without it. Either keep `bench start` running in another terminal, or start only Redis:
```bash
cd ~/frappe-bench
redis-server config/redis_cache.conf --daemonize yes
redis-server config/redis_queue.conf --daemonize yes
```
Stop them after the sites are created, or `bench start` fails with `bind: Address already in use`:
```bash
redis-cli -p 13000 shutdown nosave
redis-cli -p 11000 shutdown nosave
```

Ubuntu, engineer only (prompts for the MariaDB root password and each site's Administrator password):
```bash
cd ~/frappe-bench
bench new-site dev.localhost --db-root-username root
bench --site dev.localhost install-app erpnext hrms
bench --site dev.localhost set-config developer_mode 1
bench new-site test.localhost --db-root-username root
bench --site test.localhost install-app erpnext hrms
bench --site test.localhost set-config allow_tests true
bench use dev.localhost
```
`~/setup-sites.sh` runs the same commands and asks for the database password once.

Check: `bench --site dev.localhost list-apps` lists `frappe`, `erpnext`, `hrms`.

## Phase 6: The nortix app

The app is proprietary (D8). `bench new-app` offers only open-source licences, so pick any and replace it afterwards: `license.txt` holds the proprietary notice and `nortix/hooks.py` sets `app_license = "Proprietary"`.

1. Ubuntu: create the app without its own Git repository.
   ```bash
   cd ~/frappe-bench
   bench new-app --no-git nortix
   ```
2. Ubuntu: let Git inside WSL use the Windows credential manager for GitHub.
   ```bash
   git config --global credential.helper "/mnt/c/Program\ Files/Git/mingw64/bin/git-credential-manager.exe"
   git config --global core.autocrlf input
   ```
3. Ubuntu: attach the app folder to the GitHub repository. Save the generated `README.md`, `.editorconfig`, `.pre-commit-config.yaml` and `license.txt` first; the checkout replaces them with the repository versions, which are then merged by hand.
   ```bash
   cd apps/nortix
   git init -b main
   git remote add origin https://github.com/DilshanMP/nortix.git
   git fetch origin
   git reset origin/main
   git checkout -- .
   ```
4. Ubuntu: install the app on both sites and the Git hooks.
   ```bash
   cd ~/frappe-bench
   bench --site dev.localhost install-app nortix
   bench --site test.localhost install-app nortix
   cd apps/nortix && pipx install pre-commit && pre-commit install
   ```

The app is edited inside Linux (`~/frappe-bench/apps/nortix`). A checkout on a Windows drive (`/mnt/e/...`) is too slow for bench and file watching.

## Phase 7: Daily use

| Task | Where | Command |
| --- | --- | --- |
| Start the server | Ubuntu, `~/frappe-bench` | `bench start`, then open `http://dev.localhost:8000` |
| Open the code | PowerShell | `code --remote wsl+Ubuntu-24.04 /home/pasindu/frappe-bench/apps/nortix` |
| Run all tests | Ubuntu | `bench --site test.localhost run-tests --app nortix` |
| Apply DocType or patch changes | Ubuntu | `bench --site dev.localhost migrate` |
| Lint | Ubuntu, `apps/nortix` | `pre-commit run --all-files` |

If `dev.localhost` does not resolve in the browser, add `127.0.0.1 dev.localhost` to `C:\Windows\System32\drivers\etc\hosts` (administrator).
