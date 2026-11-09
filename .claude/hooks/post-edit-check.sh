#!/usr/bin/env bash
# Lints the edited file and reports problems back so they are fixed in the same step.
set -uo pipefail

input="$(cat)"
file="$(printf '%s' "$input" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))')"

[ -z "$file" ] && exit 0
[ -f "$file" ] || exit 0

case "$file" in
	*.py)
		if command -v ruff >/dev/null 2>&1; then
			out="$(ruff check --quiet "$file" 2>&1)" || { echo "$out" >&2; exit 2; }
		fi
		;;
	*.json)
		python3 -m json.tool "$file" >/dev/null 2>&1 || { echo "Invalid JSON: $file" >&2; exit 2; }
		;;
esac

case "$file" in
	*.py|*.js|*.vue|*.html)
		if grep -nEi "generated (by|with) (ai|claude|chatgpt)|as an ai (language )?model" "$file" >/dev/null 2>&1; then
			echo "Remove tool references from $file (docs/06-standards/coding-standards-python.md)" >&2
			exit 2
		fi
		;;
esac

exit 0
