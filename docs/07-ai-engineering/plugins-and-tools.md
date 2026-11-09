---
title: "Tools, Plugins and Integrations"
status: "Draft"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Tools, Plugins and Integrations

Project skills, agents, rules and hooks in `.claude/` are the main tooling and are versioned with the code. Third-party plugins and MCP servers are optional; review their source, permissions, commands, network access and credentials before installing (master guide, section 9).

## Claude Code setup
| Item | How |
| --- | --- |
| Project instructions | `CLAUDE.md` (loaded every session) |
| Path rules | `.claude/rules/*.md` (load when matching files are touched) |
| Skills | `.claude/skills/*/SKILL.md` (run as `/name` or picked automatically) |
| Review agents | `.claude/agents/*.md` |
| Permissions and hooks | `.claude/settings.json`; personal overrides in `.claude/settings.local.json` (git-ignored) |
| Commit attribution | `"attribution": {"commit": "", "pr": ""}` in settings |

## Plugins
Open the plugin manager with `/plugin` to browse marketplaces. Add a marketplace with `/plugin marketplace add <owner>/<repo>` and install with `/plugin install <plugin>@<marketplace>`. Candidates to evaluate (check current names and contents before installing):
- A general engineering-practice plugin (for example `obra/superpowers`: planning, test-driven development, debugging workflows).
- A GitHub integration for issues and pull requests.

Record every installed plugin, its version and why it was approved in this file.

## Developer tools
| Tool | Purpose |
| --- | --- |
| VS Code + Python, ESLint, Prettier, EditorConfig, Mermaid preview extensions | Editing |
| WSL2 Ubuntu or Docker Desktop | Running bench on Windows |
| pre-commit, ruff, gitleaks | Local checks |
| GitHub Actions | CI |
| A password manager | Network and service secrets (never in the ERP or Git) |
