# CHANGELOG

## [Unreleased]

### Added

- AI-001A standard-library fail-closed PII masking core with 13 closed categories, five unresolved
  reasons, immutable value-free findings, Unicode normalization/control rejection, deterministic
  overlap selection, conservative contextual ambiguity closure, and a frozen 74-case exact oracle;
  representative/service phones, repeated whitespace separators, Hangul explicit values, and
  fixed-token trailing-raw bypasses fail closed; irregular numeric/vehicle/email splitting, health
  modifiers, phone extensions, generated-token tail composition, and value-less inquiry controls are
  covered by direct regressions and positive value-evidence grammars; a 254-case category-gap suite
  plus independent actual/safe/insertion/Unicode/separator matrices found no raw fail-open or safe
  false positive at the final frozen source; this pure core has no route, DB, provider,
  official-data, or public API activation
- User-approved Q-PII-003=A public-number masking policy and AI-001A execution plan: citizen-provided “official” labels are untrusted, all phone-shaped input values are masked, and approved official contacts remain server-combined KB/office metadata cards
- User-approved AI-001 PII written specification and AI-001A TDD plan for an isolated standard-library core, frozen exact-output synthetic v1 evaluation set, Unicode/overlap/residual/bypass gates, and no route/DB/provider activation; its former A-032 gate is resolved by Q-PII-003=A/D-043
- User-approved AI-001 fail-closed PII masking core design and written specification: standard-library deterministic typed rules, value-free fixed tokens/findings, unsafe result with no text, metadata-only event allowance, and no route/DB/provider implementation yet
- Immutable filesystem official release `0.1.0-initial.1` with approved 19 KB·3 offices·10
  mappings, approval/artifact/semantic hashes, excluded KB 1 and rejected mappings 2, deterministic
  seed/compensation SQL, and a byte-identical local dispatcher while `[db.seed].enabled=false`
- DATA-SEED active-release-compatible no-Docker root stages for focused unit/static tests,
  `verify-release`, and `verify-local-seed`; Task 7A root and independent review passed
- DATA-SEED `.1` lineage with the Task 5 publication evidence, Task 6 actual attempts/fixes/blocker,
  cleanup boundary, immutable correction policy, and A-030/Q-SEED-002 successor decision gate
- WEB-HOME-001 static `/chat` preparation shell, navigable home CTA, explicit no-input/no-storage/request allowlist browser guard, 390/430/desktop accessibility checks, and actual Chrome UI 200% zoom verification
- Standalone exact-locked `tools/web-e2e` Playwright test project and a permanent production dependency/deploy gate that keeps Playwright out of the citizen Web runtime graph
- DATA-001 internal staging schemas, dependency-free fail-closed validator, canonical DRAFT KB 20·office 3·mapping 12, hash-bound `PENDING_PM_REVIEW` manifest, deterministic validation report, lineage, and PM review packet; all remain non-ACTIVE and outside citizen reads, seed, and readiness
- Codex repository guidance, first-run interview prompt, source-of-truth hierarchy
- ADR, implementation-note, handoff, ambiguity-audit workflows
- Draft API contracts and DB schema aligned with final scope
- Legacy project quarantine and current-repo audit
- Initial discovery report, interview answer ledger, and Interviewing execution plan
- ADR-0007 local/private admin security boundary
- ADR-0008 Supabase CLI versioned SQL migration boundary
- ADR-0009 HTTP 503 service-unavailable boundary
- ADR-0010 server-session-free signed client-carried chat context
- Dependency-free root pnpm workspace contract with exact Node 24.12.0, pnpm 11.13.0, Python 3.12.13, and uv 0.11.28 pins
- Standard-library repository scaffold contract tests for runtime, workspace, package-manager, credential, and ignored-path invariants
- FastAPI 0.1.0 scaffold with import-safe app factory, exact `/health`, pre-DB `/ready=503`, typed readiness probe, strict public models, tests, and a frozen uv lock
- Next.js 16.2.10 static `/` shell with truthful development limits, four approved service areas, semantic landmarks, mobile-first accessible styles, four render tests, and a frozen pnpm lock
- Service-scoped Web/API environment templates, metadata-only FastAPI request logging, Uvicorn unsafe-log hardening, and standard-library repository/browser artifact secret scanners
- Strict shared-contract validator with 17 synthetic fixtures, 27 fixture validations, and six OpenAPI structure/reference guards
- Deterministic OpenAPI TypeScript generation/check commands and strict Pydantic raw-JSON consumers for the same 17 contract fixtures
- PowerShell 5.1-compatible 24-stage local verification gate with exact runtime preflight, frozen/default and warm-offline modes, fail-fast exit preservation, scoped synthetic Web secret checks, and metadata-only diagnostics
- DB-001 executable-schema discovery report covering migration lineage, atomic approval, retention, ACTIVE-only access, provenance, permissions, rollback, and database test gaps
- ADR-0011 and a written DB-001 design for private schemas, capability functions, atomic approval, retention, and layered DB/backend enforcement
- User-approved DB-001 written specification and an execution-gated TDD plan covering pinned local tooling, five migrations/compensations, pgTAP, lazy FastAPI DB boundaries, concurrency, and rollback/replay
- D-026/D-027 refinements for fail-closed non-superuser role verification, separate failed-question reason confirmation, immutable event classification, candidate gating, and required approval comments
- DB-001 candidate-stage lineage: six immutable timestamp forward migrations and six disposable-local
  compensations for private schema, invariants, capability/RLS, candidate workflow,
  ACTIVE+OFFICIAL reads, and deferred validator posture. Promotion was blocked at that stage until the
  later patched-runtime and actual-loopback gates produced the verified `0.3.0-local` baseline below
- Six-file pgTAP 282 assertions, real backend integration 8/8, exact
  `006→005→004→003→002→001` compensation/absence/reset/replay gate, and local DB handoff/report
- Checksum-pinned Supabase CLI v2.109.1 source, Go 1.25.11 toolchain, 1,824-byte two-file
  loopback patch, reproducible runtime SHA-256, and patched-only DB runner with no stock/PATH fallback
- Verified disposable `0.3.0-local` baseline: exact single `127.0.0.1:54322`, fresh pgTAP 282,
  backend integration 8/8, six-stage compensation/absence/replay, final container 0/0, volume deletion 0

### Changed

- Completed the isolated AI-001A core and permanent standard-library/no-I/O architecture gate while
  leaving parent AI-001, citizen-visible unresolved-PII behavior, official readiness, DeepSeek
  adapter, and public deployment behind their existing independent blockers
- Resolved A-032 and moved AI-001A from Review to Ready while keeping parent AI-001, official seed/readiness, unresolved-PII consumer behavior, and public deployment blocked by their existing independent gates
- Clarified the source-of-truth privacy boundary: successful masking is necessary but not sufficient for storage or synthetic-provider use; unresolved PII forbids failed-question text/row and provider calls, while actual citizen DeepSeek transmission remains prohibited
- Materialized PM-LOCAL-001's exact 35-record DATA-001 review evidence at `2026-07-19T02:06:19+09:00`: KB approve 19/withhold 1, office approve 3, mapping approve 10/reject 2. Immutable content hashes remain unchanged. The `.1` filesystem release and dispatcher are now published/verified, but actual DB rows, ACTIVE reads, readiness and `official_data` promotion remain blocked.
- Pinned the approved development baseline to Node 24.x+pnpm and Python 3.12+uv; installation begins in Phase 1 after the user's 2026-07-15 approval
- Clarified local-first/zero-infrastructure-budget as the active target and managed hosting as separately approved future work
- Updated OpenAPI and logical DB drafts to 0.2.0: failed-question text expires after 30 days while metadata and candidate links remain
- Assigned official KB/office authoring to AI/Data·Backend and approval to PM, targeting 2026-07-20
- Pinned local/private synthetic evaluation to `deepseek-v4-flash`, thinking off, max 1024, concurrency 1, one retry, and 30 total outbound attempts per explicit process run
- Selected Supabase CLI versioned SQL migrations; CLI installation and migration execution remain deferred until DB-001
- Chose conservative recall-first name/address masking with a measured, human-approved relaxation gate
- Changed the public API draft to 1.0.0: 200 responses no longer allow SYSTEM_ERROR and unrecoverable service failure uses a stable 503 SERVICE_UNAVAILABLE envelope
- Chose local Git and manual validation gates for the current phase; remote repository and CI are deferred until the user asks to connect Git
- Replaced undefined `session_id` with a 15-minute signed opaque `context_token`, current-tab transcript memory, and no server session/transcript persistence; API draft is now 2.0.0
- Defaulted the disposable local demo to RPO 24h/RTO 60m, daily/pre-risk gitignored dumps, 30-day dump deletion, and restore-before-open retention purge
- Approved the final plan and initial production dependency list; began independent local Git and Phase 1 scaffold work while keeping public/real-user boundaries deferred
- Split Phase 1 into exact runtime, pre-DB health/readiness, Web shell, env/log boundary, contract/generated drift, and clean local verification review units
- Adjusted the approved ESLint development tool from the incompatible 10.7.0 candidate to exact 9.39.5 for the Next 16.2.10 bundled plugin peer range; production dependencies were unchanged
- Tightened the existing API 2.0.0-draft so SUCCESS requires at least one source and aligned nullable optional fallback office validation across OpenAPI and standalone JSON Schema
- Made public Pydantic boundary models reject scalar coercion and preserved optional OpenAPI fields with defaults in generated TypeScript
- Patched the public draft to API 2.0.1-draft: `/health` and ready-state `/ready` 200 bodies are required closed schemas, and FALLBACK extras are rejected consistently across OpenAPI, standalone JSON Schema, and Pydantic
- Scoped pnpm dependency verification/offline and six synthetic Web build environment values with exact restoration, while suppressing child output that could disclose paths or values
- Preserved the local `.pnpm-store/` cache while adding it to the tested transient-path ignore contract so it cannot be committed accidentally
- Updated the database environment record after verifying the local Docker engine, while keeping Supabase CLI installation and migration execution behind written DB design review
- Resolved Q-DB-002 as layered database-and-backend enforcement while keeping remote/public execution deferred
- Approved the DB-001 written specification for planning; migration, Docker, CLI download, and DB mutation remain deferred until the new plan is explicitly approved
- Approved the DB-001 execution plan and completed Tasks 0~5; applied migrations `00100`~`00300` remain immutable, workflow moves to `00400`, and citizen reads move to `00500`
- Completed DB-001 Tasks 0~9 and prepared Task 10 local baseline closeout without changing
  public API, official/mock seed, application version, or readiness; `00100~00500` remain immutable
  and `00600` is the validator-only posture correction
- Prepared the `repo_guidance=1.5.0`, `database_schema=0.3.0-local`,
  `test_suite=0.5.0-db-baseline`, and documentation `2.4.0` candidate closeout, then kept the
  committed manifest axes unchanged after the local port security blocker was reproduced
- Applied the approved Q-SEC-004 Docker Desktop `default-local-port-binding` policy and fully
  restarted the engine; an actual HostIP-omitted probe resolved to IPv4 `127.0.0.1` plus IPv6
  wildcard `::`, while an explicit `127.0.0.1` control resolved to one loopback binding. Both
  disposable probes were removed and no Supabase DB mutation was run
- Applied the approved Q-SEC-005 `local-only-port-binding` policy and restarted Docker Desktop;
  the HostIP-omitted probe still resolved to `127.0.0.1` plus IPv6 wildcard `::`, while the explicit
  `127.0.0.1` control remained single-loopback. Both probes were removed, container count returned to
  zero, and no Supabase DB mutation was run
- Completed Q-SEC-006/A-024 and Q-TOOL-001/A-025 locally with source manifest
  `c293e5ac32bae030eadf383d8d9511dc16eac834e51e996273ae8b7e39616657`, patch
  `109c096480e8185d761e9ce8fba10e93efc55190c42eab978f769a6993833f7d`, and runtime
  `751068e73834c5da58ac7c5287a1d66a82ad356f508637b0478d6531cdb3941c`; DB-001 is Done for
  disposable local/private use only
- Bounded DB child process trees in `73f300b`; focused descendant cleanup 1/1, full runner 50/50,
  patched tooling 24/24, independent review 0/0/0 and final-code DB revalidation PASS
- Recorded DATA-SEED Task 6 as Blocked rather than promoted: the authoritative PostgreSQL 17
  grantor-specific ADMIN/INHERIT/SET effective union conflicts with immutable `.1` seed/compensation
  exactly-one-row membership guards. The runner stopped before writes after two reviewed bounded
  fixes; no role/grant/migration/release byte changed, and cleanup ended at container 0/port listener 0
- Hardened DATA-SEED prepare rollback so any cleanup failure after owned-directory quarantine keeps
  the canonical release absent, leaves any residual only at a noncanonical path, and permits
  a safe retry. Added the exact partial-delete regression and a true post-staging-validation snapshot
  mutation guard; published `.1` bytes, dispatcher, DB, migration, API and official-data version stay
  unchanged

### Pending

- A-030/Q-SEED-002 human decision. Recommended/default A is a separately PM/technically approved
  immutable `0.1.0-initial.2` with the same 19/3/10 data and corrected effective-union guard; B is a
  new versioned DB migration that normalizes grantor-specific memberships. Neither option is
  implemented without an answer; DATA-SEED/READY/AI remain Blocked
- Full actual disposable PostgreSQL seed/rollback/concurrency/compensation/replay/citizen-read cycle;
  `official_data` remains `0.0.0-not-populated` until every gate passes
- Deployment accounts and URLs
- Official seed/readiness/chat/admin vertical slices
- Q-SEC-003/A-021 privileged-function search-path hardening before any public release;
  default B keeps remote/public deployment, public admin/API, and public backend DB credentials blocked
