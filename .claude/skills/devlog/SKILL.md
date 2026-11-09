---
name: devlog
description: "Draft a dated engineering journal entry from the day's real work: decisions, trade-offs, problems and fixes, with links to commits, ADRs and requirements. Use at the end of a work session."
disable-model-invocation: true
---

# Devlog entry

1. Read today's commits (`git log --since=midnight`), changed docs and ADRs.
2. Ask the owner three questions: What did you decide today and why? What surprised you? What will you do next?
3. Draft `docs/devlog/YYYY-MM-DD-<topic>.md` using the template in docs/07-ai-engineering/devlog-guide.md, in the owner's words from the answers.
4. Include links to commits, ADRs and requirement IDs. No personal or company-confidential data.
