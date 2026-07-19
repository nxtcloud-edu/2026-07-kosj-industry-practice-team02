# DATA-SEED-001 disposable local verification

- Status: **Blocked**
- Verification window (KST): 2026-07-20 00:21:14 ~ 00:51:40
- Release: `0.1.0-initial.1`
- Starting HEAD: `95b757733a1777323ccda5e3b0ba3e95af94477c`
- Final code HEAD before this report: `afe47ccca51ece2bfe91fd5f57fbcea85c738e09`
- Supported command: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_data_seed.ps1 -ReleaseVersion 0.1.0-initial.1`

## 1. Result

The approved runner did not reach seed, compensation, concurrency, replay, or final citizen-read
evidence. The disposable PostgreSQL gate is blocked before writes because the immutable release SQL
requires exactly one `sejong_schema_owner -> postgres` membership row with ADMIN, INHERIT and SET all
true, while the authoritative DB migration and pgTAP contract intentionally validate the effective
union of those options across grantor-specific rows.

No role/grant, migration, release, dispatcher, official-data version, application table, or public
runtime was changed to work around the mismatch. `versions/manifest.json.versions.official_data`
remains `0.0.0-not-populated`.

## 2. Runtime and release identity

| Evidence | Actual result |
|---|---|
| Docker Server | `29.2.1` |
| Pinned patched Supabase CLI | `2.109.1` |
| Patched CLI SHA-256 | `751068e73834c5da58ac7c5287a1d66a82ad356f508637b0478d6531cdb3941c` |
| PostgreSQL runtime image | `public.ecr.aws/supabase/postgres:17.6.1.143` |
| Host binding while running | exactly `127.0.0.1:54322 -> 5432/tcp` |
| Release manifest SHA-256 | `e8863a633d28125ad2c0f0323d60467236d08618e767833fc7c09444f1a6e4a2` |
| Release/dispatcher seed SHA-256 | `42d67828bb23c0eb0fa17ae2daa7d457fd71806b7cc796a54643dd975597783d` |
| Filesystem semantic SHA-256 | `c838a4aa5eb1675d93fbaebd99b63d823490eb172c64cc356c5f72114cc1e4eb` |
| Immutable projection | 19 KB / 3 offices / 10 mappings; mock 0; withheld KB 1; rejected mappings 2 |

The PostgreSQL image identity came from the repo-labelled container event. A separate server-version
SQL string was not captured before cleanup, so the image version is recorded without overstating it as
an independently queried server string.

## 3. Actual attempts and stable runner evidence

| Attempt | Time/duration | Stable result | Disposition |
|---|---|---|---|
| 1 | start after `00:21:14`; about 42.1 s | `VERIFY-DATABASE-BASELINE` PASS, then `VERIFY-DATA-SEED-PATCHED-RUNTIME` failed `operational` | PowerShell 5.1 strict-mode empty diff bug; no seed stage reached |
| 2 | `00:35:53`; about 2.1 s | nested `VERIFY-DATABASE-BASELINE` failed `child` | attempt 1 baseline reset had recreated the repo-owned container on the Supabase default network; runner correctly rejected retry state |
| 3 | after approved pinned-CLI recovery at `00:38:28`; about 47.1 s | baseline PASS, patched runtime PASS, status PASS, identity failed `child` | content-free diagnostic first found invalid `pg_catalog.coalesce` syntax, then exposed the authoritative membership-contract conflict |

`VERIFY-DATABASE-BASELINE` is the existing composite patched DB gate. The parent runner deliberately
does not relay the nested pgTAP/backend child output. Therefore this report records the stable
composite PASS but does not fabricate separate numeric pgTAP or integration output for this Task 6
run.

## 4. Reviewed code remediations

1. `faa34d49b02d75342c0f3df7921b24571887911d` —
   `fix(data): handle empty patched runtime diff`
   - Root cause: `Compare-Object` returns `$null` when equal; strict mode rejected `.Count`.
   - TDD: exact regression RED 1/1, then GREEN; focused 34/34; current-compatible runner/tooling 93/93.
   - Independent review: Critical/Important/Minor `0/0/0`.
2. `afe47ccca51ece2bfe91fd5f57fbcea85c738e09` —
   `fix(data): use valid identity guard syntax`
   - Root cause: `COALESCE` is a SQL special form and cannot be invoked as
     `pg_catalog.coalesce`.
   - TDD: exact session-query regression RED 1/1, then GREEN; focused 35/35; current-compatible
     runner/tooling/root-runner 94/94 in 89.088 s; Ruff, format and strict Mypy PASS.
   - Independent review: Critical/Important/Minor `0/0/0`.

Package validation, secret scan, `git diff --check`, protected-path diff, staging/release/dispatcher
hashes and `official_data` non-promotion checks passed after both fixes. A broad 202-test Task 1–4
combination produced 42 failures and 2 errors because pre-publication tests still assume an absent
release and data-free dispatcher after Task 5 publication. This is recorded for Task 7 to make those
tests active-release-aware; it was not hidden or treated as evidence for this blocker.

## 5. Blocking contract evidence

The following repository authorities use effective membership-option union rather than a single
catalog row:

- `supabase/migrations/20260716000300_capabilities_and_functions.sql` validates ADMIN, INHERIT and
  SET with separate `EXISTS` predicates.
- `supabase/tests/database/003_capabilities_test.sql` validates the same split-row effective options.
- `docs/implementation-notes/IMP-20260716-008-db-001-task5-capabilities-and-retention.md` records that
  PostgreSQL 17 can split membership options by grantor and tests must inspect the effective union.

The content-free actual catalog diagnostic observed two rows for the exact role/member pair:

- grantor `postgres`: ADMIN false, INHERIT true, SET true;
- grantor `supabase_admin`: ADMIN true, INHERIT false, SET false.

By contrast, the immutable `0.1.0-initial.1` seed and compensation guard generated by
`scripts/data_seed_sql.py` requires membership count `1` and `bool_and(ADMIN AND INHERIT AND SET)`.
Changing only the Python verifier would not help: the immutable SQL would reject the same safe
grantor-specific representation before writes.

## 6. Unreached acceptance evidence

The following must **not** be read as PASS for this run:

- forced mid-import rollback and partial row count;
- concurrency scenarios A and B;
- seed counts 19/3/10 in PostgreSQL;
- second-seed rejection;
- compensation guard and compensation-to-reseed replay;
- final database semantic hash;
- final citizen 19, exclusions 0, operational 0.

The manifest semantic hash above is filesystem evidence only. There is no actual DB semantic hash
claim because the seed stage was never reached.

## 7. Security, privacy and cleanup boundary

- DSN, password, raw SQL, official KB content, approval comments, citizen question text, PII and
  secrets were not written to this report or implementation note.
- No unrelated container, volume or network was stopped, removed or pruned.
- Retry recovery and final cleanup used only the pinned CLI command
  `.\.tools\supabase\v2.109.1-sejong-loopback\supabase.exe stop` after exact project-label, name,
  network and port inspection.
- Final evidence at `2026-07-20T00:51:40+09:00`: repo-owned containers `0`, listeners on port 54322
  `0`, repo-owned volumes `2` preserved, `sejong-ai-local-loopback` network `1` preserved.
- The baseline reset can recreate the DB container on `supabase_network_sejong-ai-local`; its host
  publish remained exact loopback, but a retry requires the approved pinned-CLI stop back to absent
  state. This composability risk remains documented.

## 8. Human decision and recommended next step

A new human-approved DATA-SEED design is required. The recommendation is to create a successor
immutable release whose role guard checks the effective ADMIN/INHERIT/SET union in the same way as the
existing migration and pgTAP authority, while retaining exact local principal, role-switch, table-lock,
empty-database and bidirectional semantic guards. The alternative is an explicit role/grant
normalization design, which changes global DB privilege state and is not approved here.

The existing `0.1.0-initial.1` bytes must remain untouched. After the successor decision, rerun the
entire supported actual cycle from an absent repo-owned runtime and promote `official_data` only if
every previously unreached acceptance item emits fresh PASS evidence.
