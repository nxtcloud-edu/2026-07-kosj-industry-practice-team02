# ADR-0016 — Immutable filesystem official release and empty-local transactional seed

- Status: Accepted architecture / implementation pending written spec and plan approval
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

## Safety and rollback

Release preparation is create-once and uses a same-parent publish; dispatcher activation is a separate
recoverable atomic replacement. Seed runs in one transaction and fails before writes on a non-empty DB.
Exclusive table locks prevent capability-write races. Compensation fails before delete when operational
or altered data exists. Immutable release correction uses a separately approved successor design,
never destructive in-place rollback.
