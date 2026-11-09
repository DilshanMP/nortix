#!/usr/bin/env bash
# Blocks shell commands that reach production, print secrets or bypass review.
set -euo pipefail

input="$(cat)"
cmd="$(printf '%s' "$input" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("command",""))')"

block() {
	echo "Blocked by project policy: $1" >&2
	exit 2
}

# Set NORTIX_PROD_HOSTS to the real production host and site names, separated by |
prod_hosts="${NORTIX_PROD_HOSTS:-\\bprod\\b|production}"

if printf '%s' "$cmd" | grep -Eqi "(ssh|scp|rsync).*(${prod_hosts})"; then
	block "no direct access to production hosts"
fi
if printf '%s' "$cmd" | grep -Eqi -- "--site[= ]+[^ ]*(${prod_hosts})"; then
	block "no bench commands against production sites"
fi
if printf '%s' "$cmd" | grep -Eqi "(cat|less|more|head|tail|grep).*(site_config\.json|\.env)"; then
	block "secrets files must not be printed"
fi
if printf '%s' "$cmd" | grep -Eqi "git (commit|push).*--no-verify"; then
	block "hooks and checks must not be skipped"
fi
if printf '%s' "$cmd" | grep -Eqi "Co-Authored-By|Generated with"; then
	block "commit messages follow docs/06-standards/git-workflow.md"
fi

exit 0
