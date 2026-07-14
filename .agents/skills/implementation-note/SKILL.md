---
name: implementation-note
description: Create a reproducible 6W1H implementation or decision note for every completed user request, including versions, tests, data/security impact, rollback, human decisions, and handoff details.
---

1. Run `python scripts/new_implementation_note.py --title "..." --task-id ... --type ...`.
2. Fill every applicable section of the generated note.
3. Record exact commands and actual results; do not claim unrun tests.
4. Record version before/after from `versions/manifest.json`.
5. Separate human-required knowledge from AI-internal details.
6. Link plan/ADR/RFP/task and changed files.
7. Add rollback/reproduction/handoff.
8. Ensure INDEX is updated before final response.
