# DATA-SEED-001 — `0.1.0-initial.1` lineage

- Status: **filesystem release published and verified / actual database import Blocked**
- Release ID: `sejong-official-0.1.0-initial.1`
- Governance release time: `2026-07-19T09:20:31+09:00`
  (`2026-07-19T00:20:31Z` in the manifest)
- Approval reviewer/time: `PM-LOCAL-001` / `2026-07-19T02:06:19+09:00`
- Projection: ACTIVE/OFFICIAL KB 19, OFFICIAL office 3, approved mapping 10, mock 0
- Runtime boundary: `supabase/seed.sql` is byte-active, but `[db.seed].enabled=false`; no
  automatic reset import is enabled.
- Product boundary: no release row reached PostgreSQL, no citizen-visible ACTIVE data or READY/AI
  promotion occurred, and `official_data` remains `0.0.0-not-populated`.

## 1. Approval and source lineage

The canonical authoring input is `data/staging/data-001/0.1.0-draft.1/`. PM approval selected 19 of
20 KB records, all 3 offices, and 10 of 12 mappings. The approval manifest copied into the release is
byte-identical to the approved staging manifest.

| Artifact | Records | SHA-256 |
|---|---:|---|
| staging `kb_records.json` | 20 | `38d0c801b3dab3962b5cd01fe15a43a60121963b53e8b1f7ac65304d07267365` |
| staging `offices.json` | 3 | `fe942ce476c7d78f5b17deb10fd3b53e5b673f3ae36cf67a042823ccd51a7af0` |
| staging `office_service_mappings.json` | 12 | `a0fb8f3c423c0b0b199ed27cdb35cf40efa9011e7ae3d6736f420fc175ee4e1b` |
| approval manifest (staging and release) | 35 decisions | `466d7af44cc36a9ee1ea1eed3d90f0e6fa1627fc57c03de5377c6f9f9fef5b6a` |

## 2. Immutable release artifacts

Task 5 published exactly seven create-once files under
`data/official/releases/0.1.0-initial.1/` and activated the dispatcher. Independent review found
Critical/Important/Minor `0/0/0`. The release directory and dispatcher must never be edited or
deleted in place.

| Release artifact | Bytes | Records | SHA-256 |
|---|---:|---:|---|
| `approval_manifest.json` | 13,074 | 35 decisions | `466d7af44cc36a9ee1ea1eed3d90f0e6fa1627fc57c03de5377c6f9f9fef5b6a` |
| `compensation.sql` | 41,710 | n/a | `6fde4e35e185453ca1bba42af4440fc0f935257efbc1701f84cc349ecedc2368` |
| `kb_records.json` | 37,208 | 19 | `831a0c01c9cdb08130febb122ebcad7d7b4fd9e7d846764d0d49d3e3c02402ec` |
| `office_service_mappings.json` | 4,057 | 10 | `361ba3f4024abdfc7f1d0b4c8107d3aff708e377ac309bc18beda7613bfccebd` |
| `offices.json` | 2,263 | 3 | `d83d48ff56cb945ddbb262e26c7d876dbc4b34af9b038048884057ab54e10b4e` |
| `release_manifest.json` | 1,605 | n/a | `e8863a633d28125ad2c0f0323d60467236d08618e767833fc7c09444f1a6e4a2` |
| `seed.sql` | 75,891 | n/a | `42d67828bb23c0eb0fa17ae2daa7d457fd71806b7cc796a54643dd975597783d` |

- Dispatcher `supabase/seed.sql`: SHA-256
  `42d67828bb23c0eb0fa17ae2daa7d457fd71806b7cc796a54643dd975597783d`, byte-identical to release
  `seed.sql`.
- Filesystem semantic projection SHA-256:
  `c838a4aa5eb1675d93fbaebd99b63d823490eb172c64cc356c5f72114cc1e4eb`.
- Excluded KB 1: `KB-WASTE-03` (`WITHHOLD_FOR_REGRESSION`).
- Excluded mappings 2: `OFFICE-AREUM:LOCAL_TAX_GENERAL`, `OFFICE-DODAM:BULKY_WASTE`
  (`REJECT`).

Task 7A made release verification part of the no-Docker root gate. It passed focused Task 1–4 tests
113/113, full `scripts/tests` 286 with one environment-dependent skip, direct release/dispatcher
verification, and the full root gate. This is filesystem/test evidence only, not database-import
evidence.

## 3. Actual disposable PostgreSQL attempt

Task 6 ran the approved command three times during `2026-07-20 00:21:14~00:51:40 KST`:

| Attempt | Reached evidence | Stop reason |
|---:|---|---|
| 1 | composite DB baseline PASS | PowerShell 5.1 exact-manifest empty-diff handling bug |
| 2 | retry-state preflight only | the reset-created repo runtime was correctly rejected until pinned-CLI cleanup |
| 3 | baseline, patched runtime and status PASS | session identity first exposed invalid qualified `COALESCE`, then the membership-contract conflict |

Two bounded implementation defects were fixed and independently approved:

- `faa34d49`: preserve an empty `Compare-Object` result as an array under PowerShell strict mode.
- `afe47ccc`: use the PostgreSQL `COALESCE` special form without invalid schema qualification.

The remaining blocker is architectural, not a transient test failure. PostgreSQL 17 stores role
membership options on grantor-specific rows. The existing migration and pgTAP authority intentionally
accepts the effective ADMIN/INHERIT/SET union across those rows. Actual safe metadata had INHERIT+SET
on the `postgres` grant and ADMIN on the `supabase_admin` grant. Immutable `.1` seed and compensation
instead require exactly one membership row with all three options. Both SQL files therefore reject the
authoritative safe representation before any seed write.

The following acceptance evidence was **not reached** and must not be treated as PASS: PostgreSQL
19/3/10 counts, forced rollback, concurrency A/B, second-seed rejection, compensation, replay, final
database semantic hash, citizen 19, exclusions 0, and operational rows 0.

## 4. Cleanup and current status

Final Task 6 cleanup used only the pinned project-local CLI after ownership inspection. At
`2026-07-20T00:51:40+09:00`, repo-owned container count was 0 and port 54322 listener count was 0.
Two repo-owned volumes and the single loopback network were preserved. No Docker/DB command was run
by Task 7A or this documentation synchronization.

Consequently:

- `official_data=0.0.0-not-populated` remains correct.
- no official/mock persistent application row or citizen-visible ACTIVE KB has been proven imported.
- `/ready=503`, READY-001 and AI-001 remain blocked.
- A-021/Q-SEC-003 independently continues to block public/remote use.

## 5. Correction policy and open decision

> **2026-07-20 D-044 technical correction:** references below to a combined “migration/pgTAP
> effective-union authority” are historical shorthand. The migration has three independent `EXISTS`
> predicates; the then-current pgTAP passed the observed two-row state but coupled `INHERIT+SET` on
> one row. ADR-0017 keeps the migration semantics authoritative and plans a one-predicate pgTAP
> alignment. This addendum does not alter `.1` bytes or the historical failed-run evidence.

Released `.1` bytes are immutable: never edit, overwrite, rename away, or delete them. Correction
requires a separately approved version and a complete actual DB cycle from an absent repo-owned
runtime.

`A-030/Q-SEED-002` is open and no option is implemented:

- **A (recommended/default):** keep migration/pgTAP effective-union authority and publish a separately
  PM/technically approved immutable `0.1.0-initial.2` with the same approved 19/3/10 data, a corrected
  membership guard, a new manifest, and full actual-cycle evidence. This limits change to versioned
  release artifacts but requires regeneration, approval, review, and complete rerun.
- **B:** add a new versioned DB migration that normalizes grantor-specific memberships to one row.
  This changes platform-specific global privilege/schema state and requires a broader security,
  rollback, replay, and deployment review.

If no human answer is supplied, A remains the recommendation but neither A nor B is executed;
DATA-SEED-001, READY-001, and AI-001 stay Blocked. This open decision is not D-040 and must not be
represented as a confirmed human choice.

## 6. Reproduction and evidence

Read-only filesystem verification:

```powershell
apps/api/.venv/Scripts/python.exe -B scripts/promote_data_seed.py verify-release --release-dir data/official/releases/0.1.0-initial.1
apps/api/.venv/Scripts/python.exe -B scripts/promote_data_seed.py verify-local-seed --release-dir data/official/releases/0.1.0-initial.1
```

The actual DB command below may be rerun only after Q-SEED-002 is resolved and the chosen successor
design is separately approved and materialized:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_data_seed.ps1 -ReleaseVersion <approved-successor-version>
```

Human approval owns the correction architecture, new official release/manifest, DB privilege change,
and any READY/AI/public promotion. Documentation wording, link maintenance, hash transcription, and
non-mutating validation inside the already approved contract are AI-internal work.
