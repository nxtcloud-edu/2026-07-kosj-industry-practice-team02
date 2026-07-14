# API app local rules

- Follow root `AGENTS.md`, privacy policy, OpenAPI, and DB invariants.
- Never log request bodies or raw questions.
- PII redaction happens before provider calls.
- Domain services do not import a concrete LLM SDK; use provider adapter.
- SUCCESS requires ACTIVE KB sources; server attaches source metadata.
- OUT_OF_SCOPE text is not persisted; FOLLOWUP is not a failure.
- Approval is transactional and self-approval is blocked in backend, not only UI.
- Use typed models/enums and explicit error codes.
- Public contract or migration changes require approval, ADR, tests, versions, and notes.
- Add unit, contract, integration, and privacy tests for changed behavior.
