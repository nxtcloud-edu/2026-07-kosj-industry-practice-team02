# Data local rules

- `official`, `evaluation`, `mock`, `processed`, and `legacy` must remain separate.
- Do not edit raw official data in place; transform reproducibly.
- Every official record needs provider/source URL/verified date/author/reviewer/status.
- AI-generated or mock data can never become citizen evidence without human source verification and approval.
- Never include real PII.
- Update data lineage, versions, impacted tests, and implementation note for every data change.
- Citizen office cards may use official records only.
