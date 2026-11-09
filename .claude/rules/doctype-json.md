---
paths:
  - "nortix/**/doctype/**/*.json"
---

# DocType JSON rules

- Follow docs/03-design/doctype-conventions.md.
- Transactional DocTypes have a mandatory `company` Link field and track changes on.
- Sensitive fields use a higher permlevel.
- Edit DocType JSON through `bench` and the DocType form where possible; keep field order logical.
- Never delete a field that holds data without a patch that migrates it.
