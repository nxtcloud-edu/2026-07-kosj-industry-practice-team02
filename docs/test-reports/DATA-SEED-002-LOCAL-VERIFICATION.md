# DATA-SEED-002 disposable local verification

- Status: **Blocked**
- Release: `0.1.0-initial.2`
- Attempt 1 HEAD: `4a9ae513d568c8ae50c74bdf6954f87a46439c76`
- Authorized retry HEAD: `e314592c4a8a3c38539d9ffb243f1233fe7f3543`
- Reviewed diagnostic HEAD: `f47edac9dd99cefd84e46c0c00e08b4d67bb77ef`
- Supported command: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\verify_data_seed.ps1 -ReleaseVersion 0.1.0-initial.2`
- Result boundary: all three runs passed through concurrency A. The first two failed concurrency B
  with parent evidence `reason=child code=2`; the reviewed diagnostic isolated
  `reason=CAPABILITY_WRITE_DID_NOT_BLOCK code=2`. No actual 19/3/10 import is claimed.

## 1. Result

The immutable successor release and local dispatcher passed exact identity checks before and after
the two initial attempts and the reviewed diagnostic. The database verifier passed its composite
baseline, exact seed identity, forced
rollback and concurrency A stages. It did not pass concurrency B, so the runner correctly stopped
before seed-cycle and final verification stages.

The first attempt also exposed a cleanup allowlist defect and left one exact-owned container and one
port 54322 listener. After reviewed, targeted cleanup, the authorized retry began from container 0
and listener 0. The retry's cleanup passed and restored that absent state, but the repeated
concurrency B failure keeps the entire DATA-SEED-002 actual gate Blocked.

After the strict failure relay passed independent review, one diagnostic run began from the same
container/listener-absent boundary. It again passed baseline, exact identity, forced rollback and
concurrency A, then identified the concurrency B failure as `CAPABILITY_WRITE_DID_NOT_BLOCK`.
Cleanup passed and restored exact-owned containers/listeners to 0. No automatic fourth run occurred.

`versions/manifest.json.versions.official_data` remains `0.0.0-not-populated`. The release's 19 KB,
3 offices and 10 mappings are filesystem projection counts only; PostgreSQL ACTIVE KB 19,
citizen-read and READY/AI status were not proven.

## 2. Immutable release and runtime identity

| Evidence | Actual result |
|---|---|
| Successor release ID/schema | `sejong-official-0.1.0-initial.2` / schema `2` |
| Release manifest SHA-256 | `0ccf3326616fdf0d9d96622f560e30da75d457c8295fc8bf37d2a601829a11a9` |
| Release/dispatcher seed SHA-256 | `44dc7f3c0d6c4d473119b1dcb1871e8a0133c305eac40ce8fbf36e3b7937b1e7` |
| Filesystem semantic SHA-256 | `c838a4aa5eb1675d93fbaebd99b63d823490eb172c64cc356c5f72114cc1e4eb` |
| Approval manifest SHA-256 | `466d7af44cc36a9ee1ea1eed3d90f0e6fa1627fc57c03de5377c6f9f9fef5b6a` |
| Predecessor manifest SHA-256 | `e8863a633d28125ad2c0f0323d60467236d08618e767833fc7c09444f1a6e4a2` |
| Patched CLI SHA-256 allowlist | `751068e73834c5da58ac7c5287a1d66a82ad356f508637b0478d6531cdb3941c` matched |
| Immutable filesystem projection | KB 19 / offices 3 / mappings 10 / mock 0 / withheld KB 1 / rejected mappings 2 |
| Automatic reset import | disabled (`[db.seed].enabled=false`) |

All three preflights recorded Docker ready, an absent exact-owned runtime and listener, no ambient
`PG*`/Sejong database environment variables and an exact regular non-reparse patched runtime hash.
Neither evidence file retained or emitted a DSN or secret.

## 3. Attempt 1 stage evidence

- Repository HEAD: `4a9ae513d568c8ae50c74bdf6954f87a46439c76`
- Exit/duration: `1` / `108.127` seconds
- Supported command run count: `1`
- Tracked pre/post status identity:
  `f7e7319dc0790f5396243650d37d00570ff2cb89504cd271f80789d98c54151a`
- Tracked changes introduced by the cycle: `0`

| Stage | Stable result |
|---|---|
| `PREFLIGHT-DATA-SEED-DOCKER` | PASS |
| `VERIFY-DATA-SEED-RUNTIME-ABSENT` | PASS |
| `VERIFY-DATABASE-BASELINE` | PASS |
| `VERIFY-DATA-SEED-PATCHED-RUNTIME` | PASS |
| `READ-LOCAL-DATABASE-STATUS` | PASS |
| `VERIFY-DATA-SEED-IDENTITY` | PASS, `identity=exact` |
| `RESET-BEFORE-FAILURE-ROLLBACK` | PASS |
| `VERIFY-DATA-SEED-FAILURE-ROLLBACK` | PASS, `tables=8 partial=0` |
| `RESET-BEFORE-CONCURRENCY-A` | PASS |
| `VERIFY-DATA-SEED-CONCURRENCY-A` | PASS, `ordering=capability-before-lock seed_rows=0 capability_rows=1` |
| `RESET-BEFORE-CONCURRENCY-B` | PASS |
| `VERIFY-DATA-SEED-CONCURRENCY-B` | STARTED_THEN_FAILED, `reason=child code=2` |
| `CLEANUP-DATA-SEED-RUNTIME` | STARTED_THEN_FAILED, `reason=invalid code=2` |

At runner exit, exact-owned containers 1 and port 54322 listeners 1 remained. Seven successor hashes,
the dispatcher, `.1` release and tracked tree still matched. Project volumes 2 were preserved and no
volume deletion command was issued.

The exact-owned runtime was then stopped using pinned
`supabase stop --project-id sejong-ai-local` only after targeted owner/name/port/network validation.
This reviewed recovery produced containers 0, listeners 0, volumes 2 preserved and loopback network
1 preserved. No raw Docker removal or volume/network deletion was used.

## 4. Authorized retry stage evidence

- Repository HEAD: `e314592c4a8a3c38539d9ffb243f1233fe7f3543`
- Recovery commits:
  - `50fe4a3e2a0f28ed174ff7dc8eaa14a8f2167026` — reviewed concurrency lock expectation;
    relevant tests 52/52 PASS.
  - `e314592c4a8a3c38539d9ffb243f1233fe7f3543` — reviewed cleanup/reset-network and ordinal
    equality hardening; Task 4 tests 120/120 PASS with 11 Unicode-confusable negatives.
- Exit/duration: `1` / `109.122` seconds
- Authorized retry run count: `1`
- Tracked pre/post status identity:
  `f7e7319dc0790f5396243650d37d00570ff2cb89504cd271f80789d98c54151a`
- Tracked changes introduced by the retry: `0`

| Stage | Stable result |
|---|---|
| preflight through `VERIFY-DATA-SEED-IDENTITY` | all PASS, `identity=exact` |
| failure rollback | PASS, `tables=8 partial=0` |
| concurrency A | PASS, `ordering=capability-before-lock seed_rows=0 capability_rows=1` |
| `RESET-BEFORE-CONCURRENCY-B` | PASS |
| `VERIFY-DATA-SEED-CONCURRENCY-B` | STARTED_THEN_FAILED, `reason=child code=2` |
| `CLEANUP-DATA-SEED-RUNTIME` | PASS |

Final postconditions were exact-owned containers 0, project-label containers 0, port 54322 listeners
0, cleanup complete, project volumes 2 and project network 1 preserved. Seven successor hashes,
the predecessor release, successor release and active dispatcher all remained exact; no temporary or
quarantine artifact remained.

## 5. Explicitly unreached evidence

The following items are **UNREACHED**, not PASS:

- concurrency B PASS;
- PostgreSQL seed counts 19/3/10;
- second-seed rejection;
- compensation guard rejection and compensation/reseed/replay;
- final database semantic SHA-256;
- final citizen ACTIVE count 19, excluded count 0 and operational row count 0.

The existing DB baseline stage is recorded only as the composite PASS emitted by the supported
runner. This report does not fabricate separate pgTAP/backend counts that were not emitted by these
attempt evidence files.

## 6. Reviewed diagnostic stage evidence

- Repository HEAD: `f47edac9dd99cefd84e46c0c00e08b4d67bb77ef`
- Diagnostic change: exact one-line, same-step, ASCII stable reason relay; any stderr, extra blank or
  payload line, wrong step or malformed reason falls back to `child` without disclosure.
- Independent review: Critical/Important/Minor `0/0/0`; runner tests 29/29 PASS.
- Preflight: Docker ready; exact-owned/project-label containers 0; listener 54322 count 0; patched
  runtime regular/non-reparse and exact hash; ambient `PG*`/Sejong database variables 0.
- Reached result: baseline, patched runtime, DB status, identity, rollback and concurrency A PASS;
  concurrency B `reason=CAPABILITY_WRITE_DID_NOT_BLOCK code=2`; cleanup PASS.
- Postcondition: exact-owned/project-label containers 0 and listener 54322 count 0. Immutable release
  and dispatcher files were not modified.

## 7. Current diagnosis gate and handoff

Commit `f47edac9dd99cefd84e46c0c00e08b4d67bb77ef` adds a bounded diagnostic relay that accepts only an
exact, content-free child failure line and falls back to the existing generic `child` reason for
malformed, mismatched or extra output. Independent review passed and the one diagnostic run established
the exact failure above. Commit `eb74ac8` replaces the search-path-sensitive `regclass::text` relation
name with an exact relation-OID equality predicate. Its 25/25 verifier tests and independent
Critical/Important/Minor `0/0/0` review passed, but that review authorized the code commit only and no
actual DB run has exercised it. This report does not claim the concurrency B cause is resolved.

The next operator must:

1. record a separate operational execution decision for reviewed commit `eb74ac8` before another
   actual run;
2. reconfirm container/listener 0, preserved volumes/network, patched runtime hash and no ambient DB
   environment variables without printing values;
3. verify `.1`, `.2` and active dispatcher bytes, then use only the supported command;
4. on failure, stop promotion, prove exact cleanup and retain `official_data=0.0.0-not-populated`;
5. promote versions only after concurrency B, seed-cycle, compensation/replay, final projection and
   cleanup all emit fresh PASS evidence.

## 8. Security, privacy and rollback boundary

- No DSN, password, key, token, provider body, citizen question, PII, raw SQL/catalog row or official
  KB payload is included in the evidence or this report.
- Neither attempt used DeepSeek, a remote database, deployment service or public runtime.
- `.1` and `.2` are immutable. Never edit/delete them or roll the dispatcher back to the known-broken
  `.1`; a release defect requires a separately approved `.3`.
- Preserve volumes/network. Do not use raw Docker removal, prune or ad-hoc role/grant/migration
  recovery.
- `/ready=503`, READY-001 and AI-001 remain blocked until the full local gate succeeds.

Release lineage and all seven canonical hashes are in
[`DATA-SEED-002-0.1.0-initial.2.md`](../data-lineage/DATA-SEED-002-0.1.0-initial.2.md).
