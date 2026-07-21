# DATA-SEED-002 Successor Release Correction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish and locally verify immutable official release `0.1.0-initial.2` with the PostgreSQL 17 effective membership-option union guard while preserving every `.1` byte.

**Architecture:** Add explicit historical `.1` and successor `.2` release profiles. Regenerate `.1` only in memory for immutable verification, prepare/activate only `.2`, and parameterize the shared SQL serializer so `.1` retains its legacy guard while `.2` uses three independent effective-option checks. Run the existing patched-loopback disposable DB cycle end to end before promoting only the official-data version.

**Tech Stack:** Python 3.12.13 stdlib + existing `jsonschema`/`psycopg`, PowerShell 5.1, PostgreSQL 17/Supabase CLI 2.109.1 project-local patched runtime, `unittest`, JSON Schema draft 2020-12.

## Global Constraints

- User selected Q-SEED-002=A at governance time `2026-07-20T20:41:24+09:00`; Q-MVP-001=A/D-058 and immediate execution approved this plan on 2026-07-22.
- Successor is exactly `0.1.0-initial.2`, release ID `sejong-official-0.1.0-initial.2`, generator `data-seed-release-v2`, UTC release time `2026-07-20T11:41:24Z`.
- Source approval remains exact `PM-LOCAL-001`, `2026-07-19T02:06:19+09:00`, approval SHA-256 `466d7af44cc36a9ee1ea1eed3d90f0e6fa1627fc57c03de5377c6f9f9fef5b6a`.
- Projection remains exact 19 KB, 3 offices, 10 mappings, semantic SHA-256 `c838a4aa5eb1675d93fbaebd99b63d823490eb172c64cc356c5f72114cc1e4eb`; excluded/mock rows remain 0.
- Never edit/delete/overwrite `data/official/releases/0.1.0-initial.1/**` or `data/schemas/data-seed/v1/**`.
- Do not modify `supabase/migrations/**`, `database/**`, `contracts/**` or role/grant state. The only
  permitted DB-test edit is the existing membership predicate in
  `supabase/tests/database/003_capabilities_test.sql`, aligning it to the migration's already-approved
  three-independent-`EXISTS` meaning without changing test count or runtime objects.
- Keep `supabase/config.toml` `[db.seed].enabled=false`; `/ready` remains HTTP 503 and public/remote execution remains forbidden.
- No citizen question, PII, transcript, context token, provider payload, DSN, secret or approval comment in application data or command output.
- No new dependency, external API call, cloud resource or cost.
- Every code task follows RED → minimal GREEN → focused verification → diff review → commit.
- The exact generated `.2` candidate requires independent technical review with Critical/Important 0 before create-once publication.

---

## Status and approval boundary

- Plan ID: `DATA-SEED-002-PLAN`
- Status: **Approved / In Progress — Q-MVP-001=A/D-058**
- Written specification candidate (Review): `docs/superpowers/specs/2026-07-20-data-seed-002-successor-release-correction-design.md`
- Architecture decision: D-044 / ADR-0017
- Execution was authorized by the user's Q-MVP-001=A and `즉시 실행` instruction at `2026-07-22T02:10:11+09:00`.
- That approval covers local filesystem release, `.1→.2` dispatcher replacement and disposable local
  reset/seed/compensation/replay. It does not cover Q-PII-002 consumer changes, `00700`, public
  deployment, WASTE-03, remote DB, volume deletion or `/ready=200`.

## File responsibility map

| File | Responsibility |
|---|---|
| `scripts/data_seed_release.py` | version profiles, deterministic bundle generation and strict release verification |
| `scripts/data_seed_sql.py` | legacy and effective-union principal guards plus shared deterministic SQL |
| `scripts/promote_data_seed.py` | `.2`-only prepare/activation and dual-version verification |
| `scripts/verify_data_seed_db.py` | secret-free `.2` actual DB evidence and effective-union identity probe |
| `scripts/test_data_seed_concurrency.py` | `.2`-bound two-connection ordering probes |
| `scripts/verify_data_seed.ps1` | supported `.2` full disposable-local orchestration |
| `scripts/verify.ps1` | offline verification of both releases and active `.2` dispatcher |
| `data/schemas/data-seed/v2/*.schema.json` | strict `.2` JSON/release manifest contracts |
| `data/official/releases/0.1.0-initial.2/**` | create-once generated successor artifact; never hand-edited |
| `supabase/seed.sql` | byte-identical active local dispatcher for `.2`; auto-seed remains disabled |
| `docs/data-lineage/DATA-SEED-002-0.1.0-initial.2.md` | approval, predecessor, artifact hash and DB evidence lineage |
| `docs/test-reports/DATA-SEED-002-LOCAL-VERIFICATION.md` | actual reached/unreached stage report |

### Task 1: Freeze `.1` and introduce dual release profiles

**Files:**
- Modify: `scripts/data_seed_release.py`
- Modify: `scripts/tests/test_data_seed_release.py`
- Test: `data/official/releases/0.1.0-initial.1/**`
- Test: `data/schemas/data-seed/v1/**`

**Interfaces:**
- Produces: `ReleaseProfile`, `INITIAL_RELEASE_PROFILE`, `SUCCESSOR_RELEASE_PROFILE`,
  `release_profile(version: str) -> ReleaseProfile`, `RELEASE_VERSION = "0.1.0-initial.2"`.
- Preserves: in-memory regeneration of `.1` with its v1 schema/generator/timestamp and exact seven bytes.

- [ ] **Step 1: Write frozen-byte and profile RED tests**

Add exact filename/length/SHA dictionaries and tests equivalent to:

```python
INITIAL_RELEASE_FILES = {
    "approval_manifest.json": (13074, "466d7af44cc36a9ee1ea1eed3d90f0e6fa1627fc57c03de5377c6f9f9fef5b6a"),
    "compensation.sql": (41710, "6fde4e35e185453ca1bba42af4440fc0f935257efbc1701f84cc349ecedc2368"),
    "kb_records.json": (37208, "831a0c01c9cdb08130febb122ebcad7d7b4fd9e7d846764d0d49d3e3c02402ec"),
    "office_service_mappings.json": (4057, "361ba3f4024abdfc7f1d0b4c8107d3aff708e377ac309bc18beda7613bfccebd"),
    "offices.json": (2263, "d83d48ff56cb945ddbb262e26c7d876dbc4b34af9b038048884057ab54e10b4e"),
    "release_manifest.json": (1605, "e8863a633d28125ad2c0f0323d60467236d08618e767833fc7c09444f1a6e4a2"),
    "seed.sql": (75891, "42d67828bb23c0eb0fa17ae2daa7d457fd71806b7cc796a54643dd975597783d"),
}

def test_initial_release_and_v1_schema_bytes_are_frozen(self) -> None:
    for name, (length, digest) in INITIAL_RELEASE_FILES.items():
        payload = (self.root / "data/official/releases/0.1.0-initial.1" / name).read_bytes()
        self.assertEqual(length, len(payload), name)
        self.assertEqual(digest, hashlib.sha256(payload).hexdigest(), name)

def test_profiles_are_closed_and_successor_preserves_projection(self) -> None:
    self.assertEqual("legacy-single-row", release_profile("0.1.0-initial.1").membership_guard)
    self.assertEqual("effective-option-union", release_profile("0.1.0-initial.2").membership_guard)
    with self.assertRaisesRegex(ValueError, "RELEASE_VERSION_INVALID"):
        release_profile("0.1.0-initial.3")
```

Assert the exact four v1 filename/hash pairs from the written spec and assert the `.1` bundle regenerated
with its profile equals the committed seven files byte for byte.

- [ ] **Step 2: Run focused tests and confirm RED**

Run:

```powershell
.\apps\api\.venv\Scripts\python.exe -B -m unittest -v scripts.tests.test_data_seed_release
```

Expected: existing tests remain green except new imports/profile assertions fail because
`ReleaseProfile` and `.2` do not exist. No tracked file outside the test changes.

- [ ] **Step 3: Implement the minimal closed profile model**

Add this shape in `scripts/data_seed_release.py` and route bundle/verification constants through the
selected profile:

```python
@dataclass(frozen=True)
class ReleaseProfile:
    version: str
    release_id: str
    released_at: str
    released_at_utc: str
    canonical_token: str
    schema_token: str
    generator_id: str
    manifest_schema_version: int
    membership_guard: str
    predecessor_version: str | None = None
    predecessor_manifest_sha256: str | None = None
    decision_id: str | None = None
    correction_reason: str | None = None

INITIAL_RELEASE_PROFILE = ReleaseProfile(
    version="0.1.0-initial.1",
    release_id="sejong-official-0.1.0-initial.1",
    released_at="2026-07-19T09:20:31+09:00",
    released_at_utc="2026-07-19T00:20:31Z",
    canonical_token="data/official/releases/0.1.0-initial.1",
    schema_token="data/schemas/data-seed/v1",
    generator_id="data-seed-release-v1",
    manifest_schema_version=1,
    membership_guard="legacy-single-row",
)
SUCCESSOR_RELEASE_PROFILE = ReleaseProfile(
    version="0.1.0-initial.2",
    release_id="sejong-official-0.1.0-initial.2",
    released_at="2026-07-20T20:41:24+09:00",
    released_at_utc="2026-07-20T11:41:24Z",
    canonical_token="data/official/releases/0.1.0-initial.2",
    schema_token="data/schemas/data-seed/v2",
    generator_id="data-seed-release-v2",
    manifest_schema_version=2,
    membership_guard="effective-option-union",
    predecessor_version="0.1.0-initial.1",
    predecessor_manifest_sha256="e8863a633d28125ad2c0f0323d60467236d08618e767833fc7c09444f1a6e4a2",
    decision_id="D-044",
    correction_reason="POSTGRES17_EFFECTIVE_MEMBERSHIP_OPTION_UNION",
)
RELEASE_PROFILES = {
    profile.version: profile
    for profile in (INITIAL_RELEASE_PROFILE, SUCCESSOR_RELEASE_PROFILE)
}
RELEASE_VERSION = SUCCESSOR_RELEASE_PROFILE.version

def release_profile(version: str) -> ReleaseProfile:
    try:
        return RELEASE_PROFILES[version]
    except KeyError:
        raise ValueError("RELEASE_VERSION_INVALID") from None
```

`build_release_bundle` must accept both known versions, use the selected profile for paths/schema/
metadata, and include a `correction` object only for the successor. `verify_release_directory` derives
the profile from an exact canonical path and never from manifest-controlled input.

- [ ] **Step 4: Run tests and review `.1` diff**

Run the focused test again. Expected: all tests PASS and:

```powershell
git diff --exit-code -- data/official/releases/0.1.0-initial.1 data/schemas/data-seed/v1
```

Expected: exit 0, no output.

- [ ] **Step 5: Commit Task 1**

```powershell
git add scripts/data_seed_release.py scripts/tests/test_data_seed_release.py
git commit -m "refactor(data): add immutable seed release profiles"
```

### Task 2: Correct the successor SQL and verifier identity semantics

**Files:**
- Modify: `scripts/data_seed_sql.py`
- Modify: `scripts/verify_data_seed_db.py`
- Modify: `scripts/tests/test_data_seed_release.py`
- Modify: `scripts/tests/test_verify_data_seed_db.py`
- Modify: `scripts/tests/test_supabase_tooling.py`
- Modify: `supabase/tests/database/003_capabilities_test.sql` (one membership assertion predicate only)

**Interfaces:**
- Consumes: `ReleaseProfile.membership_guard`.
- Produces: `render_seed_sql(projection, *, membership_guard: str) -> bytes` and matching compensation.
- Preserves: `.1` renderer bytes under `legacy-single-row`.

- [ ] **Step 1: Replace the stale test with profile-specific RED coverage**

Keep a legacy assertion for `.1`; add successor assertions that extract the principal block from both
seed and compensation and require three option-specific `EXISTS`, no `count(*)`, no `bool_and`, no
`<> 1`, and the existing stable error. Add pure truth-table cases:

```python
cases = (
    ((True, True, True), True),
    ((True, True, False), False),
    ((True, False, True), False),
    ((False, True, True), False),
    ((False, False, False), False),
)
```

In DB verifier tests, make a split-row aggregate result
`("postgres", "postgres", "postgres", True, True, True)` pass and any false option fail.
Add a structural test proving the migration, successor SQL and the one existing pgTAP membership
assertion each use three independent option checks. The RED evidence must expose the current pgTAP
coupling of `inherit_option` and `set_option` on one row.

- [ ] **Step 2: Run both test modules and confirm RED**

```powershell
.\apps\api\.venv\Scripts\python.exe -B -m unittest -v scripts.tests.test_data_seed_release scripts.tests.test_verify_data_seed_db scripts.tests.test_supabase_tooling
```

Expected: new successor guard, new six-column verifier identity assertions and pgTAP-alignment
assertion fail; existing safety tests remain green.

- [ ] **Step 3: Parameterize the SQL guard**

Implement `_transaction_prefix(membership_guard: str)` with the existing block unchanged for
`legacy-single-row` and the exact three-`EXISTS` block from the specification for
`effective-option-union`. Unknown modes raise `ValueError("MEMBERSHIP_GUARD_INVALID")` before SQL is
returned. Pass the profile guard into both render functions so seed and compensation cannot diverge.

Update `_assert_session_identity()` to select:

```sql
SELECT
  session_user,
  current_user,
  current_database(),
  COALESCE(pg_catalog.bool_or(memberships.admin_option), false),
  COALESCE(pg_catalog.bool_or(memberships.inherit_option), false),
  COALESCE(pg_catalog.bool_or(memberships.set_option), false)
FROM pg_catalog.pg_auth_members AS memberships
JOIN pg_catalog.pg_roles AS granted_role ON granted_role.oid = memberships.roleid
JOIN pg_catalog.pg_roles AS member_role ON member_role.oid = memberships.member
WHERE granted_role.rolname = 'sejong_schema_owner'
  AND member_role.rolname = 'postgres'
GROUP BY session_user, current_user, current_database()
```

Accept only `("postgres", "postgres", "postgres", True, True, True)`. Zero rows or any false option
raises `DATABASE_SESSION_IDENTITY_INVALID` without relaying catalog content.

In the existing pgTAP assertion named `migration user keeps ADMIN, INHERIT, and SET for schema owner`,
split the current combined `inherit_option AND set_option` predicate into two independent `EXISTS`
blocks. Do not rename/add/remove assertions and do not change any migration, function, role or grant.

- [ ] **Step 4: Run focused GREEN and immutable regeneration**

Run the three modules. Expected: PASS. Regenerate `.1` in memory and assert all seven committed byte
hashes remain exact. Inspect that no migration, role/grant or release byte changed and that the pgTAP
diff is limited to the one approved predicate with the total assertion count unchanged.

- [ ] **Step 5: Commit Task 2**

```powershell
git add scripts/data_seed_sql.py scripts/verify_data_seed_db.py scripts/tests/test_data_seed_release.py scripts/tests/test_verify_data_seed_db.py scripts/tests/test_supabase_tooling.py supabase/tests/database/003_capabilities_test.sql
git commit -m "fix(data): align successor seed membership guard"
```

### Task 3: Add strict v2 schemas and version-aware publication

**Files:**
- Create: `data/schemas/data-seed/v2/release-manifest.schema.json`
- Create: `data/schemas/data-seed/v2/kb-records.schema.json`
- Create: `data/schemas/data-seed/v2/offices.schema.json`
- Create: `data/schemas/data-seed/v2/office-service-mappings.schema.json`
- Modify: `scripts/promote_data_seed.py`
- Modify: `scripts/tests/test_data_seed_release.py`
- Modify: `scripts/tests/test_promote_data_seed.py`

**Interfaces:**
- Produces: `.2`-only `prepare` and `activate-local-seed`; `.1`/`.2` `verify-release`; `.2`
  `verify-local-seed`.
- Consumes: exact `.1` dispatcher SHA-256 as the sole upgrade predecessor.

- [ ] **Step 1: Add RED schema and CLI state-machine tests**

Assert all v2 schemas are strict and exact `.2`. The manifest requires `schema_version=2` and:

```json
"correction": {
  "type": "object",
  "additionalProperties": false,
  "required": ["predecessor_release_version", "predecessor_manifest_sha256", "decision_id", "reason"],
  "properties": {
    "predecessor_release_version": {"const": "0.1.0-initial.1"},
    "predecessor_manifest_sha256": {"const": "e8863a633d28125ad2c0f0323d60467236d08618e767833fc7c09444f1a6e4a2"},
    "decision_id": {"const": "D-044"},
    "reason": {"const": "POSTGRES17_EFFECTIVE_MEMBERSHIP_OPTION_UNION"}
  }
}
```

Add tests proving prepare rejects `.1` and unknown versions before writes, verify accepts exact canonical
`.1` and `.2`, activation rejects `.1`, `.2` activation accepts only byte-identical `.1` predecessor,
idempotent `.2`, and rejects data-free/arbitrary/reparse/raced replacements.

- [ ] **Step 2: Run release/promoter tests and confirm RED**

```powershell
.\apps\api\.venv\Scripts\python.exe -B -m unittest -v scripts.tests.test_data_seed_release scripts.tests.test_promote_data_seed
```

Expected: v2 schema/profile and `.1→.2` predecessor tests fail without modifying the real dispatcher.

- [ ] **Step 3: Create v2 schemas and implement exact CLI rules**

Create v2 record schemas from the v1 structure using `apply_patch`; the only record-schema changes are
title/version constants from `.1` to `.2`. Create the v2 manifest with the exact correction object
above. A structural test must prove the diff from v1 is limited to title/version/id/generator,
`schema_version=2`, and correction.

Refactor CLI parsing to resolve exact raw canonical tokens through release profiles. `prepare` accepts
only `.2` and its fixed `--released-at 2026-07-20T20:41:24+09:00`; verification accepts either exact
canonical release token; activation/local verification accepts only `.2`. Change dispatcher upgrade
precondition from data-free bytes to the committed `.1` seed bytes loaded only after `.1` release
verification. Preserve all identity/reparse/create-once/fsync/quarantine rollback logic.

- [ ] **Step 4: Run GREEN and protected-path checks**

Expected: both modules PASS; `.1` and v1 diff 0; migrations/contracts/database/config diff 0.

- [ ] **Step 5: Commit Task 3**

```powershell
git add data/schemas/data-seed/v2 scripts/promote_data_seed.py scripts/tests/test_data_seed_release.py scripts/tests/test_promote_data_seed.py
git commit -m "feat(data): add successor release contract"
```

### Task 4: Bind the supported verifier and offline root gate to `.2`

**Files:**
- Modify: `scripts/verify_data_seed_db.py`
- Modify: `scripts/test_data_seed_concurrency.py`
- Modify: `scripts/verify_data_seed.ps1`
- Modify: `scripts/verify.ps1`
- Modify: `scripts/tests/test_verify_data_seed_db.py`
- Modify: `scripts/tests/test_verify_data_seed_runner.py`
- Modify: `scripts/tests/test_verify_runner.py`
- Modify: `scripts/tests/test_supabase_tooling.py`

**Interfaces:**
- Produces: supported actual runner accepting only `.2`; offline root verifies `.1`, `.2`, active `.2`.
- Preserves: patched CLI hash/runtime allowlist, stage order, stable content-free evidence and cleanup.

- [ ] **Step 1: Write runner/root RED tests**

Change exact expected release to `.2`; assert `.1` is rejected by the actual DB runner as known-broken.
Require root steps in this order:

```text
VERIFY-DATA-SEED-RELEASE-INITIAL
VERIFY-DATA-SEED-RELEASE-SUCCESSOR
VERIFY-LOCAL-SEED
```

Update the Supabase tooling invariant so `supabase/seed.sql` must equal `.2/seed.sql`, never `.1`.
Keep the actual DB stages unchanged and exact.

- [ ] **Step 2: Run runner tests and confirm RED**

```powershell
.\apps\api\.venv\Scripts\python.exe -B -m unittest -v scripts.tests.test_verify_data_seed_db scripts.tests.test_verify_data_seed_runner scripts.tests.test_verify_runner scripts.tests.test_supabase_tooling
```

Expected: failures only at stale `.1` literals/root-step expectations.

- [ ] **Step 3: Implement exact `.2` wiring**

Update Python/PowerShell accepted version literals, stable evidence regexes and release paths. Root verify
must require both v1 and v2 manifest schemas, verify both immutable releases, then verify `.2` dispatcher.
Do not add Docker to `verify.ps1 -Offline`. Do not change the actual DB runner's patched runtime hash,
DSN identity, reset order, timeouts, output allowlist, environment restore or cleanup semantics.

- [ ] **Step 4: Run the focused DATA-SEED suite**

```powershell
.\apps\api\.venv\Scripts\python.exe -B -m unittest -v scripts.tests.test_data_seed_release scripts.tests.test_promote_data_seed scripts.tests.test_verify_data_seed_db scripts.tests.test_verify_data_seed_runner scripts.tests.test_verify_runner scripts.tests.test_supabase_tooling
```

Expected: all PASS before real `.2` publication tests that explicitly require the canonical artifact;
tests needing publication use isolated temp repositories.

- [ ] **Step 5: Commit Task 4**

```powershell
git add scripts/verify_data_seed_db.py scripts/test_data_seed_concurrency.py scripts/verify_data_seed.ps1 scripts/verify.ps1 scripts/tests/test_verify_data_seed_db.py scripts/tests/test_verify_data_seed_runner.py scripts/tests/test_verify_runner.py scripts/tests/test_supabase_tooling.py
git commit -m "test(data): bind successor seed verification"
```

### Task 5: Generate, technically review, publish and activate `.2`

**Files:**
- Create: `data/official/releases/0.1.0-initial.2/approval_manifest.json`
- Create: `data/official/releases/0.1.0-initial.2/compensation.sql`
- Create: `data/official/releases/0.1.0-initial.2/kb_records.json`
- Create: `data/official/releases/0.1.0-initial.2/office_service_mappings.json`
- Create: `data/official/releases/0.1.0-initial.2/offices.json`
- Create: `data/official/releases/0.1.0-initial.2/release_manifest.json`
- Create: `data/official/releases/0.1.0-initial.2/seed.sql`
- Modify: `supabase/seed.sql`

**Interfaces:**
- Consumes: approved Task 1–4 code and exact canonical staging input.
- Produces: create-once immutable `.2` and byte-identical local dispatcher.

- [ ] **Step 1: Verify clean pre-publication state**

Run staging validator, full focused tests, `.1`/v1 hashes, secret scan, `git diff --check`, protected
migration/contract/config diff and assert `.2`/prepare temp are absent. Expected: all PASS/absent.

- [ ] **Step 2: Generate a deterministic candidate in isolated temp roots**

Build twice in separate trusted temporary repositories and compare all seven byte hashes. Expected:
both trees identical; approval bytes and parsed record content match `.1`; projection/semantic hash are
exact; seed/compensation differ from `.1` only in the approved principal block.

- [ ] **Step 3: Obtain independent technical approval before canonical publication**

Dispatch a reviewer who did not write Tasks 1–4. The reviewer checks the written spec, exact `.1`
fingerprints, v2 schema/manifest, generated `.1↔.2` semantic diff, SQL guard parity, publisher rollback,
secret/output boundary and tests. Publication is allowed only with Critical 0 and Important 0; otherwise
fix code/tests and repeat Step 2 and review. Record the reviewer identity, reviewed commit, verdict and
candidate hashes in the implementation note and later lineage.

- [ ] **Step 4: Publish the canonical `.2` release**

Run:

```powershell
.\apps\api\.venv\Scripts\python.exe -B scripts\promote_data_seed.py prepare --draft-dir data/staging/data-001/0.1.0-draft.1 --release-version 0.1.0-initial.2 --released-at 2026-07-20T20:41:24+09:00
.\apps\api\.venv\Scripts\python.exe -B scripts\promote_data_seed.py verify-release --release-dir data/official/releases/0.1.0-initial.1
.\apps\api\.venv\Scripts\python.exe -B scripts\promote_data_seed.py verify-release --release-dir data/official/releases/0.1.0-initial.2
```

Expected: prepare and both verifies PASS. A second prepare fails `RELEASE_ALREADY_EXISTS` without byte
change. Before dispatcher activation, compare canonical `.2` filename/length/SHA-256 for all seven
files with the exact independently reviewed candidate hash set. Any mismatch blocks activation and
actual DB execution; retain the create-once `.2` unchanged and require a separately approved `.3`
correction. Never delete `.2` after successful publication.

- [ ] **Step 5: Atomically activate `.2` dispatcher**

Run:

```powershell
.\apps\api\.venv\Scripts\python.exe -B scripts\promote_data_seed.py activate-local-seed --release-dir data/official/releases/0.1.0-initial.2
.\apps\api\.venv\Scripts\python.exe -B scripts\promote_data_seed.py verify-local-seed --release-dir data/official/releases/0.1.0-initial.2
```

Expected: changed=1 then active=1; rerun activation yields changed=0. Compare exact dispatcher/release
SHA. Confirm `[db.seed].enabled=false` and `.1`/v1 hashes unchanged.

- [ ] **Step 6: Commit immutable artifact and dispatcher**

```powershell
git add data/official/releases/0.1.0-initial.2 supabase/seed.sql
git commit -m "data: publish corrected immutable seed release"
```

### Task 6: Run the actual disposable DB cycle and close lineage

**Files:**
- Create: `docs/data-lineage/DATA-SEED-002-0.1.0-initial.2.md`
- Create: `docs/test-reports/DATA-SEED-002-LOCAL-VERIFICATION.md`
- Modify: `docs/data-lineage/README.md`
- Modify: `docs/test-reports/README.md`
- Modify: `data/official/README.md`
- Modify: `database/README.md`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/source-of-truth/TEAM_DECISIONS.md`
- Modify: `docs/source-of-truth/PROJECT_PLAN.md`
- Modify: `docs/11_AMBIGUITY_REGISTER.md`
- Modify: `docs/decisions/DECISION_LOG.md` (append-only rows preserved; current summary only)
- Modify: `docs/adr/0017-successor-immutable-seed-release-correction.md`
- Modify: `TASKS.md`
- Modify: `versions/manifest.json`
- Create/update: request implementation note and `docs/implementation-notes/INDEX.md`

**Interfaces:**
- Consumes: verified immutable `.2` and active dispatcher.
- Produces on PASS: `official_data=0.1.0-initial.2`; on failure: exact Blocked report and unchanged
  `official_data=0.0.0-not-populated`.

- [ ] **Step 1: Capture pre-run safety evidence**

Require Docker Desktop ready, repo-owned runtime absent, listener 54322 absent, exact patched runtime
hash present, git status understood, and no ambient `PG*` variables passed into the verifier. Do not
print the local DSN or Docker status secrets.

- [ ] **Step 2: Run the one supported actual command**

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\verify_data_seed.ps1 -ReleaseVersion 0.1.0-initial.2
```

Expected PASS evidence includes baseline pgTAP 282, backend integration 8/8, identity exact, forced
rollback partial 0, concurrency A/B, seed 19/3/10, second seed blocked, compensation guard blocked,
compensation/reseed/replay, final citizen 19, exclusions 0, operational 0 and exact semantic SHA.

If any stage fails, stop promotion, preserve `.2`, record only reached stages, verify cleanup, keep
`official_data` unchanged, and close DATA-SEED-002 as Blocked. Do not improvise a role/grant/migration
or rerun manually outside the supported runner.

- [ ] **Step 3: Record actual report and lineage**

Write exact start/end commit, command, reached stages, counts, hashes, runtime identity, independent
review verdict, cleanup counts and unreached tests. The lineage explicitly links `.1` predecessor
manifest SHA, D-044, source approval SHA and v2 correction reason. It contains no DSN, key, question,
PII or provider body.

- [ ] **Step 4: Promote versions only on complete PASS**

On PASS update `official_data` from `0.0.0-not-populated` to `0.1.0-initial.2`, increment the test suite
for the verified successor/DB gate, and increment documentation. Keep application, web, API, shared
contracts, DB schema, mock data and prompt versions unchanged. Keep `/ready=503`; set DATA-SEED-001
historical blocker resolved by DATA-SEED-002 and mark DATA-SEED-002 Done. READY-001 becomes Ready for
its separate plan.

On failure, increment only test/documentation if code/gates changed, keep official-data unchanged,
and leave READY/AI blocked with the exact new cause.

- [ ] **Step 5: Run final verification**

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\verify.ps1 -Offline
git diff --check
git status --short
```

Also run package validation, secret scan, exact `.1`/v1 fingerprint check, both release verifiers,
active `.2` dispatcher verification and protected migration/contract/config diff. Expected: all PASS,
no temporary/quarantine files, no product code/contract/migration/config diff; the only DB-test diff is
the reviewed `003_capabilities_test.sql` predicate alignment.

- [ ] **Step 6: Request final two-stage review and commit closeout**

Use `superpowers:requesting-code-review` for specification compliance and code/data quality. Fix every
Critical/Important finding, rerun affected tests, then commit report/lineage/version/task/note changes:

```powershell
git add README.md CHANGELOG.md docs data/official/README.md database/README.md TASKS.md versions/manifest.json
git commit -m "docs: verify corrected official seed release"
```

## Failure and recovery matrix

| Failure | Required outcome |
|---|---|
| `.1` fingerprint drift | Stop before `.2` generation; restore by reverting only the unauthorized change, never regenerate over `.1` |
| candidate mismatch | Delete only owned temporary candidate; canonical `.2` remains absent |
| technical review finding | Fix generator/test code, rebuild isolated candidate, repeat review |
| canonical publish collision | Fail closed; inspect existing `.2`, never overwrite/delete automatically |
| canonical bytes differ from reviewed candidate | Do not activate or run DB; retain immutable `.2` and require an approved `.3` correction |
| dispatcher activation failure | Restore and byte-verify captured `.1`; no DB run |
| actual DB stage failure | Transaction rollback, cleanup proof, `.2` retained, official-data unchanged, report Blocked |
| successful `.2` activation then later code defect | Do not roll back to known-broken `.1`; use a separately approved `.3` correction |
| public/remote request | Reject; SEC-003 `00700` and deployment approval are separate |

## Plan self-review

- Spec coverage: `.1` immutability, dual profiles, v2 correction lineage, effective union, publication,
  dispatcher rollback, full DB cycle, promotion and non-goals each map to a task.
- Incomplete-marker scan: no unresolved marker or ambient timestamp; all identities, versions, counts, hashes, commands
  and error boundaries needed before execution are fixed.
- Type consistency: `ReleaseProfile.membership_guard` is consumed by both SQL renderers; `.2` is the
  only active runner/dispatcher version; `.1` remains verification-only.
- Scope: one vertical DATA-SEED correction. PII consumer, `00700`, READY and public deployment are
  explicitly excluded.
