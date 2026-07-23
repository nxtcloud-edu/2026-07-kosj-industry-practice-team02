# DATA-SEED-002 successor immutable release correction design

- Status: Approved / In Progress — Q-SEED-002=A selected; Q-MVP-001=A/D-058 approved immediate execution on 2026-07-22
- Date: 2026-07-20
- Owner: Backend·Data·Security
- Related: D-044, A-030, ADR-0015, ADR-0016, ADR-0017, DATA-SEED-001 actual report

## 1. Goal

Create a new immutable `0.1.0-initial.2` release from the exact PM-approved DATA-001 payload, correct
only the PostgreSQL 17 membership guard to accept the authoritative effective option union, and rerun
the entire disposable-local database verification cycle before promoting the official-data version.

Success means fresh evidence for 19 ACTIVE/OFFICIAL KB records, 3 OFFICIAL offices, 10 approved
mappings, 0 excluded/mock/operational rows, exact citizen reads, compensation/replay and semantic
hash equality. It does not mean public readiness or `/ready=200`.

## 2. Fixed inputs and identities

- Source draft: `data/staging/data-001/0.1.0-draft.1/`
- Source approval reviewer/time: `PM-LOCAL-001`, `2026-07-19T02:06:19+09:00`
- Source approval SHA-256: `466d7af44cc36a9ee1ea1eed3d90f0e6fa1627fc57c03de5377c6f9f9fef5b6a`
- Successor version/id: `0.1.0-initial.2`, `sejong-official-0.1.0-initial.2`
- Governance decision time: `2026-07-20T20:41:24+09:00` / `2026-07-20T11:41:24Z`
- Generator: `data-seed-release-v2`
- Expected projection: KB 19, office 3, mapping 10, withheld KB 1, rejected mapping 2, mock 0
- Expected seed semantic SHA-256: `c838a4aa5eb1675d93fbaebd99b63d823490eb172c64cc356c5f72114cc1e4eb`
- Exclusions: `KB-WASTE-03`, `OFFICE-AREUM:LOCAL_TAX_GENERAL`,
  `OFFICE-DODAM:BULKY_WASTE`

The governance time records the human choice of the successor correction, not filesystem clock time.
The existing PM approval remains the content approval because no official fact, record disposition or
projection changes. Independent technical review approves the generated correction mechanics and
hashes before publication; it cannot change source facts.

## 3. Non-goals

- No edit, delete or regeneration-in-place of `0.1.0-initial.1`.
- No DB migration, role/grant normalization or function change. The existing pgTAP membership
  assertion is aligned from its narrower `INHERIT+SET` same-row predicate to the migration's already
  approved three-independent-`EXISTS` meaning; assertion count and runtime objects do not change.
- No public API, `PRIVACY_UNRESOLVED`, chat, UI, LLM or provider work.
- No automatic Supabase seed; `[db.seed].enabled=false` remains exact.
- No `/ready=200`; READY-001 remains separate even after a successful import.
- No remote/public DB, public admin/API or public backend credential.
- No WASTE-03 activation and no mock rows.
- No new production or development dependency.

## 4. Historical immutability boundary

The following `.1` release files are a frozen historical failure artifact:

| File | Bytes | SHA-256 |
|---|---:|---|
| `approval_manifest.json` | 13074 | `466d7af44cc36a9ee1ea1eed3d90f0e6fa1627fc57c03de5377c6f9f9fef5b6a` |
| `compensation.sql` | 41710 | `6fde4e35e185453ca1bba42af4440fc0f935257efbc1701f84cc349ecedc2368` |
| `kb_records.json` | 37208 | `831a0c01c9cdb08130febb122ebcad7d7b4fd9e7d846764d0d49d3e3c02402ec` |
| `office_service_mappings.json` | 4057 | `361ba3f4024abdfc7f1d0b4c8107d3aff708e377ac309bc18beda7613bfccebd` |
| `offices.json` | 2263 | `d83d48ff56cb945ddbb262e26c7d876dbc4b34af9b038048884057ab54e10b4e` |
| `release_manifest.json` | 1605 | `e8863a633d28125ad2c0f0323d60467236d08618e767833fc7c09444f1a6e4a2` |
| `seed.sql` | 75891 | `42d67828bb23c0eb0fa17ae2daa7d457fd71806b7cc796a54643dd975597783d` |

The four `data/schemas/data-seed/v1/` files are also frozen:

| File | Bytes | SHA-256 |
|---|---:|---|
| `kb-records.schema.json` | 2564 | `97bd21438bbfc1a60c13de13106b9378961ddef20839c3227d88bcf75eae9527` |
| `office-service-mappings.schema.json` | 1460 | `82853a80f7147cd9948580bec97a9bf5c765cf1956520680f205ebfd5d4d2bfa` |
| `offices.schema.json` | 1885 | `7a251ba5fff8e5990788db010faf946d221b845089c2192ae5c0a122e632f280` |
| `release-manifest.schema.json` | 2765 | `0b6cc2deb20cf25ea9b02059cc6400826304c0452ee957e3757a41679e91423e` |

## 5. Release profile and schema boundary

The release library supports two explicit profiles:

- historical `.1`: v1 schema, `data-seed-release-v1`, legacy single-row SQL regeneration used only
  for byte verification;
- active successor `.2`: v2 schema, `data-seed-release-v2`, effective-union SQL.

An unknown version fails before reading or writing a release. CLI `prepare` can create only `.2`;
`.1` can be verified but never prepared or activated as a new artifact. The v2 data-record schemas
preserve the strict v1 structure with exact `.2` release version. The v2 manifest changes
`schema_version` to `2`, fixes the `.2` ID/version and v2 generator, and adds this required strict
correction object:

```json
{
  "predecessor_release_version": "0.1.0-initial.1",
  "predecessor_manifest_sha256": "e8863a633d28125ad2c0f0323d60467236d08618e767833fc7c09444f1a6e4a2",
  "decision_id": "D-044",
  "reason": "POSTGRES17_EFFECTIVE_MEMBERSHIP_OPTION_UNION"
}
```

All other field allowlists, counts and `additionalProperties=false` remain unchanged.

## 6. Correct membership contract

Both successor `seed.sql` and `compensation.sql` must execute the same principal guard before role
switch or table mutation:

```sql
IF NOT EXISTS (
  SELECT 1
  FROM pg_catalog.pg_auth_members AS memberships
  JOIN pg_catalog.pg_roles AS granted_role
    ON granted_role.oid = memberships.roleid
  JOIN pg_catalog.pg_roles AS member_role
    ON member_role.oid = memberships.member
  WHERE granted_role.rolname = 'sejong_schema_owner'
    AND member_role.rolname = 'postgres'
    AND memberships.admin_option
)
OR NOT EXISTS (
  SELECT 1
  FROM pg_catalog.pg_auth_members AS memberships
  JOIN pg_catalog.pg_roles AS granted_role
    ON granted_role.oid = memberships.roleid
  JOIN pg_catalog.pg_roles AS member_role
    ON member_role.oid = memberships.member
  WHERE granted_role.rolname = 'sejong_schema_owner'
    AND member_role.rolname = 'postgres'
    AND memberships.inherit_option
)
OR NOT EXISTS (
  SELECT 1
  FROM pg_catalog.pg_auth_members AS memberships
  JOIN pg_catalog.pg_roles AS granted_role
    ON granted_role.oid = memberships.roleid
  JOIN pg_catalog.pg_roles AS member_role
    ON member_role.oid = memberships.member
  WHERE granted_role.rolname = 'sejong_schema_owner'
    AND member_role.rolname = 'postgres'
    AND memberships.set_option
)
THEN
  RAISE EXCEPTION USING
    ERRCODE = 'P0001', MESSAGE = 'DATA_SEED_MEMBERSHIP_INVALID';
END IF;
```

The three options may be true on one row or different grantor-specific rows. Every row must still
refer to the exact granted/member role OIDs. An empty set or one missing option fails. No grantor name,
row count, transitive role or `pg_has_role` shortcut is accepted.

The migration already implements this exact three-`EXISTS` contract. The current pgTAP happens to pass
the observed two-row catalog but combines `inherit_option` and `set_option` on one row, so the
successor implementation must split that one assertion into three independent checks. This is a test
alignment to the migration authority, not a DB behavior or schema change.

## 7. SQL and projection invariants

All DATA-SEED-001 safety constraints remain:

- exact session/current user/database and successful `SET LOCAL ROLE sejong_schema_owner`;
- advisory lock `20260719001`, lock timeout `5s`;
- exact eight-table ACCESS EXCLUSIVE lock order;
- empty preflight before seed, operational/reference and bidirectional exact projection guard before
  compensation;
- explicit columns, generated expected-row CTEs, both-direction `EXCEPT ALL`, exclusions and mock 0;
- one transaction, second seed rejected, altered/reference/non-empty compensation rejected;
- DSN and child output remain content-free and secret-free.

The source approval, projected records and semantic hash must be identical between `.1` and `.2`.
Only release metadata embedded in JSON and the membership guard SQL may differ.

## 8. Publication and dispatcher state machine

```text
.1 immutable + dispatcher=.1 + official_data=not-populated
  → generate .2 in owned same-parent prepare directory
  → strict regeneration/schema/hash/immutability checks
  → independent technical review approves exact candidate
  → create-once publish .2
  → atomic dispatcher .1→.2, rollback to captured .1 on failure
  → offline root gate
  → full disposable actual DB cycle
  → actual PASS: official_data=.2, /ready remains 503
  → actual FAIL: official_data unchanged, .2 retained immutable, report Blocked
```

Publication never overwrites `.1` or an existing `.2`. Dispatcher activation accepts exact `.1` as
the only upgrade predecessor and exact `.2` as idempotent current state. Data-free, unknown, modified,
reparse or concurrently replaced dispatcher entries fail closed.

## 9. Actual local database acceptance

The supported command is exactly:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_data_seed.ps1 -ReleaseVersion 0.1.0-initial.2
```

It must begin from absent repo-owned runtime and run the existing patched-only DB baseline first. The
cycle must then emit allowlisted PASS evidence for identity, forced mid-import rollback, concurrency
A/B, seed-cycle including second seed and blocked compensation, compensation, six-migration replay,
second pgTAP/integration baseline and final 19/3/10 citizen projection. Failure at any stage preserves
`official_data=0.0.0-not-populated` and records unreached stages as not run, never PASS.

After either outcome, the runner stops only the exact repo-owned container, verifies listener 0 and
preserves owned volumes/network. It does not delete Docker volumes, remote data or unrelated paths.

## 10. Testing strategy

TDD starts with four focused RED groups:

1. `.1` release/schema fingerprint and no-prepare/no-overwrite invariants;
2. split-row effective union positive plus each missing-option negative, with seed/compensation parity;
3. migration/pgTAP/successor three-`EXISTS` structural parity without changing pgTAP count;
4. `.2` version/schema/manifest/dispatcher predecessor and exact CLI wiring.

GREEN then covers deterministic generation across roots, strict byte regeneration, atomic publish and
dispatcher race/rollback tests, secret-safe verifier output, active-release-aware root tests and the
full actual DB cycle. Final review must separately check specification compliance and code/data quality.

## 11. Security, privacy, accessibility, cost

- Security: no role/grant/migration relaxation; exact identity/locks and patched loopback runner remain.
- Privacy: no citizen question, PII, transcript, context token, provider payload, DSN or approval
  comment enters application data or logs.
- Data quality: no official fact changes; source approval hash, record set and semantic hash stay exact.
- Accessibility: no UI change.
- Performance/cost: local dataset only, external API 0, dependency 0, cloud cost 0원.

## 12. Human gates and completion boundary

Q-MVP-001=A and the user's `즉시 실행` instruction on 2026-07-22 approved this written specification
and its execution plan. That approval authorizes the local filesystem/dispatcher/disposable-DB work
and the one existing pgTAP membership-predicate alignment in the plan, but not public deployment,
`00700`, PII contract work, WASTE-03 or `/ready=200`.

If the actual cycle passes, documentation may promote only `official_data` to `.2`; application, API,
DB schema and web versions remain unchanged. If it fails, the task closes as Blocked with `.2` retained
and a new human decision only if the next correction would change this approved architecture.
