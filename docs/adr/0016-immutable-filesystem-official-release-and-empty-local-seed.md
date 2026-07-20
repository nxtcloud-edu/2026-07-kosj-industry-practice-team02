# ADR-0016 — Immutable filesystem official release and empty-local transactional seed

- Status: Accepted historical `.1`; actual import blocked, correction direction superseded by ADR-0017
- Date: 2026-07-19
- Related: Q-SEED-001, D-036, A-028, ADR-0015, DATA-SEED-001

## Context

ADR-0015 defines hash-bound PM approval in staging and assigns promotion/import to DATA-SEED-001.
The existing DB already enforces ACTIVE/OFFICIAL KB and separate approver metadata. The project is a
zero-budget local/private demo, while a new DB release-ledger migration would expand schema, privilege,
rollback and public-security review without being necessary for the first reproducible dataset.

## Decision

1. Use `data/official/releases/<version>/` as the immutable official release authority.
2. The initial version is `0.1.0-initial.1` with the PM-approved 19 KB, 3 offices and 10 mappings only.
3. Generate deterministic projected JSON, release manifest, transactional seed and guarded
   compensation from the approved hash-bound staging artifact using two recoverable phases: immutable
   release preparation, then independent local dispatcher activation.
4. Keep DB schema/API and `[db.seed].enabled=false` unchanged. `supabase/seed.sql` is a verified
   byte-identical generated copy only after explicit local activation.
5. Import is initial-release-only and allowed only through the repository verifier into a
   migration-only empty disposable local DB. It requires the patched-gate local DSN identity
   `postgres@127.0.0.1:54322/postgres`, asserts session/database/catalog membership before and after
   switching to `sejong_schema_owner`, and locks all eight participating tables before preflight and
   writes. SQL does not claim parent-process provenance.
6. Compensation is allowed only under the same role/table locks, before any operational/reference row
   exists and only when bidirectional exact column comparisons prove every seed-owned field and
   question example matches the release. The repository verifier separately records the precisely
   serialized semantic SHA-256 evidence; no new PostgreSQL digest dependency is introduced.
7. Released bytes are never edited/deleted. Corrections require a new draft, PM approval and release.
8. `/ready`, retrieval and citizen behavior remain unchanged until their later vertical slices.

## Alternatives considered

### DB release ledger and privileged import function

Rejected for this phase. It improves in-DB release queries but requires a new migration, function
security review, replay/rollback and coordination with Q-SEC-003.

### Release-only, import deferred

Not selected as the target because it leaves READY/AI critical-path work blocked. It remains the
fail-safe outcome if real DB import verification cannot pass.

### Direct edit of `supabase/seed.sql`

Rejected because it lacks a self-contained immutable release, approval-hash lineage and correction
history.

## Consequences

- Positive: reproducible and auditable official data without a new production dependency, migration
  or public contract.
- Positive: official data provenance that the current normalized DB tables do not retain stays in the
  release artifact.
- Negative: DB cannot query release history directly; operators use release manifest/lineage files.
- Negative: empty-only import/compensation is intentionally unsuitable for a live database. A future
  operational deployment needs a separately approved data-transition architecture.

## 2026-07-20 actual outcome addendum

- Task 5 published and independently verified immutable filesystem release `0.1.0-initial.1` with
  exactly 19 KB, 3 offices and 10 mappings. `supabase/seed.sql` is byte-identical to its `seed.sql`;
  `[db.seed].enabled=false` remains unchanged.
- Task 7A added and passed the no-Docker release/dispatcher root gate. This proves release bytes and
  filesystem semantics, not a PostgreSQL import.
- Task 6 attempted the supported actual runner three times. Two bounded runner/query defects were
  fixed and independently approved, but the final attempt stopped before seed writes.
- The authoritative migration accepts the effective PostgreSQL 17 ADMIN/INHERIT/SET option union
  across grantor-specific membership rows. The then-current pgTAP proves the observed two-row shape
  but combines INHERIT and SET on one row. Immutable `.1` seed and
  compensation instead require exactly one row with all three options. Actual safe metadata used two
  grantor-specific rows, so the `.1` guard rejected it before mutation.
- Consequently there is no actual 19/3/10 PostgreSQL count, compensation/replay, final DB semantic
  hash, citizen-read, READY or AI promotion evidence. `official_data=0.0.0-not-populated` and
  `/ready=503` remain authoritative. Cleanup ended with repo-owned container 0 and port 54322
  listener 0.
- Released `.1` bytes remain immutable and must not be edited or deleted. Q-SEED-002=A/D-044 later
  selected ADR-0017: keep migration union authority, align the narrower pgTAP predicate, and create immutable
  `0.1.0-initial.2` with the same PM-approved 19/3/10 data, corrected guard, new manifest and full
  rerun. ADR-0017의 written specification/plan은 Review이며 후속 plan 승인 전 구현하지 않는다.

## Safety and rollback

Release preparation is create-once and uses a same-parent publish; dispatcher activation is a separate
recoverable atomic replacement. Seed runs in one transaction and fails before writes on a non-empty DB.
Exclusive table locks prevent capability-write races. Compensation fails before delete when operational
or altered data exists. Immutable release correction uses a separately approved successor design,
never destructive in-place rollback. The actual `.1` failure produced no application rows, so no
compensation was run; runtime cleanup stopped only the exact repo-owned container and preserved the
owned volumes/network.
