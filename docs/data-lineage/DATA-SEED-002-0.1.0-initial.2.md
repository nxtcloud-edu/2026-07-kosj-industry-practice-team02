# DATA-SEED-002 — `0.1.0-initial.2` lineage

- Status: **immutable filesystem release published and byte-verified / supported actual database cycle PASS (2026-07-22 continuation)**
- Release ID: `sejong-official-0.1.0-initial.2`
- Governance release time: `2026-07-20T11:41:24Z`
- Approval reviewer/time: `PM-LOCAL-001` / `2026-07-19T02:06:19+09:00`
- Projection in the release: ACTIVE/OFFICIAL KB 19, OFFICIAL office 3, approved mapping 10,
  mock 0
- Runtime boundary: `supabase/seed.sql` is byte-identical to the `.2` release seed, but
  `[db.seed].enabled=false`; automatic reset import is disabled.
- Product boundary: the 2026-07-22 supported continuation reached seed import and final verification.
  PostgreSQL local projection is ACTIVE/OFFICIAL KB 19, OFFICIAL office 3 and approved mapping 10;
  `official_data=0.1.0-initial.2` is authoritative. `/ready=200`, 20th ACTIVE and any public/remote
  readiness remain separate, unclaimed gates.

## 1. Source approval and correction lineage

The canonical authoring input remains `data/staging/data-001/0.1.0-draft.1/`. PM approval selected
19 of 20 KB records, all 3 offices and 10 of 12 mappings. DATA-SEED-002 does not alter those source
decisions: its release approval manifest is byte-identical to the approved staging manifest.

| Source artifact | Source records | SHA-256 |
|---|---:|---|
| staging `kb_records.json` | 20 | `38d0c801b3dab3962b5cd01fe15a43a60121963b53e8b1f7ac65304d07267365` |
| staging `offices.json` | 3 | `fe942ce476c7d78f5b17deb10fd3b53e5b673f3ae36cf67a042823ccd51a7af0` |
| staging `office_service_mappings.json` | 12 | `a0fb8f3c423c0b0b199ed27cdb35cf40efa9011e7ae3d6736f420fc175ee4e1b` |
| approval manifest (staging and `.2`) | 35 decisions | `466d7af44cc36a9ee1ea1eed3d90f0e6fa1627fc57c03de5377c6f9f9fef5b6a` |

This successor implements D-044/Q-SEED-002 A and ADR-0017. Its correction reason is
`POSTGRES17_EFFECTIVE_MEMBERSHIP_OPTION_UNION`: it preserves the approved data projection while
aligning the seed and compensation membership guard with the existing migration's effective
ADMIN/INHERIT/SET option union. It does not rewrite the immutable predecessor.

- Predecessor: `0.1.0-initial.1`
- Predecessor manifest SHA-256:
  `e8863a633d28125ad2c0f0323d60467236d08618e767833fc7c09444f1a6e4a2`
- Successor schema/generator: `2` / `data-seed-release-v2`
- Shared filesystem semantic SHA-256:
  `c838a4aa5eb1675d93fbaebd99b63d823490eb172c64cc356c5f72114cc1e4eb`
- Excluded KB: `KB-WASTE-03` (`WITHHOLD_FOR_REGRESSION`)
- Excluded mappings: `OFFICE-AREUM:LOCAL_TAX_GENERAL`,
  `OFFICE-DODAM:BULKY_WASTE` (`REJECT`)

## 2. Immutable successor artifacts

Commit `3f0e906cc539dca03d0e21139e12a330338af638` published the independently reviewed candidate as
seven create-once files and activated the local dispatcher. The candidate gate passed 206/206 and
the independent technical review found Critical/Important/Minor `0/0/0`. Commit
`4a9ae513d568c8ae50c74bdf6954f87a46439c76` then isolated post-publication promoter fixtures;
release/promoter tests passed 89/89 and the independent re-review was clean. These are filesystem
and test results, not actual import proof.

| Release artifact | Bytes | Release records | SHA-256 |
|---|---:|---:|---|
| `approval_manifest.json` | 13,074 | 35 decisions | `466d7af44cc36a9ee1ea1eed3d90f0e6fa1627fc57c03de5377c6f9f9fef5b6a` |
| `compensation.sql` | 41,968 | n/a | `4b0994db69b0297a63607c3e65b835fd15bef359b8280eee9042f3760cd2b1f1` |
| `kb_records.json` | 37,208 | 19 | `1c4c303d8f0057d285023ba18a3d2829fcf856c1140baa270456aaf061c0fdaf` |
| `office_service_mappings.json` | 4,057 | 10 | `2fdffda6ff3019d3c0848f5611505a73e8ea0c25617bc9c6ed5f8780849f8697` |
| `offices.json` | 2,263 | 3 | `3eea2eb46cae9367c55e2f13d52186a74a3c48f0143f7cc79c40a08606ec6f79` |
| `release_manifest.json` | 1,874 | n/a | `0ccf3326616fdf0d9d96622f560e30da75d457c8295fc8bf37d2a601829a11a9` |
| `seed.sql` | 76,149 | n/a | `44dc7f3c0d6c4d473119b1dcb1871e8a0133c305eac40ce8fbf36e3b7937b1e7` |

Dispatcher `supabase/seed.sql` has SHA-256
`44dc7f3c0d6c4d473119b1dcb1871e8a0133c305eac40ce8fbf36e3b7937b1e7` and is byte-identical to
the release `seed.sql`. All seven successor hashes matched after the two initial attempts and the
reviewed diagnostic; `.1`, `.2` and the dispatcher acquired no tracked change from any run.

## 3. Actual local database evidence

The supported command was used for both authorized attempts:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\verify_data_seed.ps1 -ReleaseVersion 0.1.0-initial.2
```

| Attempt | Repository HEAD | Reached evidence | Stop and cleanup result |
|---:|---|---|---|
| 1 | `4a9ae513d568c8ae50c74bdf6954f87a46439c76` | baseline PASS; identity exact; forced rollback tables 8/partial 0; concurrency A PASS with seed rows 0/capability rows 1 | concurrency B failed `reason=child code=2`; runner cleanup failed `reason=invalid code=2` |
| authorized retry | `e314592c4a8a3c38539d9ffb243f1233fe7f3543` | same reached PASS evidence through concurrency A | concurrency B again failed `reason=child code=2`; cleanup PASS |
| reviewed diagnostic | `f47edac9dd99cefd84e46c0c00e08b4d67bb77ef` | same reached PASS evidence through concurrency A; strict child-reason relay active | concurrency B failed `reason=CAPABILITY_WRITE_DID_NOT_BLOCK code=2`; cleanup PASS |

After attempt 1, the exact-owned runtime was stopped only after targeted owner, name, port and
network checks, using the pinned `supabase stop --project-id sejong-ai-local` path. Postcondition was
owned containers 0, port 54322 listeners 0, project volumes 2 preserved and loopback network 1
preserved. No raw Docker removal or volume/network deletion occurred.

The retry included reviewed verifier remediations:

- `50fe4a3e2a0f28ed174ff7dc8eaa14a8f2167026` — concurrency lock expectation; focused tests
  52/52 PASS and independent review clean.
- `e314592c4a8a3c38539d9ffb243f1233fe7f3543` — exact reset-network cleanup boundary plus ordinal
  comparison hardening; Task 4 tests 120/120 PASS, including 11 Unicode-confusable negatives, and
  independent security review clean.

The retry and reviewed diagnostic run both finished with owned containers 0, port 54322 listeners 0
and cleanup PASS. Neither run issued a volume/network deletion command. The diagnostic run proved
that the failure is the lock observation predicate timing out, not a hidden child payload or a later
seed-cycle result. It still did not prove concurrency B, seed import, second-seed rejection,
compensation guard, compensation/reseed/replay, final database semantic hash, citizen 19,
exclusions 0 or operational rows 0. None of these unreached items is reported as PASS.

## 4. Current status and next gate

DATA-SEED-002 is **Blocked**, not Done. The immutable `.2` publication is valid, but an artifact
containing 19 ACTIVE records is not evidence that 19 ACTIVE rows exist in the local database.
Consequently `/ready=503`, READY-001 and AI-001 remain blocked and no `official_data` version
promotion is allowed.

Commit `f47edac9dd99cefd84e46c0c00e08b4d67bb77ef` added an independently reviewed, bounded relay that
accepts only one exact same-step stable failure line, rejects any stderr/extra line and never exposes
the child payload. Its one authorized diagnostic run returned
`CAPABILITY_WRITE_DID_NOT_BLOCK`. Static follow-up identified a search-path-sensitive
`regclass::text` relation comparison in the observation query. Commit `eb74ac8` replaces it with
exact relation-OID equality; 25/25 DB verifier tests and independent Critical/Important/Minor `0/0/0`
review passed. The review authorizes the code commit only, not another actual run. No further actual
run is authorized by this lineage record.

## 4A. 2026-07-22 supported actual PASS continuation

This continuation supersedes only the historical **Blocked** status in sections 3–4; the earlier
attempt chronology remains evidence and is not rewritten. After the concurrency observer accepted
`AccessShareLock`/`RowShareLock` for the exact protected relation, the approved supported runner was
run from the owner worktree (`HEAD f15b189` plus the in-progress local MVP integration) without
printing a DSN, secret or citizen question.

| Required stage | Result |
|---|---|
| baseline, exact `.2` identity | PASS |
| forced rollback | PASS (`tables=8`, `partial=0`) |
| concurrency A and B | PASS |
| seed cycle | PASS: KB 19 / office 3 / mapping 10 |
| replay and second seed | PASS; replay 1, second seed blocked |
| compensation guard | PASS; blocked as required |
| final projection | PASS: citizen 19 / exclusions 0 / operational 0 |
| cleanup | PASS; exact-owned runtime process/container 0 |

The immutable `.2` artifacts and dispatcher did not change. This is a local/private evidence
promotion only: it does not activate a remote database, provider, deployment, public admin, or
application `/ready=200`. The authoritative command is recorded above; the private source
repository's detailed execution report is intentionally excluded from this public evaluation
snapshot.

## 5. Security, privacy, rollback and handoff

- This lineage contains no DSN, key, token, provider payload, citizen question, raw official-data
  body or PII. Neither actual attempt used DeepSeek, remote DB or deployment services.
- Never edit, delete, overwrite or rename away `.1` or `.2`. A defect discovered after publication
  requires a separately approved immutable `.3` successor.
- Historical pre-continuation instruction (superseded by section 4A): keep `[db.seed].enabled=false`
  and `official_data=0.0.0-not-populated` until one supported cycle reaches every required stage and
  cleanup PASS. The supported cycle now passed; auto-seed remains disabled and `.2` stays immutable.
- Before a future attempt, require a separate operational execution decision for reviewed commit
  `eb74ac8`, an absent exact-owned runtime and listener, the pinned runtime and both
  releases/dispatcher, and use only the supported command above.
- On any future failure, stop promotion, retain `.2`, record only reached stages, prove cleanup and
  do not improvise role/grant/migration or destructive Docker recovery.

The detailed reached/unreached stage report remains in the private source repository and is
intentionally excluded from this public evaluation snapshot.
