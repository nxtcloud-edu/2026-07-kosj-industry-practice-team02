# DB-001 Deferred Active Question Trigger Security Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the deferred ACTIVE-question invariant executable through the restricted backend approval capability without granting the backend any private-schema or table privilege.

**Architecture:** Preserve immutable migrations `00100` through `00500` and add one forward-only `00600` posture correction for `app_private.validate_active_kb_question()`. The function body and deferred triggers remain unchanged; pgTAP proves the exact owner, search path, revocations, and privilege boundary, while the existing real-backend integration test proves atomic approval behavior.

**Tech Stack:** Supabase CLI `v2.109.1`, PostgreSQL 17, SQL/PLpgSQL, pgTAP, Windows PowerShell 5.1, Python 3.12.13, psycopg 3.3.4 with `psycopg_pool`, pytest 9.1.1, Ruff, Mypy, local Docker Desktop.

## Global Constraints

- Decision authority: Q-DB-003=A, D-028, ADR-0012.
- Approval evidence: after option A was recommended, the user wrote `이거 끝나면 계속해서 진행해줘. 5시간 동안 루프 ㄱㄱ` on 2026-07-17 KST; record this as approval of the immediately preceding recommendation, not as a literal typed `A`.
- Never edit applied or committed forward migrations `20260716000100` through `20260716000500`.
- Create exactly one new forward migration, one matching compensation, and one pgTAP file.
- Do not grant `app_private` schema or table privileges to `sejong_backend`, browser roles, or PUBLIC.
- Do not add an app_api function, dynamic SQL, function-body rewrite, table/data/seed change, repository/admin-DSN workaround, dependency, public route, remote operation, or DeepSeek call.
- Preserve public HTTP contracts, retention, cost, `/health=200`, and no-seed `/ready=503` behavior.
- Never print DSNs, passwords, keys, Docker credentials, Supabase status payloads, SQL statements, questions, answers, or native database diagnostics.
- Keep every version manifest axis unchanged until DB-001 Task 10.
- Run only against the disposable local PostgreSQL stack; no `link`, `login`, `db push`, remote compensation, volume deletion, or prune.

---

## Plan governance

- Plan ID: `DB-001-T9A-PLAN`
- Status: Approved; implementation pending
- Date: 2026-07-17 KST
- Branch: `codex/db-001-layered-enforcement`
- Worktree: `.worktrees/db-001-layered-enforcement`
- Parent plan: [DB-001 Layered Database Enforcement](2026-07-16-db-001-layered-enforcement.md)
- Decision: [D-028](../../decisions/DECISION_LOG.md), [ADR-0012](../../adr/0012-deferred-active-question-trigger-execution.md)
- Historical evidence: [Task 9 blocker note](../../implementation-notes/IMP-20260717-004-db-001-task-9-deferred-trigger-permission-blocker.md)
- Execution mode: the user already selected agent-driven continuation; use a fresh implementation agent followed by independent specification and quality review.

## File map and ownership

Create during the remediation implementation:

- `supabase/migrations/20260717000600_deferred_active_question_trigger_security.sql` — forward-only function posture correction.
- `database/rollbacks/20260717000600_deferred_active_question_trigger_security.rollback.sql` — local compensation to the `00500` SECURITY INVOKER posture.
- `supabase/tests/database/006_deferred_trigger_security_test.sql` — exact catalog, ACL, trigger, and private-access regression.

Modify only when resuming the already-started Task 9 gate:

- `scripts/verify_database.ps1` — prepend `00600` to the exact compensation list.
- `scripts/tests/test_supabase_tooling.py` — expect six newest-first compensation files in source and behavioral runner tests.
- `apps/api/tests/db/test_integration.py` — remove only the temporary `BACKEND_APPROVAL_BOUNDARY_BLOCKED` diagnostic branch after the success assertions pass; retain safe error wrapping, cleanup, and all eight tests.

Preserve unchanged:

- forward migrations `20260716000100` through `20260716000500`;
- existing compensation `00100` through `00500` and pgTAP files `001` through `005`;
- `apps/api/src`, routes, contracts, dependency/lock files, env templates and real `.env`;
- seed/data, `versions/manifest.json`, `PACKAGE_MANIFEST.json`, remote/public state.

### Interfaces

- Consumes: `app_private.validate_active_kb_question() RETURNS trigger`, owner role `sejong_schema_owner`, deferred triggers `ctrg_kb_documents_require_question` and `ctrg_kb_question_examples_require_active_question`, backend capability role `sejong_backend`.
- Produces: the same function signature and body with `prosecdef=true`, exact `proconfig=ARRAY['search_path=pg_catalog, pg_temp']`, no direct EXECUTE for PUBLIC/anon/authenticated/backend, unchanged exact constraint-trigger bindings, and no backend private privilege.
- Behavioral proof: `test_two_concurrent_approvals_create_one_active_kb_and_audit` returns one public ID plus one safe `P1003` loser and leaves one ACTIVE OFFICIAL KB, one question, one candidate link, and one approval audit.

### Task 1: Correct the deferred trigger execution boundary and finish Task 9

**Files:**

- Create: `supabase/migrations/20260717000600_deferred_active_question_trigger_security.sql`
- Create: `database/rollbacks/20260717000600_deferred_active_question_trigger_security.rollback.sql`
- Create: `supabase/tests/database/006_deferred_trigger_security_test.sql`
- Modify: `scripts/verify_database.ps1`
- Modify: `scripts/tests/test_supabase_tooling.py`
- Modify: `apps/api/tests/db/test_integration.py`

- [ ] **Step 1: Verify scope and snapshot the three pre-existing Task 9 files**

Run:

```powershell
git status --short
git diff --exit-code HEAD -- supabase/migrations/20260716000100_private_schema.sql supabase/migrations/20260716000200_invariants_and_lineage.sql supabase/migrations/20260716000300_capabilities_and_functions.sql supabase/migrations/20260716000400_candidate_workflow.sql supabase/migrations/20260716000500_indexes_and_read_interfaces.sql
git diff --exit-code -- versions/manifest.json PACKAGE_MANIFEST.json contracts
New-Item -ItemType Directory -Force .superpowers\sdd\task-9a-recovery | Out-Null
Copy-Item -LiteralPath scripts\tests\test_supabase_tooling.py -Destination .superpowers\sdd\task-9a-recovery\test_supabase_tooling.py
Copy-Item -LiteralPath scripts\verify_database.ps1 -Destination .superpowers\sdd\task-9a-recovery\verify_database.ps1
Copy-Item -LiteralPath apps\api\tests\db\test_integration.py -Destination .superpowers\sdd\task-9a-recovery\test_integration.py
Get-FileHash -Algorithm SHA256 .superpowers\sdd\task-9a-recovery\test_supabase_tooling.py, .superpowers\sdd\task-9a-recovery\verify_database.ps1, .superpowers\sdd\task-9a-recovery\test_integration.py | ForEach-Object { "$($_.Hash) $([System.IO.Path]::GetFileName($_.Path))" } | Set-Content -Encoding ascii .superpowers\sdd\task-9a-recovery\SHA256SUMS
```

Expected: the first command lists only the existing Task 9 paths
`scripts/tests/test_supabase_tooling.py`, `scripts/verify_database.ps1`, and
`apps/api/tests/db/test_integration.py`; the immutable migrations, versions,
package snapshot, and contracts have no diff. The ignored recovery directory
contains exact copies of all three files—including the untracked integration
file—and a hash manifest. Verify each listed SHA-256 against `Get-FileHash`
before continuing. Stop if any unrelated path is dirty or a hash differs.

- [ ] **Step 2: Reproduce the real backend approval RED before adding `00600`**

Run against the healthy disposable local DB:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_database.ps1 -SkipStart
```

Expected: reset one, current five-file pgTAP 274/274, five-file compensation,
absence proof, reset/replay two, and pgTAP 274/274 pass; the stable
`TEST-DATABASE-INTEGRATION` phase exits 1 because exactly 6 tests pass and the
two approval paths fail through the fixed safe database-unavailable boundary.
No native diagnostic or environment value is public output.

- [ ] **Step 3: Add the pgTAP security contract before production SQL**

Create `supabase/tests/database/006_deferred_trigger_security_test.sql` with
exactly this transaction-scoped catalog test:

```sql
BEGIN;

CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;

SELECT plan(8);

SELECT ok(
  (
    SELECT functions.prosecdef
      AND owners.rolname = 'sejong_schema_owner'
      AND functions.proconfig = ARRAY['search_path=pg_catalog, pg_temp']::text[]
    FROM pg_catalog.pg_proc AS functions
    JOIN pg_catalog.pg_roles AS owners ON owners.oid = functions.proowner
    WHERE functions.oid = pg_catalog.to_regprocedure(
      'app_private.validate_active_kb_question()'
    )
  ),
  'ACTIVE-question validator is schema-owner SECURITY DEFINER with fixed search_path'
);

SELECT results_eq(
  $actual$
    SELECT pg_catalog.format(
      '%I.%I(%s)',
      namespaces.nspname,
      functions.proname,
      pg_catalog.pg_get_function_identity_arguments(functions.oid)
    )::text AS function_identity
    FROM pg_catalog.pg_proc AS functions
    JOIN pg_catalog.pg_namespace AS namespaces
      ON namespaces.oid = functions.pronamespace
    WHERE namespaces.nspname = 'app_private'
      AND functions.prosecdef
    ORDER BY function_identity
  $actual$,
  $expected$
    SELECT expected.function_identity
    FROM (
      VALUES
        ('app_private.validate_active_kb_question()'::text)
    ) AS expected(function_identity)
    ORDER BY expected.function_identity
  $expected$,
  'validator is the sole SECURITY DEFINER among all app_private functions'
);

SELECT is(
  (
    SELECT pg_catalog.count(*)::integer
    FROM pg_catalog.pg_proc AS functions
    CROSS JOIN LATERAL pg_catalog.aclexplode(
      COALESCE(functions.proacl, pg_catalog.acldefault('f', functions.proowner))
    ) AS privileges
    WHERE functions.oid = pg_catalog.to_regprocedure(
      'app_private.validate_active_kb_question()'
    )
      AND privileges.grantee = 0
      AND privileges.privilege_type = 'EXECUTE'
  ),
  0,
  'PUBLIC has no direct EXECUTE on the private trigger validator'
);

SELECT ok(
  NOT pg_catalog.has_function_privilege(
    'anon', 'app_private.validate_active_kb_question()', 'EXECUTE'
  )
  AND NOT pg_catalog.has_function_privilege(
    'authenticated', 'app_private.validate_active_kb_question()', 'EXECUTE'
  )
  AND NOT pg_catalog.has_function_privilege(
    'sejong_backend', 'app_private.validate_active_kb_question()', 'EXECUTE'
  ),
  'browser and backend roles cannot directly execute the private trigger validator'
);

SELECT results_eq(
  $actual$
    SELECT
      namespaces.nspname::text AS schema_name,
      relations.relname::text AS table_name,
      triggers.tgname::text AS trigger_name,
      triggers.tgtype::integer AS trigger_type,
      triggers.tgenabled::text AS enabled,
      triggers.tgdeferrable,
      triggers.tginitdeferred,
      pg_catalog.format(
        '%I.%I(%s)',
        function_namespaces.nspname,
        functions.proname,
        pg_catalog.pg_get_function_identity_arguments(functions.oid)
      )::text AS function_identity,
      pg_catalog.pg_get_triggerdef(triggers.oid)::text AS trigger_definition
    FROM pg_catalog.pg_trigger AS triggers
    JOIN pg_catalog.pg_class AS relations ON relations.oid = triggers.tgrelid
    JOIN pg_catalog.pg_namespace AS namespaces
      ON namespaces.oid = relations.relnamespace
    JOIN pg_catalog.pg_proc AS functions ON functions.oid = triggers.tgfoid
    JOIN pg_catalog.pg_namespace AS function_namespaces
      ON function_namespaces.oid = functions.pronamespace
    WHERE NOT triggers.tgisinternal
      AND triggers.tgfoid = pg_catalog.to_regprocedure(
        'app_private.validate_active_kb_question()'
      )
    ORDER BY schema_name, table_name, trigger_name
  $actual$,
  $expected$
    SELECT
      expected.schema_name,
      expected.table_name,
      expected.trigger_name,
      expected.trigger_type,
      expected.enabled,
      expected.tgdeferrable,
      expected.tginitdeferred,
      expected.function_identity,
      expected.trigger_definition
    FROM (
      VALUES
        (
          'app_private'::text,
          'kb_documents'::text,
          'ctrg_kb_documents_require_question'::text,
          21::integer,
          'O'::text,
          true,
          true,
          'app_private.validate_active_kb_question()'::text,
          'CREATE CONSTRAINT TRIGGER ctrg_kb_documents_require_question AFTER INSERT OR UPDATE ON app_private.kb_documents DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION app_private.validate_active_kb_question()'::text
        ),
        (
          'app_private'::text,
          'kb_question_examples'::text,
          'ctrg_kb_question_examples_require_active_question'::text,
          29::integer,
          'O'::text,
          true,
          true,
          'app_private.validate_active_kb_question()'::text,
          'CREATE CONSTRAINT TRIGGER ctrg_kb_question_examples_require_active_question AFTER INSERT OR DELETE OR UPDATE ON app_private.kb_question_examples DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION app_private.validate_active_kb_question()'::text
        )
    ) AS expected(
      schema_name,
      table_name,
      trigger_name,
      trigger_type,
      enabled,
      tgdeferrable,
      tginitdeferred,
      function_identity,
      trigger_definition
    )
    ORDER BY expected.schema_name, expected.table_name, expected.trigger_name
  $expected$,
  'both ACTIVE-question triggers retain exact table, event, row, deferred, and function bindings'
);

SELECT ok(
  NOT pg_catalog.has_schema_privilege('sejong_backend', 'app_private', 'USAGE'),
  'backend retains no app_private schema usage'
);

SELECT is(
  (
    SELECT pg_catalog.count(*)::integer
    FROM pg_catalog.pg_class AS relations
    JOIN pg_catalog.pg_namespace AS namespaces
      ON namespaces.oid = relations.relnamespace
    CROSS JOIN pg_catalog.unnest(
      ARRAY[
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE',
        'REFERENCES', 'TRIGGER', 'MAINTAIN'
      ]::text[]
    ) AS requested(privilege_name)
    WHERE namespaces.nspname = 'app_private'
      AND relations.relkind IN ('r', 'p')
      AND pg_catalog.has_table_privilege(
        'sejong_backend', relations.oid, requested.privilege_name
      )
  ),
  0,
  'backend retains no effective privilege on any private base or partitioned table'
);

SELECT ok(
  (
    SELECT pg_catalog.md5(functions.prosrc) =
      '6014f41ed693231e30a9369dd0e394a4'
      AND functions.prosrc !~* '\mEXECUTE\M'
      AND functions.prosrc LIKE '%FROM app_private.kb_documents%'
      AND functions.prosrc LIKE '%FROM app_private.kb_question_examples%'
    FROM pg_catalog.pg_proc AS functions
    WHERE functions.oid = pg_catalog.to_regprocedure(
      'app_private.validate_active_kb_question()'
    )
  ),
  'validator body fingerprint and schema-qualified static SQL remain unchanged'
);

SELECT * FROM finish();

ROLLBACK;
```

- [ ] **Step 4: Change the runner expectation before the runner**

In both exact rollback lists in `scripts/tests/test_supabase_tooling.py`, use
this newest-first sequence and change nothing else:

```python
[
    "20260717000600_deferred_active_question_trigger_security.rollback.sql",
    "20260716000500_indexes_and_read_interfaces.rollback.sql",
    "20260716000400_candidate_workflow.rollback.sql",
    "20260716000300_capabilities_and_functions.rollback.sql",
    "20260716000200_invariants_and_lineage.rollback.sql",
    "20260716000100_private_schema.rollback.sql",
]
```

The behavioral full-path invocation list must prepend the same `00600` filename
inside its single `['sql', ...]` entry.

- [ ] **Step 5: Run both focused RED checks**

Run:

```powershell
.\.tools\supabase\v2.109.1\supabase.exe test db supabase/tests/database/006_deferred_trigger_security_test.sql
apps\api\.venv\Scripts\python.exe -B -m unittest scripts.tests.test_supabase_tooling.LocalDatabaseToolingContractTests.test_database_runner_uses_exact_newest_first_compensation_order scripts.tests.test_supabase_tooling.LocalDatabaseToolingContractTests.test_database_runner_full_path_orders_replay_and_restores_environment
```

Expected: the pgTAP command is nonzero because the validator is still SECURITY
INVOKER; the two tooling tests are nonzero because the runner still has only five
compensation paths. Preserve the exact failure counts in the Task 9 report and do
not weaken any assertion.

- [ ] **Step 6: Add the minimal forward migration**

Create `supabase/migrations/20260717000600_deferred_active_question_trigger_security.sql`
with exactly:

```sql
BEGIN;

ALTER FUNCTION app_private.validate_active_kb_question()
  SECURITY DEFINER;
ALTER FUNCTION app_private.validate_active_kb_question()
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_private.validate_active_kb_question()
  SET search_path = pg_catalog, pg_temp;
REVOKE ALL ON FUNCTION app_private.validate_active_kb_question()
  FROM PUBLIC, anon, authenticated, sejong_backend;

COMMIT;
```

Verify this exact PostgreSQL 17 syntax through the pinned local reset and focused
pgTAP command. Do not add a function body, grant, table/data statement, or a
second changed function.

- [ ] **Step 7: Add the exact matching compensation**

Create
`database/rollbacks/20260717000600_deferred_active_question_trigger_security.rollback.sql`
with exactly:

```sql
BEGIN;

ALTER FUNCTION app_private.validate_active_kb_question()
  SECURITY INVOKER;
ALTER FUNCTION app_private.validate_active_kb_question()
  OWNER TO sejong_schema_owner;
ALTER FUNCTION app_private.validate_active_kb_question()
  SET search_path = pg_catalog, pg_temp;
REVOKE ALL ON FUNCTION app_private.validate_active_kb_question()
  FROM PUBLIC, anon, authenticated, sejong_backend;

COMMIT;
```

Expected: compensation changes only `prosecdef` back to false and preserves owner,
search path, revocations, function body, triggers, tables, and data.

- [ ] **Step 8: Reset and run the new pgTAP GREEN**

Run:

```powershell
.\.tools\supabase\v2.109.1\supabase.exe db reset --local
.\.tools\supabase\v2.109.1\supabase.exe test db supabase/tests/database/006_deferred_trigger_security_test.sql
.\.tools\supabase\v2.109.1\supabase.exe test db
```

Expected: reset and focused pgTAP exit 0. Full pgTAP exits 0 with six files; copy
the emitted `Files` and `Tests` totals into the Task 9 report after the command
returns instead of predicting a new assertion total.

- [ ] **Step 9: Prove `00600`-only compensation and the exact `00500` baseline**

In one PowerShell process, capture the local status payload in memory, set the
admin URL only for child processes, apply the compensation, and print only stable
verdicts:

```powershell
$statusOutput = & .\.tools\supabase\v2.109.1\supabase.exe status -o env 2>$null
if ($LASTEXITCODE -ne 0) { throw "LOCAL_DATABASE_STATUS_FAILED" }
$assignment = $statusOutput | Where-Object {
    $_.StartsWith("DB_URL=", [System.StringComparison]::Ordinal)
} | Select-Object -First 1
if ($null -eq $assignment) { throw "LOCAL_DATABASE_URL_MISSING" }
$databaseUrl = $assignment.Substring(7).Trim().Trim('"')
$saved = [Environment]::GetEnvironmentVariable("SEJONG_ADMIN_DATABASE_URL", "Process")
try {
    [Environment]::SetEnvironmentVariable(
        "SEJONG_ADMIN_DATABASE_URL", $databaseUrl, "Process"
    )
    & apps\api\.venv\Scripts\python.exe -B scripts\run_database_sql.py database\rollbacks\20260717000600_deferred_active_question_trigger_security.rollback.sql
    if ($LASTEXITCODE -ne 0) { throw "TASK9A_COMPENSATION_FAILED" }
    @'
import os
import psycopg

try:
    with psycopg.connect(os.environ["SEJONG_ADMIN_DATABASE_URL"]) as connection:
        row = connection.execute(
            """
            WITH target AS (
              SELECT functions.*, owners.rolname AS owner_name
              FROM pg_catalog.pg_proc AS functions
              JOIN pg_catalog.pg_roles AS owners
                ON owners.oid = functions.proowner
              WHERE functions.oid = pg_catalog.to_regprocedure(
                'app_private.validate_active_kb_question()'
              )
            )
            SELECT COALESCE((
              SELECT
                NOT target.prosecdef
                AND target.owner_name = 'sejong_schema_owner'
                AND target.proconfig =
                  ARRAY['search_path=pg_catalog, pg_temp']::text[]
                AND pg_catalog.md5(target.prosrc) =
                  '6014f41ed693231e30a9369dd0e394a4'
                AND NOT EXISTS (
                  SELECT 1
                  FROM pg_catalog.pg_proc AS functions
                  JOIN pg_catalog.pg_namespace AS namespaces
                    ON namespaces.oid = functions.pronamespace
                  WHERE namespaces.nspname = 'app_private'
                    AND functions.prosecdef
                )
                AND 0 = (
                  SELECT pg_catalog.count(*)
                  FROM pg_catalog.aclexplode(
                    COALESCE(
                      target.proacl,
                      pg_catalog.acldefault('f', target.proowner)
                    )
                  ) AS privileges
                  WHERE privileges.grantee = 0
                    AND privileges.privilege_type = 'EXECUTE'
                )
                AND NOT pg_catalog.has_function_privilege(
                  'anon', 'app_private.validate_active_kb_question()', 'EXECUTE'
                )
                AND NOT pg_catalog.has_function_privilege(
                  'authenticated',
                  'app_private.validate_active_kb_question()',
                  'EXECUTE'
                )
                AND NOT pg_catalog.has_function_privilege(
                  'sejong_backend',
                  'app_private.validate_active_kb_question()',
                  'EXECUTE'
                )
                AND NOT EXISTS (
                  (
                    SELECT
                      namespaces.nspname::text,
                      relations.relname::text,
                      triggers.tgname::text,
                      triggers.tgtype::integer,
                      triggers.tgenabled::text,
                      triggers.tgdeferrable,
                      triggers.tginitdeferred,
                      pg_catalog.pg_get_triggerdef(triggers.oid)::text
                    FROM pg_catalog.pg_trigger AS triggers
                    JOIN pg_catalog.pg_class AS relations
                      ON relations.oid = triggers.tgrelid
                    JOIN pg_catalog.pg_namespace AS namespaces
                      ON namespaces.oid = relations.relnamespace
                    WHERE NOT triggers.tgisinternal
                      AND triggers.tgfoid = target.oid
                    EXCEPT
                    SELECT * FROM (
                      VALUES
                        (
                          'app_private'::text,
                          'kb_documents'::text,
                          'ctrg_kb_documents_require_question'::text,
                          21::integer,
                          'O'::text,
                          true,
                          true,
                          'CREATE CONSTRAINT TRIGGER ctrg_kb_documents_require_question AFTER INSERT OR UPDATE ON app_private.kb_documents DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION app_private.validate_active_kb_question()'::text
                        ),
                        (
                          'app_private'::text,
                          'kb_question_examples'::text,
                          'ctrg_kb_question_examples_require_active_question'::text,
                          29::integer,
                          'O'::text,
                          true,
                          true,
                          'CREATE CONSTRAINT TRIGGER ctrg_kb_question_examples_require_active_question AFTER INSERT OR DELETE OR UPDATE ON app_private.kb_question_examples DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION app_private.validate_active_kb_question()'::text
                        )
                    ) AS expected(
                      schema_name,
                      table_name,
                      trigger_name,
                      trigger_type,
                      enabled,
                      tgdeferrable,
                      tginitdeferred,
                      trigger_definition
                    )
                  )
                  UNION ALL
                  (
                    SELECT * FROM (
                      VALUES
                        (
                          'app_private'::text,
                          'kb_documents'::text,
                          'ctrg_kb_documents_require_question'::text,
                          21::integer,
                          'O'::text,
                          true,
                          true,
                          'CREATE CONSTRAINT TRIGGER ctrg_kb_documents_require_question AFTER INSERT OR UPDATE ON app_private.kb_documents DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION app_private.validate_active_kb_question()'::text
                        ),
                        (
                          'app_private'::text,
                          'kb_question_examples'::text,
                          'ctrg_kb_question_examples_require_active_question'::text,
                          29::integer,
                          'O'::text,
                          true,
                          true,
                          'CREATE CONSTRAINT TRIGGER ctrg_kb_question_examples_require_active_question AFTER INSERT OR DELETE OR UPDATE ON app_private.kb_question_examples DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION app_private.validate_active_kb_question()'::text
                        )
                    ) AS expected(
                      schema_name,
                      table_name,
                      trigger_name,
                      trigger_type,
                      enabled,
                      tgdeferrable,
                      tginitdeferred,
                      trigger_definition
                    )
                    EXCEPT
                    SELECT
                      namespaces.nspname::text,
                      relations.relname::text,
                      triggers.tgname::text,
                      triggers.tgtype::integer,
                      triggers.tgenabled::text,
                      triggers.tgdeferrable,
                      triggers.tginitdeferred,
                      pg_catalog.pg_get_triggerdef(triggers.oid)::text
                    FROM pg_catalog.pg_trigger AS triggers
                    JOIN pg_catalog.pg_class AS relations
                      ON relations.oid = triggers.tgrelid
                    JOIN pg_catalog.pg_namespace AS namespaces
                      ON namespaces.oid = relations.relnamespace
                    WHERE NOT triggers.tgisinternal
                      AND triggers.tgfoid = target.oid
                  )
                )
                AND NOT pg_catalog.has_schema_privilege(
                  'sejong_backend', 'app_private', 'USAGE'
                )
                AND 0 = (
                  SELECT pg_catalog.count(*)
                  FROM pg_catalog.pg_class AS relations
                  JOIN pg_catalog.pg_namespace AS namespaces
                    ON namespaces.oid = relations.relnamespace
                  CROSS JOIN pg_catalog.unnest(
                    ARRAY[
                      'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE',
                      'REFERENCES', 'TRIGGER', 'MAINTAIN'
                    ]::text[]
                  ) AS requested(privilege_name)
                  WHERE namespaces.nspname = 'app_private'
                    AND relations.relkind IN ('r', 'p')
                    AND pg_catalog.has_table_privilege(
                      'sejong_backend', relations.oid, requested.privilege_name
                    )
                )
              FROM target
            ), false)
            """
        ).fetchone()
except Exception:
    raise SystemExit("TASK9A_COMPENSATION_POSTURE_FAILED") from None
if row != (True,):
    raise SystemExit("TASK9A_COMPENSATION_POSTURE_FAILED")
print("TASK9A-COMPENSATION-POSTURE PASS")
'@ | apps\api\.venv\Scripts\python.exe -B -
    if ($LASTEXITCODE -ne 0) { throw "TASK9A_COMPENSATION_POSTURE_FAILED" }
}
finally {
    [Environment]::SetEnvironmentVariable(
        "SEJONG_ADMIN_DATABASE_URL", $saved, "Process"
    )
}
```

Then run all five pre-006 pgTAP files in one CLI invocation:

```powershell
.\.tools\supabase\v2.109.1\supabase.exe test db supabase/tests/database/001_schema_test.sql supabase/tests/database/002_invariants_test.sql supabase/tests/database/003_capabilities_test.sql supabase/tests/database/004_approval_test.sql supabase/tests/database/005_citizen_reads_test.sql
```

Expected: the stable compensation posture verdict passes and the single baseline
invocation reports `Files=5, Tests=274`. The new 006 test is intentionally not
run against the compensated posture.

- [ ] **Step 10: Restore the six-migration state and update the runner**

Run reset once, then prepend the new compensation path in
`scripts/verify_database.ps1` without changing phase names or output behavior:

```powershell
.\.tools\supabase\v2.109.1\supabase.exe db reset --local
```

The runner block must be exactly:

```powershell
$rollbackFiles = @(
    (Join-Path $repositoryRoot "database\rollbacks\20260717000600_deferred_active_question_trigger_security.rollback.sql"),
    (Join-Path $repositoryRoot "database\rollbacks\20260716000500_indexes_and_read_interfaces.rollback.sql"),
    (Join-Path $repositoryRoot "database\rollbacks\20260716000400_candidate_workflow.rollback.sql"),
    (Join-Path $repositoryRoot "database\rollbacks\20260716000300_capabilities_and_functions.rollback.sql"),
    (Join-Path $repositoryRoot "database\rollbacks\20260716000200_invariants_and_lineage.rollback.sql"),
    (Join-Path $repositoryRoot "database\rollbacks\20260716000100_private_schema.rollback.sql")
)
```

- [ ] **Step 11: Prove approval GREEN before and after removing the temporary branch**

First retain the temporary `BACKEND_APPROVAL_BOUNDARY_BLOCKED` diagnostic branch
and run the six-migration integration gate without another compensation replay:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_database.ps1 -SkipStart -SkipRollbackReplay
```

Expected: pgTAP passes, real integration is exactly 8/8, both approval assertions
pass, and the temporary blocker branch is not reached. Do not delete that branch
on catalog evidence alone.

In `test_two_concurrent_approvals_create_one_active_kb_and_audit`, replace the
temporary block beginning with `if any(` and ending in
`BACKEND_APPROVAL_BOUNDARY_BLOCKED` with this stable assertion:

```python
assert not any(
    isinstance(result, BaseException) and not isinstance(result, DatabaseRuleError)
    for result in results
), "UNEXPECTED_BACKEND_APPROVAL_ERROR"
```

Retain `_backend`, identifier-scoped cleanup, one-success/one-`P1003` assertions,
ACTIVE OFFICIAL KB/question/link/audit assertions, and all seven other integration
tests unchanged.

Rerun the same command after that single removal:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_database.ps1 -SkipStart -SkipRollbackReplay
```

Expected: the post-removal gate remains exactly 8/8 with the same one-success,
one-safe-`P1003`, one-KB/question/link/audit proof.

- [ ] **Step 12: Run focused tooling, formatting, and typing GREEN**

Run:

```powershell
apps\api\.venv\Scripts\python.exe -B -m unittest scripts.tests.test_supabase_tooling.LocalDatabaseToolingContractTests
.\.tools\uv\uv.exe run --directory apps/api --frozen ruff format --check src tests
.\.tools\uv\uv.exe run --directory apps/api --frozen ruff check src tests
.\.tools\uv\uv.exe run --directory apps/api --frozen mypy src tests
```

Expected: all 16 tooling tests, Ruff formatting/lint, and strict Mypy pass.

- [ ] **Step 13: Run the complete six-stage disposable DB gate**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_database.ps1 -SkipStart
```

Expected stable phases all pass: reset one, six-file full pgTAP, compensation
`00600 → 00500 → 00400 → 00300 → 00200 → 00100`, DB-001 absence, reset/replay
two, full pgTAP again, and exactly 8/8 integration tests. Concurrent approval
must leave one successful public ID, one safe `P1003` loser, one ACTIVE OFFICIAL
KB, one required question, one candidate link, one approval audit, and no native
diagnostic in public output.

- [ ] **Step 14: Run the no-Docker root regression and safety gates**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1
apps\api\.venv\Scripts\python.exe -B scripts\validate_codex_package.py
git diff --check
git diff --exit-code -- PACKAGE_MANIFEST.json versions/manifest.json contracts apps/api/pyproject.toml apps/api/uv.lock supabase/seed.sql
git diff --exit-code HEAD -- supabase/migrations/20260716000100_private_schema.sql supabase/migrations/20260716000200_invariants_and_lineage.sql supabase/migrations/20260716000300_capabilities_and_functions.sql supabase/migrations/20260716000400_candidate_workflow.sql supabase/migrations/20260716000500_indexes_and_read_interfaces.sql
git status --short
```

Then prove the eight synthetic tables are empty without printing row content or
connection information:

```powershell
$statusOutput = & .\.tools\supabase\v2.109.1\supabase.exe status -o env 2>$null
if ($LASTEXITCODE -ne 0) { throw "LOCAL_DATABASE_STATUS_FAILED" }
$assignment = $statusOutput | Where-Object {
    $_.StartsWith("DB_URL=", [System.StringComparison]::Ordinal)
} | Select-Object -First 1
if ($null -eq $assignment) { throw "LOCAL_DATABASE_URL_MISSING" }
$databaseUrl = $assignment.Substring(7).Trim().Trim('"')
$saved = [Environment]::GetEnvironmentVariable("SEJONG_ADMIN_DATABASE_URL", "Process")
try {
    [Environment]::SetEnvironmentVariable(
        "SEJONG_ADMIN_DATABASE_URL", $databaseUrl, "Process"
    )
    @'
import os
import psycopg

try:
    with psycopg.connect(os.environ["SEJONG_ADMIN_DATABASE_URL"]) as connection:
        row = connection.execute(
            """
            SELECT
              (SELECT pg_catalog.count(*) FROM app_private.interaction_events) = 0
              AND (SELECT pg_catalog.count(*) FROM app_private.failed_questions) = 0
              AND (SELECT pg_catalog.count(*) FROM app_private.kb_candidates) = 0
              AND (SELECT pg_catalog.count(*) FROM app_private.kb_documents) = 0
              AND (SELECT pg_catalog.count(*) FROM app_private.kb_question_examples) = 0
              AND (SELECT pg_catalog.count(*) FROM app_private.offices) = 0
              AND (SELECT pg_catalog.count(*) FROM app_private.office_service_mappings) = 0
              AND (SELECT pg_catalog.count(*) FROM app_private.audit_logs) = 0
            """
        ).fetchone()
except Exception:
    raise SystemExit("TASK9A_SYNTHETIC_ROWS_FAILED") from None
if row != (True,):
    raise SystemExit("TASK9A_SYNTHETIC_ROWS_FAILED")
print("TASK9A-SYNTHETIC-ROWS PASS")
'@ | apps\api\.venv\Scripts\python.exe -B -
    if ($LASTEXITCODE -ne 0) { throw "TASK9A_SYNTHETIC_ROWS_FAILED" }
}
finally {
    [Environment]::SetEnvironmentVariable(
        "SEJONG_ADMIN_DATABASE_URL", $saved, "Process"
    )
}
```

Expected: root gate exits 0 without starting Docker; secret/package/diff checks
pass; version/package/contract/dependency/seed and five immutable migrations have
no diff. Status contains only the three new remediation files and the three
authorized Task 9 files. The final probe prints only
`TASK9A-SYNTHETIC-ROWS PASS` after proving all eight table counts are zero.

- [ ] **Step 15: Commit the remediation and resumed Task 9 in two exact commits**

First commit only the new migration, compensation, and pgTAP file:

```powershell
git add supabase/migrations/20260717000600_deferred_active_question_trigger_security.sql database/rollbacks/20260717000600_deferred_active_question_trigger_security.rollback.sql supabase/tests/database/006_deferred_trigger_security_test.sql
git commit -m "fix(db): secure deferred active question trigger"
```

Then commit only the already-started Task 9 runner/integration files:

```powershell
git add scripts/verify_database.ps1 scripts/tests/test_supabase_tooling.py apps/api/tests/db/test_integration.py
git commit -m "test(db): verify rollback replay and concurrent approval"
```

Expected: each commit contains exactly three paths; no documentation, version,
contract, env, data, dependency, or immutable migration path is staged.

## Independent review checkpoint

After both implementation commits, invoke `superpowers:requesting-code-review`
twice with fresh reviewers.

Specification review must prove:

- D-028/ADR-0012 exact A boundary and no B/grant/repository workaround;
- only `validate_active_kb_question()` changes posture;
- exact six-stage compensation and immutable `00100`~`00500`;
- pgTAP contract, compensation baseline, real 8/8 integration, root gate, and
  zero synthetic rows.

Quality/security review must inspect PostgreSQL 17 syntax, owner/search path,
ACL effectiveness, function-body immutability, trigger deferral, RLS/grants,
transaction rollback, concurrency, diagnostic privacy, runner environment
restoration, compensation scope, and secret output. Resolve every Critical or
Important finding and rerun Steps 8 through 14. Do not mark the plan complete
from review alone.

## Documentation closeout checkpoint

Only after the implementation, verification, and both reviews pass:

1. Record actual pgTAP totals, 8/8 integration, six-file compensation, review
   findings, commit IDs, and zero-row cleanup in
   `docs/implementation-notes/IMP-20260716-006-db-001-layered-enforcement.md`,
   `docs/implementation-notes/IMP-20260717-004-db-001-task-9-deferred-trigger-permission-blocker.md`,
   and `docs/implementation-notes/IMP-20260717-005-q-db-003-a-decision-and-deferred-trigger-remediation-plan.md`.
2. Check the completed steps in this plan and then the parent Task 9 steps; do
   not mark DB-001 Done until Task 10 evidence passes.
3. Change `TASKS.md` from remediation in progress to Task 9 complete/Task 10
   ready and synchronize `docs/implementation-notes/INDEX.md`.
4. Keep `versions/manifest.json` unchanged. Task 10 owns repo guidance, DB schema,
   test-suite, and documentation version promotion.
5. Validate links, placeholders, secret patterns, package snapshot, staged scope,
   and `git diff --check`.
6. Stage exactly these closeout paths—no migration, runner, test, version,
   contract, env, data, dependency, or other document:

```powershell
git add -- docs/adr/0012-deferred-active-question-trigger-execution.md docs/decisions/DECISION_LOG.md docs/superpowers/specs/2026-07-16-db-001-layered-enforcement-design.md docs/superpowers/plans/2026-07-16-db-001-layered-enforcement.md docs/superpowers/plans/2026-07-17-db-001-deferred-trigger-security-fix.md TASKS.md docs/implementation-notes/IMP-20260716-006-db-001-layered-enforcement.md docs/implementation-notes/IMP-20260717-004-db-001-task-9-deferred-trigger-permission-blocker.md docs/implementation-notes/IMP-20260717-005-q-db-003-a-decision-and-deferred-trigger-remediation-plan.md docs/implementation-notes/INDEX.md
git diff --cached --name-only
git commit -m "docs(db): close deferred trigger remediation"
```

Expected: the staged-name output contains exactly the ten listed paths and the
commit succeeds with exactly those paths.

## Remaining risk outside `00600`

Ambiguity A-021 is deliberately not implemented here. The local catalog shows
all nine existing `app_api` SECURITY DEFINER functions still use
`proconfig=['search_path=pg_catalog']`, while `sejong_backend` has effective
database TEMP. No exploit was reproduced. Before public deployment, investigate
their bodies, ACLs, and call behavior and obtain human approval for any separate
forward-migration hardening. D-028 and this plan authorize only the deferred
validator posture correction.

## Rollback and recovery

- Before either implementation commit, verify and restore the exact Step 1
  snapshot rather than approximating the prior dirty state:

```powershell
$recoveryRoot = (Resolve-Path -LiteralPath .superpowers\sdd\task-9a-recovery).Path
$expected = @{}
Get-Content -LiteralPath (Join-Path $recoveryRoot 'SHA256SUMS') | ForEach-Object {
    $parts = $_ -split ' ', 2
    if ($parts.Count -ne 2) { throw 'TASK9A_RECOVERY_MANIFEST_INVALID' }
    $expected[$parts[1]] = $parts[0]
}
$destinations = @{
    'test_supabase_tooling.py' = 'scripts\tests\test_supabase_tooling.py'
    'verify_database.ps1' = 'scripts\verify_database.ps1'
    'test_integration.py' = 'apps\api\tests\db\test_integration.py'
}
foreach ($name in $destinations.Keys) {
    $source = Join-Path $recoveryRoot $name
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $source).Hash -ne $expected[$name]) {
        throw 'TASK9A_RECOVERY_SNAPSHOT_HASH_FAILED'
    }
    Copy-Item -Force -LiteralPath $source -Destination $destinations[$name]
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $destinations[$name]).Hash -ne $expected[$name]) {
        throw 'TASK9A_RECOVERY_RESTORE_HASH_FAILED'
    }
}
Remove-Item -LiteralPath supabase\migrations\20260717000600_deferred_active_question_trigger_security.sql, database\rollbacks\20260717000600_deferred_active_question_trigger_security.rollback.sql, supabase\tests\database\006_deferred_trigger_security_test.sql -ErrorAction SilentlyContinue
```

  Do not touch `00100`~`00500`.
- After the first commit on disposable local DB: run the `00600` compensation,
  prove `prosecdef=false`, and rerun the five prior pgTAP files for 274/274.
- After both commits: `git revert` the Task 9 commit first and remediation commit
  second, then reset/replay the local DB. Never rewrite a shared migration.
- After a shared `00600` requires correction: add a new reviewed forward migration;
  do not edit `00600`.
- Remote compensation, actual-data deletion, public deployment, credential policy,
  and Docker volume deletion remain separate human approval gates.

## Target completion criteria

- [ ] Q-DB-003 remains resolved by D-028/ADR-0012.
- [ ] Six immutable forward migrations and six local compensation files are verified.
- [ ] Backend private schema/table grants remain zero.
- [ ] Real integration is 8/8 and concurrent approval is atomic.
- [ ] Task 9 is complete and Task 10 is ready, while DB-001 and manifest versions
  remain incomplete until Task 10.
