---
name: ambiguity-audit
description: Audit a repository or feature request for missing, ambiguous, contradictory, or architecture-changing decisions before implementation. Use at project start, before large features, or when user requirements are fuzzy.
---

1. Read root and nearest AGENTS plus source-of-truth and decision logs.
2. Inspect actual repository state; do not rely only on documents.
3. Search product, architecture, data, privacy, auth, deployment, cost, failure, test, accessibility, migration, and handoff gaps.
4. Classify findings A Blocker, B High, C Defaultable, D Internal.
5. Ask only A/B questions, max 7 per batch, with options/tradeoffs/recommendation/default/impact.
6. Do not ask resolved questions.
7. Write/update discovery report, ambiguity register, decision log, and an implementation note.
8. Do not implement large code changes until blockers are resolved and plan is approved.
