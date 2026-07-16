# DB-001 Layered Database Enforcement Design

- Status: Approved; execution in progress, Tasks 0~5 complete
- Date: 2026-07-16 (KST)
- Approved approach: Q-DB-002=A, Q-SEC-002=A, Q-WF-001=A on 2026-07-16
- Related: D-025/D-026/D-027, ADR-0003/0004/0007/0008/0011, TASK DB-001
- Discovery evidence: `docs/discovery/DB_001_DISCOVERY_REPORT.md`

## 1. Goal

Create the first executable, locally reproducible Supabase/PostgreSQL schema for the Sejong civil-service AI MVP. Privacy, approval, ACTIVE-only retrieval, provenance, retention, and audit rules must be enforced in both PostgreSQL and the FastAPI service.

This design converts the logical draft into an executable boundary. Tasks 0~5 have installed the pinned local tooling and implemented migrations `00100~00300`; no official/mock seed exists and `/ready=503` remains correct. The remaining workflow/read/repository work follows this refined approved design.

## 2. Scope

### Included in DB-001

- project-local, checksum-pinned Supabase CLI bootstrap design
- local Supabase config and ordered SQL migration lineage
- the existing eight domain tables, hardened with explicit constraints and provenance
- private base-table schema and restricted callable interface schema
- atomic candidate approval and rejection
- ACTIVE+OFFICIAL citizen read boundary
- metadata-only interaction/failure storage and 30-day masked-text purge
- append-only audit metadata
- explicit compensation SQL and local reset/rollback/replay tests
- DB-specific verification command that does not silently run in the normal no-Docker gate

### Excluded

- official KB/office seed data and PM approval
- chat classification, masking implementation, retrieval ranking, DeepSeek calls
- `/chat` and `/admin` endpoints or frontend behavior
- remote Supabase project link, `db push`, public deployment, SSO/RBAC
- production scheduling, cloud backup, destructive real-data migration
- full schema normalization beyond the minimum needed for current invariants

## 3. Non-negotiable requirements

- Raw questions, answers, transcripts, context tokens, IP addresses, device IDs, and secrets are not schema fields.
- `OUT_OF_SCOPE` text is never stored. FOLLOWUP never creates a failed-question row.
- A safely masked support-scope failure may create a failure row. If no safe masked text is retained, only the metadata event is stored.
- Stored `masked_question` is set to NULL after exactly 30 days; the row, metadata, and candidate foreign keys remain.
- Only `INSUFFICIENT_GROUNDING` is candidate eligible. PERSONAL_LOOKUP and LEGAL_JUDGMENT remain ineligible even when masked text is retained.
- The author cannot approve their own candidate.
- Only ACTIVE, OFFICIAL knowledge and office records are visible through citizen read interfaces.
- Source title, URL, and verified date come from approved records, not an LLM.
- No ACTIVE official seed means `/ready=503` remains correct.
- Remote execution, destructive data operations, and new production dependencies require separate approval.

## 4. Architecture

### 4.1 Schemas

`app_private` owns enums, base tables, triggers, internal helper functions, and private testable retention helpers. It is not added to the Supabase exposed-schema list.

`app_api` owns the narrow server-callable views and functions. Its objects return only fields required by a backend use case. Browser roles never receive access.

The default `public` schema contains no Sejong business tables or citizen/admin RPC functions.

### 4.2 Roles and privileges

| Role | Login | Direct base-table access | Allowed use |
|---|---:|---:|---|
| `sejong_schema_owner` | No | Owner only | Own tables and SECURITY DEFINER functions |
| `sejong_backend` | No | None | Execute approved `app_api` functions and read approved views |
| local generated login | Yes, local only | None | Member of `sejong_backend`; credential lives only in ignored env |
| `PUBLIC`, `anon`, `authenticated` | platform-defined | None | No schema usage, table DML, or function execution |

Base tables have RLS enabled and forced. The only permissive policy is for the NOLOGIN schema owner used inside reviewed SECURITY DEFINER functions. All such functions:

- are owned by `sejong_schema_owner`;
- set a fixed `search_path` containing only `pg_catalog` and explicitly referenced application schemas;
- schema-qualify every application object;
- revoke execute from `PUBLIC` before granting it to `sejong_backend`;
- never accept raw question text or a secret;
- emit stable SQLSTATE values without echoing user content.

The generated local login is credential provisioning, not schema lineage. A bootstrap script creates or rotates it after reset using a random password and writes only the final connection URL to an ignored local env file. Tracked migration and documentation contain no password.

The migration executor remains the PostgreSQL 17 non-superuser runner. Role creation specifies all safe attributes. On replay it reasserts only `NOLOGIN`, `NOCREATEDB`, and `NOCREATEROLE`, which that runner may apply, then verifies `NOSUPERUSER`, `NOREPLICATION`, `NOBYPASSRLS`, role settings, and effective memberships in catalogs. Any unsafe pre-existing role fails closed. No privileged auto-downgrade or privileged bootstrap is added.

## 5. Logical model hardening

The eight current tables remain. Their physical location changes from implicit `public` to `app_private`.

### 5.1 Provenance

Add a `data_origin` enum with `OFFICIAL` and `MOCK`.

- `kb_documents.data_origin`: required, no default
- `offices.data_origin`: required, no default
- `kb_candidates.data_origin`: required, no default
- `offices.is_official`: generated from `data_origin = 'OFFICIAL'`, not caller-controlled
- question examples and office mappings inherit their parent's origin
- failure/event test classification continues to use `interaction_events.is_test`
- an approval function preserves candidate origin in the activated KB
- citizen reads always require `data_origin = 'OFFICIAL'`

There is no implicit official default. Test fixtures explicitly use MOCK.

### 5.2 KB and question examples

- JSON procedure/document fields must be arrays of non-empty strings.
- Public IDs and required text fields are trimmed and non-empty.
- ACTIVE requires approver, approval time, official provenance, source title/URL, verified date, and at least one question example.
- RETIRED may retain its historical approval fields but is never returned by citizen reads.
- The approval function inserts the candidate's generalized `representative_question` as the first question example.
- DB UUID is internal; API/contract `id` maps to `public_id`.

### 5.3 Office records

- Region remains exactly 아름동, 도담동, or 조치원읍 for the MVP.
- `is_official` cannot be independently supplied.
- Citizen office reads require OFFICIAL provenance and a matching region/intent mapping.

### 5.4 Interaction events and failed questions

- `request_id` is the idempotency key. A duplicate with identical metadata returns the existing interaction ID without a second event; conflicting metadata for the same ID fails with `P1010`.
- `used_source_ids` is a JSON array of unique non-empty public IDs.
- `source_count` equals the array length. SUCCESS source IDs must resolve to ACTIVE+OFFICIAL KB at write time.
- `selected_region`, when present, is one of the three supported regions.
- On initial insertion, a `NEW` failed row can only reference a FALLBACK event and must match that event's intent and fallback reason.
- The event intent/reason is the immutable initial automated classification.
- On OPERATOR confirmation, only `failed_questions.fallback_reason`, `candidate_eligible`, and status may change. The parent event is not rewritten, preserving request-id replay semantics.
- SUCCESS and FOLLOWUP cannot have a fallback reason or failed row.
- OUT_OF_SCOPE records metadata only and rejects any masked text.
- INSUFFICIENT_GROUNDING creates a candidate-eligible row only when a safe masked question is supplied.
- PERSONAL_LOOKUP and LEGAL_JUDGMENT may create an ineligible row only when a safe masked question is supplied.
- A caller that supplies no safe masked question records the event only.
- A retained failure row starts with non-null text, exact `created_at + interval '30 days'` expiry, and null purge time. After expiry only text becomes NULL and purge time becomes non-null.

### 5.5 Candidate and audit state

- `failed_questions.status` and `kb_candidates.review_status` keep the existing enum but gain table-specific allowed-state checks.
- A candidate can only reference a `REASON_CONFIRMED`, eligible INSUFFICIENT_GROUNDING failure.
- Candidate source, department, verified date, generalized representative question, and answer fields must be non-empty before submission.
- `audit_logs` accepts allowlisted candidate actions plus `FAILED_QUESTION_REASON_CONFIRMED`; target types include `KB_CANDIDATE` and `FAILED_QUESTION`. Reason confirmation records `NEW → REASON_CONFIRMED` and only actual changed field names from `status`, `fallback_reason`, and `candidate_eligible`.
- Audit INSERT is available only inside approved state-transition functions. UPDATE and DELETE are unavailable to the backend role.
- Audit rows do not contain question or answer snapshots.

## 6. Callable database interfaces

| Interface | Responsibility | Atomic result |
|---|---|---|
| `app_api.list_active_kb` | Return ACTIVE+OFFICIAL KB records and question examples for an allowed intent | Read-only closed row set |
| `app_api.list_offices` | Return OFFICIAL office cards for region and intent | Read-only closed row set |
| `app_api.record_interaction` | Insert metadata event and, only when permitted, a masked failure row | One event and zero/one failure |
| `app_api.confirm_failed_question_reason` | OPERATOR confirms/corrects one NEW failure reason while preserving the event classification | Failure transition, re-derived eligibility, one metadata audit row |
| `app_api.create_kb_candidate` | Create DRAFTED candidate from eligible failure | One candidate and audit row |
| `app_api.submit_kb_candidate` | Validate completeness and move to PENDING_APPROVAL | Candidate transition and audit row |
| `app_api.approve_kb_candidate` | Lock candidate, enforce different APPROVER and required review comment, create ACTIVE KB/question example, link candidate | Exactly one KB, link, transition, audit row |
| `app_api.reject_kb_candidate` | Lock candidate, require different APPROVER and comment, move to REJECTED | Transition and audit row |
| `app_api.purge_expired_failed_question_text` | Purge expired text at DB current time | Count and IDs only, idempotent |

The backend never sends client-provided role headers directly to these interfaces. It resolves the local/private demo actor first. DB functions then repeat structural checks such as `actor_role = APPROVER` and `actor_id <> created_by`.

The refined exact internal signatures are:

```sql
app_api.confirm_failed_question_reason(uuid, text, text, text) RETURNS void
app_api.approve_kb_candidate(uuid, text, text, text) RETURNS text
```

The four confirmation arguments are failure ID, actor ID, actor role, and confirmed fallback reason. The fourth approval argument is the required trimmed review comment. Existing OpenAPI already exposes the reason PATCH and requires `review_comment` for both review decisions, so this is not a public wire change.

Internal test code can call a private cutoff-parameterized purge helper inside a transaction. The backend-callable purge interface accepts no time argument, preventing a caller from advancing the cutoff.

## 7. Transaction flows

### 7.1 Citizen read

1. Backend determines intent after masking/classification in a later slice.
2. Backend calls the restricted KB/office read interface.
3. DB filters ACTIVE+OFFICIAL records before returning them.
4. Backend attaches server-owned source metadata. LLM output cannot override it.

### 7.2 Event and failure write

1. Backend builds metadata and an optional already-masked text value.
2. `record_interaction` validates status/reason/source relationships.
3. It inserts one idempotent event.
4. It inserts a failure only for an allowed FALLBACK with retained safe masked text.
5. Any failure rolls back both inserts; exception data contains no question text.

### 7.3 Failure reason confirmation

1. Function requires OPERATOR, locks the failed row, and requires `NEW`.
2. It validates one stored failure reason, leaves the parent event untouched, and updates only the failure reason, re-derived eligibility, and status `REASON_CONFIRMED`.
3. It inserts one `FAILED_QUESTION_REASON_CONFIRMED`/`FAILED_QUESTION` metadata audit row with actual changed field names.
4. Concurrent confirmation serializes on the failed row; one succeeds and later attempts return `P1003` without another audit row.
5. Candidate creation locks the same failure and requires confirmed INSUFFICIENT_GROUNDING eligibility.

### 7.4 Candidate approval

1. Function locks the candidate with `FOR UPDATE`.
2. It verifies PENDING_APPROVAL, APPROVER role, different actor, complete official source data, and allowed provenance.
3. It creates one ACTIVE KB and one generalized initial question example.
4. It updates the candidate with APPROVED, reviewer, timestamp, and activated KB ID.
5. It stores the required trimmed review comment on the candidate and appends it as metadata in the audit row in the same transaction.
6. Duplicate/concurrent approval sees the terminal state and creates nothing else.

### 7.5 Retention and restore

1. The public maintenance wrapper uses DB current time.
2. It updates only expired, non-null `masked_question` fields and sets `text_purged_at`.
3. Repeated execution changes zero additional rows.
4. Backup restore procedure invokes purge before readiness can open service.

## 8. Stable errors

Business functions use stable private SQLSTATE codes that the later repository layer maps without parsing human messages:

| SQLSTATE | Meaning |
|---|---|
| `P1001` | forbidden actor role |
| `P1002` | self approval |
| `P1003` | invalid candidate state |
| `P1004` | incomplete candidate/source data |
| `P1005` | disallowed origin or ACTIVE transition |
| `P1010` | invalid interaction/failure combination |

Standard constraint codes remain for unique/FK/check violations. Error messages and logs may include stable IDs and constraint names but never question, answer, provider body, secret, or full record snapshots.

No public HTTP error contract changes in DB-001. A later API slice maps these internal errors to the already approved 403/409/422 behavior.

## 9. Migration and tooling layout

The implementation plan will use these responsibilities:

- `scripts/supabase-cli.version.json`: exact stable release, official asset URL, SHA-256
- `scripts/bootstrap_supabase.ps1`: verify/download the project-local binary into ignored `.tools/supabase/<version>/`
- `supabase/config.toml`: local project config with only required services enabled
- `supabase/migrations/*_private_schema.sql`
- `supabase/migrations/*_invariants_and_lineage.sql`
- `supabase/migrations/*_capabilities_and_functions.sql`
- `supabase/migrations/*_candidate_workflow.sql`
- `supabase/migrations/*_indexes_and_read_interfaces.sql`
- `database/rollbacks/`: reverse-order compensation SQL for the same five stages
- `supabase/tests/database/`: pgTAP/catalog tests with synthetic data only
- `scripts/verify_database.ps1`: explicit Docker-required reset/test/rollback/replay gate

Migration filenames use Supabase timestamp order. Timestamp lineage is not a semantic version. When the executable baseline and tests pass, `database_schema` moves from `0.2.0-draft` to `0.3.0-local`.

Applied and committed migrations `20260716000100` through `20260716000300` are immutable. Candidate workflow/audit refinement is `20260716000400_candidate_workflow.sql`; citizen indexes/read interfaces shift to `20260716000500_indexes_and_read_interfaces.sql`.

The bootstrap script rechecks official release metadata during implementation. It fails closed if the exact asset digest cannot be verified. It does not use global install, floating latest, or npm lifecycle scripts. CLI/status output that may contain local credentials is suppressed or reduced to non-secret health state.

## 10. Rollback and recovery

- Applied migration files are immutable; corrections use new forward migrations.
- Initial compensation is allowed only against the disposable local DB.
- Rollback runs in reverse: `00500` read interfaces/indexes → `00400` candidate workflow/audit → `00300` capabilities/functions/roles → `00200` invariants/triggers → `00100` private tables/types.
- The verification gate confirms objects and privileges are removed, then performs a fresh reset/replay and reruns tests.
- No wrapper executes remote push, volume prune, or destructive real-data commands.
- Future non-reproducible data requires a gitignored dump before destructive change. Restore must run retention purge before readiness.

## 11. Verification matrix

### Schema and replay

- two consecutive empty resets produce the same catalog
- migration order and semantic manifest are consistent
- compensation rollback removes only DB-001 objects, then replay succeeds

### Permissions

- `PUBLIC`, `anon`, `authenticated`, and `sejong_backend` direct base-table CRUD all fail
- backend capability role can execute only allowlisted `app_api` interfaces
- SECURITY DEFINER functions have fixed search paths and no PUBLIC execute
- role replay reasserts runner-permitted attributes and fails closed on unsafe elevated attributes, memberships, or settings

### State and concurrency

- self approval, OPERATOR approval, incomplete candidate, wrong state, and cross-origin activation fail
- only OPERATOR can confirm one NEW failure; concurrent duplicate confirmation yields one transition/audit and one `P1003`
- confirmation preserves event reason, updates only failure reason/eligibility/status, and candidate creation requires confirmed IG eligibility
- approval and rejection both require a non-empty review comment
- two concurrent approvals produce one ACTIVE KB, one activated link, and one approval audit row
- rejected, retired, pending, draft, and mock KB never appear in citizen reads

### Privacy and retention

- schema contains no raw-question/answer/transcript/token/IP/device fields
- OUT_OF_SCOPE text and FOLLOWUP failure rows remain zero
- candidate eligibility is true only for INSUFFICIENT_GROUNDING
- expiry just before/equal/after the boundary is correct
- repeated purge is idempotent and preserves event/candidate links
- audit and error output contain no text snapshots

### Data quality

- JSON arrays contain strings only
- source count and source IDs agree
- SUCCESS sources resolve to ACTIVE+OFFICIAL KB
- ACTIVE requires one question example and complete official metadata
- MOCK fixtures cannot enter citizen reads

### Readiness

- DB ready with no approved seed still returns `/ready=503`
- DB failure or missing migration remains 503
- READY-001, not DB-001, owns the eventual 200 transition

## 12. Version impact

The Q-SEC-002/Q-WF-001 refinement changes documentation from `2.3.13` to `2.3.14`. Application, API, shared contract, DB, data, prompt, and test versions stay unchanged.

The later approved implementation is expected to change:

- `repo_guidance`: `1.4.0` → `1.5.0` for pinned DB tooling and verification
- `database_schema`: `0.2.0-draft` → `0.3.0-local`
- `test_suite`: `0.4.2-readiness-contract` → `0.5.0-db-baseline`
- documentation: next compatible version

It does not change the OpenAPI wire contract or add a production dependency.

## 13. Acceptance and next gate

The user approved this written specification and execution plan on 2026-07-16. Tasks 0~5 are complete. Q-SEC-002=A accepts the existing Task 5 fail-closed role model, and Q-WF-001=A unblocks Task 6. Task 6 must begin with RED tests for the new `00400` workflow migration; no additional human blocker remains.
