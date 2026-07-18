# CHANGELOG

## [Unreleased]

### Added

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

- Marked DATA-001 AI scope complete / Review (PM pending); `official_data` remains `0.0.0-not-populated`, while test-suite and documentation evidence advance to `0.7.0-data-trust-boundary` and `2.6.0`. Remediation 3 cleared the historical `TEST-ROOT` early-stop concern with a direct 171-test discovery (511.715s) and a fresh full verification pass; PM approval/release/seed remain out of scope.
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

### Pending

- Official KB and office data
- Deployment accounts and URLs
- Official seed/readiness/chat/admin vertical slices
- Q-SEC-003/A-021 privileged-function search-path hardening before any public release;
  default B keeps remote/public deployment, public admin/API, and public backend DB credentials blocked
