# DB-001 Layered Database Enforcement Design

- Status: Written design pending user review
- Date: 2026-07-16 (KST)
- Approved approach: Q-DB-002=A on 2026-07-16
- Related: D-025, ADR-0003/0004/0007/0008/0011, TASK DB-001
- Discovery evidence: `docs/discovery/DB_001_DISCOVERY_REPORT.md`

## 1. Goal

Create the first executable, locally reproducible Supabase/PostgreSQL schema for the Sejong civil-service AI MVP. Privacy, approval, ACTIVE-only retrieval, provenance, retention, and audit rules must be enforced in both PostgreSQL and the FastAPI service.

This design converts the current logical draft into a migration-ready boundary. It does not yet install the CLI, pull images, start containers, write migrations, or seed data.

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
- A failed row can only reference a FALLBACK event with identical intent and fallback reason.
- SUCCESS and FOLLOWUP cannot have a fallback reason or failed row.
- OUT_OF_SCOPE records metadata only and rejects any masked text.
- INSUFFICIENT_GROUNDING creates a candidate-eligible row only when a safe masked question is supplied.
- PERSONAL_LOOKUP and LEGAL_JUDGMENT may create an ineligible row only when a safe masked question is supplied.
- A caller that supplies no safe masked question records the event only.
- A retained failure row starts with non-null text, exact `created_at + interval '30 days'` expiry, and null purge time. After expiry only text becomes NULL and purge time becomes non-null.

### 5.5 Candidate and audit state

- `failed_questions.status` and `kb_candidates.review_status` keep the existing enum but gain table-specific allowed-state checks.
- A candidate can only reference an eligible INSUFFICIENT_GROUNDING failure.
- Candidate source, department, verified date, generalized representative question, and answer fields must be non-empty before submission.
- `audit_logs` accepts an allowlisted action, target type, old/new status, changed field names, and optional review comment.
- Audit INSERT is available only inside approved state-transition functions. UPDATE and DELETE are unavailable to the backend role.
- Audit rows do not contain question or answer snapshots.

## 6. Callable database interfaces

| Interface | Responsibility | Atomic result |
|---|---|---|
| `app_api.list_active_kb` | Return ACTIVE+OFFICIAL KB records and question examples for an allowed intent | Read-only closed row set |
| `app_api.list_offices` | Return OFFICIAL office cards for region and intent | Read-only closed row set |
| `app_api.record_interaction` | Insert metadata event and, only when permitted, a masked failure row | One event and zero/one failure |
| `app_api.create_kb_candidate` | Create DRAFTED candidate from eligible failure | One candidate and audit row |
| `app_api.submit_kb_candidate` | Validate completeness and move to PENDING_APPROVAL | Candidate transition and audit row |
| `app_api.approve_kb_candidate` | Lock candidate, enforce different APPROVER, create ACTIVE KB/question example, link candidate | Exactly one KB, link, transition, audit row |
| `app_api.reject_kb_candidate` | Lock candidate, require different APPROVER and comment, move to REJECTED | Transition and audit row |
| `app_api.purge_expired_failed_question_text` | Purge expired text at DB current time | Count and IDs only, idempotent |

The backend never sends client-provided role headers directly to these interfaces. It resolves the local/private demo actor first. DB functions then repeat structural checks such as `actor_role = APPROVER` and `actor_id <> created_by`.

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

### 7.3 Candidate approval

1. Function locks the candidate with `FOR UPDATE`.
2. It verifies PENDING_APPROVAL, APPROVER role, different actor, complete official source data, and allowed provenance.
3. It creates one ACTIVE KB and one generalized initial question example.
4. It updates the candidate with APPROVED, reviewer, timestamp, and activated KB ID.
5. It appends an audit row in the same transaction.
6. Duplicate/concurrent approval sees the terminal state and creates nothing else.

### 7.4 Retention and restore

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
- `supabase/migrations/*_indexes_and_read_interfaces.sql`
- `database/rollbacks/`: reverse-order compensation SQL for the same four stages
- `supabase/tests/database/`: pgTAP/catalog tests with synthetic data only
- `scripts/verify_database.ps1`: explicit Docker-required reset/test/rollback/replay gate

Migration filenames use Supabase timestamp order. Timestamp lineage is not a semantic version. When the executable baseline and tests pass, `database_schema` moves from `0.2.0-draft` to `0.3.0-local`.

The bootstrap script rechecks official release metadata during implementation. It fails closed if the exact asset digest cannot be verified. It does not use global install, floating latest, or npm lifecycle scripts. CLI/status output that may contain local credentials is suppressed or reduced to non-secret health state.

## 10. Rollback and recovery

- Applied migration files are immutable; corrections use new forward migrations.
- Initial compensation is allowed only against the disposable local DB.
- Rollback runs in reverse: read interfaces/indexes → capabilities/functions/roles → invariants/triggers → private tables/types.
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

### State and concurrency

- self approval, OPERATOR approval, incomplete candidate, wrong state, and cross-origin activation fail
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

This design-only commit changes documentation from `2.3.11` to `2.3.12`. Application, API, shared contract, DB, data, prompt, and test versions stay unchanged.

The later approved implementation is expected to change:

- `repo_guidance`: `1.4.0` → `1.5.0` for pinned DB tooling and verification
- `database_schema`: `0.2.0-draft` → `0.3.0-local`
- `test_suite`: `0.4.2-readiness-contract` → `0.5.0-db-baseline`
- documentation: next compatible version

It does not change the OpenAPI wire contract or add a production dependency.

## 13. Acceptance and next gate

The design is accepted for planning when the user confirms this written specification. After that confirmation, `superpowers:writing-plans` creates a task-by-task TDD plan. Migration SQL, CLI download, image pull, container start, and DB mutation begin only during the separately approved execution of that plan.
