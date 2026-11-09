---
name: commit-message
description: "Propose commit messages and a pull request description for staged changes in the project's Conventional Commits format. Use when changes are ready to commit."
disable-model-invocation: true
---

# Commit message

1. Read `git diff --staged`.
2. Split into logical commits if the staged changes mix concerns; say how.
3. For each commit propose:
   - `<type>(<scope>): <imperative summary, max 72 chars>`
   - body: why the change was needed and which rule it implements
   - `Refs: <requirement IDs>`
4. Use the engineer's voice. No trailers other than `Refs:`.
5. For the pull request, fill `.github/pull_request_template.md`.

The owner reviews and runs `git commit`.
