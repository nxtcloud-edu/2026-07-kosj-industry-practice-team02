# DATA-SEED-001 Task 7A offline root gate report

- Status: **PASS — nonblocked code/test slice complete**
- Starting HEAD: `0a0d2064acaddf4ff9b3b6098cd4d99ad6c94d24`
- Scope: active-release-compatible offline/root verification only
- Immutable release, dispatcher, config, migrations, DB definitions, Docker runtime, product code,
  contracts, documentation, and version manifest: unchanged

## Root-cause evidence and TDD

Task 5 legitimately published `data/official/releases/0.1.0-initial.1/` and activated the
byte-identical `supabase/seed.sql` dispatcher. Prepublication publication tests still copied both live
states into temporary repositories while asserting that the release was absent and the dispatcher was
the canonical initial empty dispatcher. The deterministic generator test likewise copied the live
release before asserting that generation wrote no release directory. The Supabase tooling contract
still asserted the obsolete empty dispatcher bytes.

- Supplied active-release baseline: 202 tests, 42 failures and 2 errors.
- Direct reproduction confirmed failures in publication/activation cases, the deterministic no-write
  case, and the stale empty-dispatcher assertion.
- Root-gate TDD RED: `scripts.tests.test_verify_runner` ran 17 tests with 5 failures because the three
  DATA-SEED stages and their exact wiring were absent.
- Root-gate GREEN: the same suite passed 17/17 after the minimal runner change.

## Implemented behavior

- Publication fixtures now exclude the live `data/official/releases` directory and explicitly write
  the canonical initial dispatcher bytes before exercising prepare/activate behavior.
- The deterministic generator fixture excludes the live release and asserts absence both before and
  after bundle generation.
- Supabase tooling now asserts that the active dispatcher byte-equals the canonical release seed while
  `[db.seed].enabled=false` and `sql_paths=["./seed.sql"]` remain unchanged.
- `scripts/verify.ps1` now runs these stable stages immediately after `VALIDATE-DATA-001` with the
  locked API Python:
  - `TEST-DATA-SEED`: Task 1–4 focused unit/static suites
  - `VERIFY-DATA-SEED-RELEASE`: direct `promote_data_seed.py verify-release` for exact version
    `0.1.0-initial.1`
  - `VERIFY-LOCAL-SEED`: direct `promote_data_seed.py verify-local-seed` for the same release
- Required release marker/schema/dispatcher files are checked before their read-only verification.
  Child output is not relayed, child exit codes propagate, and no prepare, activate, Docker, DB, DSN,
  source-content, or external-provider path was added.

## Verification evidence

- Fixture/tooling suites: 128/128 PASS.
- DATA-SEED Task 1–4 focused suites: 113/113 PASS.
- Root runner suite: 17/17 PASS.
- Full `scripts/tests` discovery: 286 tests PASS, 1 environment-dependent symlink fixture skipped,
  0 failures, 0 errors, 243.395 seconds.
- Direct `verify-release`: PASS, `issues=0`.
- Direct `verify-local-seed`: PASS, `active=1`.
- Actual `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1`: PASS through
  `TEST-ROOT`, `VALIDATE-DATA-001`, all three new DATA-SEED stages, Web, API, contracts, both secret
  boundaries, package validation, and diff check; final output `[PASS] verification=complete`.
- `py_compile`: PASS for all four changed Python test modules.
- Package validator: PASS, 12 required files and valid version manifest.
- Secret scan and `git diff --check`: PASS.
- Protected-scope comparison from starting HEAD: official release, dispatcher/config, version manifest,
  migrations, and database definitions unchanged.

Repository-wide Ruff/format/mypy are not configured as a clean gate for `scripts/tests`. Focused checks
reported only pre-existing findings in `test_supabase_tooling.py`: Ruff F841/F541 at lines 343/349 and
mypy `arg-type` at line 1925; Git blame binds them to older commits. No unrelated cleanup was included.

## Remaining blocker and boundary

Task 6 remains blocked exactly as reported: PostgreSQL 17 expresses the effective ADMIN/INHERIT/SET
membership option union across grantor-specific rows, while immutable release seed/compensation guards
require one row carrying all three flags. This task did not hide, weaken, or modify that contract.
`versions/manifest.json.official_data` remains `0.0.0-not-populated`; no version or documentation
promotion is claimed. No Docker or database command was executed.
