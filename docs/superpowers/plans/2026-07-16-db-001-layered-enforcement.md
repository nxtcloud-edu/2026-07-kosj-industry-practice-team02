# DB-001 Layered Database Enforcement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a checksum-pinned, locally reproducible Supabase/PostgreSQL baseline that enforces privacy, provenance, approval, retention, citizen-read, and backend-only capability rules in both the database and a lazy FastAPI repository boundary.

**Architecture:** Business tables and enums live in non-exposed `app_private`; only reviewed capability functions in `app_api` are directly executable by the NOLOGIN `sejong_backend` role. Five committed migrations remain immutable, and the approved Task 9A adds a sixth forward/compensation stage that changes only the deferred ACTIVE-question validator posture. All six stages are tested with pgTAP, Python integration tests, and reset/rollback/replay, while the FastAPI process keeps database I/O lazy and adds no public routes or wire-contract changes.

**Tech Stack:** Supabase CLI `v2.109.1`, PostgreSQL 17, SQL/PLpgSQL, pgTAP, Windows PowerShell 5.1, Python 3.12.13, psycopg 3.3.4 with `psycopg_pool`, pytest 9.1.1, existing local Docker Desktop.

---

## Plan governance

- Plan ID: `DB-001-PLAN`
- Status: Completed for disposable local/private use — Tasks 0~10, remediation, final-code DB gate, final reviews, final verification and closeout commit complete
- User approval: `계획 승인, 구현 시작` on 2026-07-16 KST
- Execution branch: `codex/db-001-layered-enforcement`
- Execution worktree: `.worktrees/db-001-layered-enforcement`
- Approved specification: `docs/superpowers/specs/2026-07-16-db-001-layered-enforcement-design.md`
- Decisions: D-018, D-025, D-026, D-027, D-028, D-029, D-030, D-031
- ADRs: ADR-0003, ADR-0004, ADR-0007, ADR-0008, ADR-0011, ADR-0012, ADR-0013
- Task 9A remediation plan: `docs/superpowers/plans/2026-07-17-db-001-deferred-trigger-security-fix.md`
- Task 10 patched CLI plan: `docs/superpowers/plans/2026-07-17-q-sec-006-patched-supabase-cli.md` (amendment approved; implementation, actual gate, reviews and final verification complete)
- Logical projection: `database/schema-v1.draft.sql` describes the active local `0.3.0-local` baseline; executable authority remains timestamp migrations
- Achieved local/private target: `database_schema=0.3.0-local`, `repo_guidance=1.5.0`, `test_suite=0.5.0-db-baseline`
- Execution gate: no task below starts until the user explicitly approves this plan.
- Execution mode: the user's recorded preference makes subagent-driven development the default. A fresh implementation agent handles one task, then specification and code-quality review occur before the next task.
- Scope guard: no official seed, DeepSeek call, public route, readiness 200 transition, remote link/push, cloud resource, production auth, or new production dependency is authorized.

## Verified external tool pin

The plan pins the current official stable GitHub release observed on 2026-07-16 KST:

```json
{
  "release": "v2.109.1",
  "published_at": "2026-07-07T09:00:28Z",
  "asset": "supabase_2.109.1_windows_amd64.zip",
  "url": "https://github.com/supabase/cli/releases/download/v2.109.1/supabase_2.109.1_windows_amd64.zip",
  "sha256": "d0d270692cf78b8aa56545461f02cdf929ce9bb94e95e5e66404fd0e7d2c0c16"
}
```

At execution, Task 1 rechecks that the release is still an official non-prerelease asset and that the downloaded bytes match this digest. A changed upstream release does not silently alter the pin; changing it requires a reviewed manifest patch.

## Authoritative file map

### Local tooling

| Path | Responsibility |
|---|---|
| `scripts/supabase-cli.version.json` | Exact official CLI release, Windows asset URL, size, and SHA-256 |
| `scripts/bootstrap_supabase.ps1` | Verify or download the pinned archive, validate digest, extract into ignored `.tools/supabase/v2.109.1/`, print stable non-secret status only |
| `scripts/provision_local_database_login.py` | Create/rotate one local login that is a member of `sejong_backend`; update only `DATABASE_URL` in ignored `apps/api/.env` while preserving every other line |
| `scripts/run_database_sql.py` | Execute a reviewed ordered SQL file list using an admin DSN supplied only through process environment; never print DSN or SQL values |
| `scripts/verify_database.ps1` | Explicit Docker-required start → reset → provision → pgTAP → rollback → absence check → replay → pgTAP → Python integration gate |
| `scripts/tests/test_supabase_tooling.py` | Standard-library tests for pin, checksum behavior, stable output, ignore rules, local-only command allowlist, and env preservation helper |
| `supabase/config.toml` | CLI-generated v2.109.1 local config with only PostgreSQL enabled and no application schema exposed through Data API |
| `supabase/seed.sql` | Tracked, intentionally data-free file explaining that DATA-SEED-001 owns official/mock seed |

### Database lineage

| Forward migration | Compensation file | Responsibility |
|---|---|---|
| `supabase/migrations/20260716000100_private_schema.sql` | `database/rollbacks/20260716000100_private_schema.rollback.sql` | Schemas, seven enums, eight tables |
| `supabase/migrations/20260716000200_invariants_and_lineage.sql` | `database/rollbacks/20260716000200_invariants_and_lineage.rollback.sql` | JSON/text/state checks, updated-at and ACTIVE-question constraint triggers |
| `supabase/migrations/20260716000300_capabilities_and_functions.sql` | `database/rollbacks/20260716000300_capabilities_and_functions.rollback.sql` | Roles, ownership, forced RLS, event/failure recording, retention functions |
| `supabase/migrations/20260716000400_candidate_workflow.sql` | `database/rollbacks/20260716000400_candidate_workflow.rollback.sql` | Failure-reason confirmation, candidate workflow, approval/rejection, audit refinement |
| `supabase/migrations/20260716000500_indexes_and_read_interfaces.sql` | `database/rollbacks/20260716000500_indexes_and_read_interfaces.rollback.sql` | Five indexes and ACTIVE+OFFICIAL KB/office read functions |
| `supabase/migrations/20260717000600_deferred_active_question_trigger_security.sql` | `database/rollbacks/20260717000600_deferred_active_question_trigger_security.rollback.sql` | Validator-only SECURITY DEFINER posture correction and matching INVOKER compensation |
| `database/verify_db001_absent.sql` | none | After compensation, assert DB-001 schemas and roles are absent without touching Supabase-owned objects |

### Tests

| Path | Responsibility |
|---|---|
| `supabase/tests/database/001_schema_test.sql` | Exact schemas, enums, tables, columns, generated provenance field, forbidden privacy fields |
| `supabase/tests/database/002_invariants_test.sql` | JSON arrays, text/state/provenance, event/failure linkage, ACTIVE question constraint |
| `scripts/test_database_concurrency.py` | Two-connection isolation probes for ACTIVE-question, event/failure, and failure/candidate stale-snapshot races |
| `supabase/tests/database/003_capabilities_test.sql` | Function signatures, fixed search paths, RLS, grants, event/failure behavior, retention |
| `supabase/tests/database/004_approval_test.sql` | Role/state/self-approval/source completeness, atomic activation, append-only audit |
| `supabase/tests/database/005_citizen_reads_test.sql` | ACTIVE+OFFICIAL visibility and rejection of mock/draft/pending/retired records |
| `apps/api/tests/db/test_errors.py` | Stable SQLSTATE to typed domain-error mapping |
| `apps/api/tests/db/test_models.py` | Backend-side role/state/provenance and privacy validation |
| `apps/api/tests/db/test_repository.py` | Exact parameterized SQL calls, transaction behavior, no import-time I/O |
| `apps/api/tests/db/test_integration.py` | Local DB idempotency, concurrent approval, purge boundary, role denial; skipped unless `SEJONG_DB_TEST_URL` is present |

### FastAPI internal boundary

| Path | Responsibility |
|---|---|
| `apps/api/src/sejong_ai_api/db/__init__.py` | Export internal DB types only; no pool creation |
| `apps/api/src/sejong_ai_api/db/errors.py` | `DatabaseRuleError` and SQLSTATE mapping |
| `apps/api/src/sejong_ai_api/db/models.py` | Frozen dataclasses/enums for actors, events, candidates, KB, office, purge results |
| `apps/api/src/sejong_ai_api/db/repository.py` | `SejongRepository` protocol and psycopg implementation calling only `app_api` functions |
| `apps/api/src/sejong_ai_api/db/pool.py` | Explicit `create_pool(database_url)` with `open=False`; callers own open/close lifecycle |

## Exact database interface contract

The implementation must use these names and parameter types. Later API slices consume this boundary without changing its SQL signatures.

```sql
app_api.list_active_kb(
  p_intent text
) RETURNS TABLE (
  public_id text,
  category text,
  service_name text,
  answer_summary text,
  procedure_steps jsonb,
  required_documents jsonb,
  processing_time text,
  fee text,
  department text,
  source_title text,
  source_url text,
  last_verified_at date,
  caution text,
  question_examples jsonb
)

app_api.list_offices(
  p_region text,
  p_intent text
) RETURNS TABLE (
  public_id text,
  region text,
  office_name text,
  address text,
  phone text,
  opening_hours text,
  map_url text,
  department_label text,
  source_title text,
  source_url text,
  last_verified_at date
)

app_api.record_interaction(
  p_request_id uuid,
  p_intent text,
  p_answer_status text,
  p_fallback_reason text,
  p_used_source_ids text[],
  p_response_time_ms integer,
  p_selected_region text,
  p_routed_office_public_id text,
  p_is_test boolean,
  p_masked_question text
) RETURNS TABLE (interaction_id uuid, failed_question_id uuid)

app_api.confirm_failed_question_reason(
  p_failed_question_id uuid,
  p_actor_id text,
  p_actor_role text,
  p_confirmed_fallback_reason text
) RETURNS void

app_api.create_kb_candidate(
  p_failed_question_id uuid,
  p_actor_id text,
  p_actor_role text,
  p_title text,
  p_representative_question text,
  p_category text,
  p_answer_summary text,
  p_procedure_steps jsonb,
  p_required_documents jsonb,
  p_processing_time text,
  p_fee text,
  p_department text,
  p_source_title text,
  p_source_url text,
  p_last_verified_at date,
  p_caution text,
  p_data_origin text
) RETURNS uuid

app_api.submit_kb_candidate(
  p_candidate_id uuid,
  p_actor_id text,
  p_actor_role text
) RETURNS void

app_api.approve_kb_candidate(
  p_candidate_id uuid,
  p_actor_id text,
  p_actor_role text,
  p_review_comment text
) RETURNS text

app_api.reject_kb_candidate(
  p_candidate_id uuid,
  p_actor_id text,
  p_actor_role text,
  p_review_comment text
) RETURNS void

app_api.purge_expired_failed_question_text()
RETURNS TABLE (purged_count integer, purged_ids uuid[])
```

The callable boundary deliberately uses `text` for enum-shaped inputs and outputs. Each
SECURITY DEFINER function validates against an explicit allowlist and casts internally to
the corresponding `app_private` enum. This prevents the backend login from needing
`USAGE` on the private schema or private enum types.

Stable business SQLSTATE mapping:

| SQLSTATE | Python enum | Meaning |
|---|---|---|
| `P1001` | `FORBIDDEN_ACTOR_ROLE` | actor role or actor ownership is not allowed |
| `P1002` | `SELF_APPROVAL` | creator attempted approval/rejection |
| `P1003` | `INVALID_CANDIDATE_STATE` | candidate/failure missing or not in required state |
| `P1004` | `INCOMPLETE_CANDIDATE` | required candidate/source content is incomplete |
| `P1005` | `DISALLOWED_ORIGIN` | non-OFFICIAL candidate attempted activation |
| `P1010` | `INVALID_INTERACTION` | event/failure/source/idempotency combination is invalid |

Error detail may contain a stable record ID or constraint name. It must not contain a question, answer, context token, provider payload, DSN, password, or full row snapshot.

## Task 0: Isolate execution and prove the clean baseline

**Files:**

- Read: `AGENTS.md`
- Read: `apps/api/AGENTS.md`
- Read: `docs/superpowers/specs/2026-07-16-db-001-layered-enforcement-design.md`
- Read: `docs/adr/0011-layered-database-and-backend-enforcement.md`
- Read: `docs/implementation-notes/IMP-20260716-005-db-001-명세-승인과-실행계획.md`
- Modify: `docs/superpowers/plans/2026-07-16-db-001-layered-enforcement.md`
- Modify: `TASKS.md`
- Create: `docs/implementation-notes/IMP-20260716-006-db-001-layered-enforcement.md`
- Modify: `docs/implementation-notes/INDEX.md`

- [x] **Step 1: Create the isolated execution branch/worktree**

Invoke `superpowers:using-git-worktrees`, create branch `codex/db-001-layered-enforcement`, and verify the selected worktree is ignored or outside the repository.

Expected: `git status --short --branch` shows the new branch and no changes.

- [x] **Step 2: Run the existing no-Docker baseline gate**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1
```

Expected: exit 0 with all existing 24 stable step IDs passing; `/ready=503` remains the approved state.

- [x] **Step 3: Record the execution baseline**

Run:

```powershell
git rev-parse --short HEAD
git status --short
docker version --format '{{.Server.Version}}'
```

Expected: a commit ID, empty Git status, and a Docker server version. Do not run Supabase or read `apps/api/.env` in this task.

- [x] **Step 4: Open the implementation note and mark the plan active**

Run:

```powershell
apps/api/.venv/Scripts/python.exe -B scripts/new_implementation_note.py --title "DB-001 layered enforcement" --task-id DB-001 --type implementation
```

Expected: the generator creates exactly `docs/implementation-notes/IMP-20260716-006-db-001-layered-enforcement.md`. If another note has already consumed sequence 006, stop and reconcile the plan/index before implementation. Set the new note to `In Progress`, record the approval text and baseline commit, change this plan status to `In Progress`, add the approval date to plan governance, and change TASK DB-001 from Blocked to In Progress with this plan/note linked.

- [x] **Step 5: Commit the approved execution start**

```powershell
git add docs/superpowers/plans/2026-07-16-db-001-layered-enforcement.md TASKS.md docs/implementation-notes/IMP-20260716-006-db-001-layered-enforcement.md docs/implementation-notes/INDEX.md
git commit -m "docs(db): start approved DB-001 plan"
```

## Task 1: Pin and bootstrap the project-local Supabase CLI

**Files:**

- Create: `scripts/supabase-cli.version.json`
- Create: `scripts/bootstrap_supabase.ps1`
- Create: `scripts/tests/test_supabase_tooling.py`
- Modify: `.gitignore`
- Modify: `scripts/README.md`

- [x] **Step 1: Write the failing repository/tooling tests**

Add tests that parse the pin JSON and script text without network access:

```python
class SupabaseToolPinTests(unittest.TestCase):
    def test_exact_official_windows_pin(self) -> None:
        pin = json.loads((ROOT / "scripts/supabase-cli.version.json").read_text("utf-8"))
        self.assertEqual(pin["version"], "2.109.1")
        self.assertEqual(pin["release"], "v2.109.1")
        self.assertEqual(pin["asset"], "supabase_2.109.1_windows_amd64.zip")
        self.assertEqual(pin["size_bytes"], 75309565)
        self.assertEqual(
            pin["sha256"],
            "d0d270692cf78b8aa56545461f02cdf929ce9bb94e95e5e66404fd0e7d2c0c16",
        )
        self.assertEqual(urlparse(pin["url"]).hostname, "github.com")

    def test_bootstrap_is_local_checksum_gated_and_non_secret(self) -> None:
        script = (ROOT / "scripts/bootstrap_supabase.ps1").read_text("utf-8")
        self.assertIn("Get-FileHash", script)
        self.assertIn("Expand-Archive", script)
        self.assertIn(".tools\\supabase", script)
        self.assertNotIn("npm install", script.lower())
        self.assertNotIn("winget", script.lower())
        self.assertNotIn("supabase login", script.lower())
        self.assertNotIn("supabase link", script.lower())
```

Also extend `RepositoryScaffoldContractTests.test_should_ignore_repository_transient_paths` so `.tools/`, `supabase/.temp/`, and `supabase/.branches/` are required ignores.

- [x] **Step 2: Run the focused tests and confirm RED**

Run:

```powershell
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_supabase_tooling scripts.tests.test_repository_scaffold -v
```

Expected: failures report the missing pin and bootstrap files plus missing Supabase transient ignore entries.

- [x] **Step 3: Add the exact pin manifest**

Create `scripts/supabase-cli.version.json` with this complete content:

```json
{
  "version": "2.109.1",
  "release": "v2.109.1",
  "published_at": "2026-07-07T09:00:28Z",
  "asset": "supabase_2.109.1_windows_amd64.zip",
  "size_bytes": 75309565,
  "url": "https://github.com/supabase/cli/releases/download/v2.109.1/supabase_2.109.1_windows_amd64.zip",
  "sha256": "d0d270692cf78b8aa56545461f02cdf929ce9bb94e95e5e66404fd0e7d2c0c16"
}
```

- [x] **Step 4: Implement the checksum-gated PowerShell bootstrap**

`scripts/bootstrap_supabase.ps1` must:

1. expose only `-VerifyOnly` and `-ArchivePath` parameters;
2. resolve paths from `$PSScriptRoot`, never current directory;
3. download only the manifest URL when `-ArchivePath` is absent and the binary is missing;
4. require HTTPS and exact host `github.com`;
5. validate byte count and SHA-256 before extraction;
6. extract to `.tools/supabase/v2.109.1/` through a temporary sibling directory;
7. require `supabase.exe --version` to equal `2.109.1`;
8. delete only its own temporary archive/directory after resolving and checking the absolute path is under `.tools/supabase/`;
9. print only `[START]`, `[PASS]`, or `[FAIL]` with stable step IDs and exit 0/1/2;
10. never print URLs with credentials, file contents, archive bytes, environment values, or child process output.

The final success lines are exactly:

```text
[PASS] step=VERIFY-SUPABASE-ARCHIVE
[PASS] step=VERIFY-SUPABASE-VERSION
```

`-VerifyOnly` fails with exit 2 and `[FAIL] step=VERIFY-SUPABASE-BINARY reason=missing code=2` when the local binary is absent; it never downloads.

- [x] **Step 5: Add ignore and usage documentation**

Append these exact ignore entries under local DB/runtime state:

```gitignore
supabase/.temp/
supabase/.branches/
```

Document:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_supabase.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_supabase.ps1 -VerifyOnly
```

State that the script is local tooling, not a production dependency, and never performs `login`, `link`, `db push`, or remote project operations.

- [x] **Step 6: Run focused and security tests**

Run:

```powershell
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_supabase_tooling scripts.tests.test_repository_scaffold scripts.tests.test_security_boundaries -v
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1
git diff --check
```

Expected: all tests pass, secret scan exits 0, diff check exits 0.

- [x] **Step 7: Commit Task 1**

```powershell
git add .gitignore scripts/supabase-cli.version.json scripts/bootstrap_supabase.ps1 scripts/README.md scripts/tests/test_supabase_tooling.py scripts/tests/test_repository_scaffold.py
git commit -m "build(db): pin local Supabase CLI"
```

## Task 2: Create the PostgreSQL-only local project and explicit DB gate

**Files:**

- Create: `supabase/config.toml`
- Create: `supabase/seed.sql`
- Create: `scripts/provision_local_database_login.py`
- Create: `scripts/run_database_sql.py`
- Create: `scripts/verify_database.ps1`
- Modify: `scripts/tests/test_supabase_tooling.py`
- Modify: `scripts/README.md`
- Modify: `apps/api/README.md`

- [x] **Step 1: Extend the failing tooling tests**

Add assertions that:

```python
def test_local_config_runs_database_only_and_exposes_no_app_schema(self) -> None:
    config = tomllib.loads((ROOT / "supabase/config.toml").read_text("utf-8"))
    self.assertEqual(config["project_id"], "sejong-ai-local")
    self.assertEqual(config["db"]["port"], 54322)
    self.assertEqual(config["db"]["major_version"], 17)
    self.assertFalse(config["api"]["enabled"])
    self.assertEqual(config["api"]["schemas"], ["public", "graphql_public"])
    self.assertFalse(config["auth"]["enabled"])
    self.assertFalse(config["realtime"]["enabled"])
    self.assertFalse(config["storage"]["enabled"])
    self.assertFalse(config["studio"]["enabled"])
    self.assertFalse(config["local_smtp"]["enabled"])
    self.assertNotIn("inbucket", config)
    self.assertFalse(config["analytics"]["enabled"])
    self.assertFalse(config["edge_runtime"]["enabled"])
    self.assertFalse(config["db"]["pooler"]["enabled"])

def test_database_runner_has_no_remote_or_destructive_host_commands(self) -> None:
    script = (ROOT / "scripts/verify_database.ps1").read_text("utf-8").lower()
    for forbidden in ("db push", "link", "login", "projects", "volume prune", "system prune"):
        self.assertNotIn(forbidden, script)
    self.assertIn("db reset", script)
    self.assertIn("test db", script)
```

Add a temp-file unit test that calls the pure `update_env_assignment(path, "DATABASE_URL", value)` helper in `scripts/provision_local_database_login.py` and proves comments, ordering, `LLM_API_KEY`, and every non-target line remain byte-identical.
Inject an `os.replace` failure after a complete sibling-temp write and prove the original CRLF file remains byte-identical and no temporary file remains.

- [x] **Step 2: Run the focused tests and confirm RED**

Run:

```powershell
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_supabase_tooling -v
```

Expected: missing config, runner, and credential helper failures.

- [x] **Step 3: Generate and harden the local config with the pinned CLI**

Run the exact bootstrap and init commands:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap_supabase.ps1
.tools/supabase/v2.109.1/supabase.exe init
```

Expected: the binary digest/version passes and `supabase/config.toml` is generated. Modify only these settings in the generated v2.109.1 config:

```toml
project_id = "sejong-ai-local"

[api]
enabled = false
port = 54321
schemas = ["public", "graphql_public"]
extra_search_path = ["public", "extensions"]
max_rows = 1000

[db]
port = 54322
shadow_port = 54320
major_version = 17

[db.pooler]
enabled = false

[db.seed]
enabled = false
sql_paths = ["./seed.sql"]

[realtime]
enabled = false

[studio]
enabled = false

[local_smtp]
enabled = false

[storage]
enabled = false

[auth]
enabled = false

[edge_runtime]
enabled = false

[analytics]
enabled = false
```

Keep the remaining generated v2.109.1 keys unchanged so CLI decoding remains forward-compatible. `app_private` and `app_api` must not appear in `api.schemas` or `api.extra_search_path`.

- [x] **Step 4: Add the intentionally empty seed boundary**

Create `supabase/seed.sql`:

```sql
-- DB-001 deliberately contains no official or mock seed.
-- DATA-001 and DATA-SEED-001 own PM-approved data and versioned lineage.
-- An empty approved-data set must keep /ready at HTTP 503.
```

- [x] **Step 5: Implement local credential provisioning**

`scripts/provision_local_database_login.py` must define constants
`ROLE_NAME = "sejong_local_login"` and `TARGET_ENV_KEY = "DATABASE_URL"`, plus typed
functions `update_env_assignment(path: Path, key: str, value: str) -> None`,
`provision(admin_dsn: str, env_path: Path) -> None`, and `main() -> int`.

The completed implementations must have these behaviors:

- read admin DSN only from `SEJONG_ADMIN_DATABASE_URL`;
- generate `secrets.token_urlsafe(32)` on every successful provisioning run;
- use `psycopg.sql.Identifier` and `psycopg.sql.Literal`, not string interpolation, for role DDL;
- create `sejong_local_login` if absent or rotate its password if present;
- explicitly apply `LOGIN INHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS`;
- execute `GRANT sejong_backend TO sejong_local_login`;
- construct the backend DSN with `psycopg.conninfo.make_conninfo`;
- update only `DATABASE_URL` in `apps/api/.env`, creating the ignored file if absent;
- preserve comments, blank lines, and all other environment assignments, including the user's DeepSeek key;
- write and fsync an exclusively created same-directory temporary file, atomically replace the target, and clean the temporary file on every failure;
- never read or print the DeepSeek value;
- print only `[PASS] step=PROVISION-LOCAL-DB-LOGIN` on success.

An omitted admin environment value returns exit 2 with a stable error line. A DB failure returns exit 1 without exception text or DSN.

- [x] **Step 6: Implement the ordered SQL helper**

`scripts/run_database_sql.py` takes one or more explicit file paths, requires every resolved file to remain inside `database/`, reads `SEJONG_ADMIN_DATABASE_URL`, and executes each file in its own transaction with `autocommit=False`. Its success output contains the decimal file count and, for the four-file rollback invocation, is exactly:

```text
[PASS] step=RUN-DATABASE-SQL files=4
```

It rejects directories, missing files, paths outside `database/`, and empty file lists with exit 2. SQL execution failure rolls back and returns exit 1 without SQL text or server error detail.

- [x] **Step 7: Implement the explicit DB verification runner**

`scripts/verify_database.ps1` exposes only `-SkipStart` and `-SkipRollbackReplay`. It must:

1. verify PowerShell 5.1, Docker server, pinned CLI, and API venv Python;
2. call `supabase db start` unless `-SkipStart` is present so the persistent project runtime contains PostgreSQL only;
3. call `supabase db reset --local`;
4. capture `supabase status -o env` in memory, extract `DB_URL`, assign it only to child process `SEJONG_ADMIN_DATABASE_URL`, and never echo captured output;
5. call the provisioning script;
6. call `supabase test db`;
7. run the four compensation files newest-first and `database/verify_db001_absent.sql` unless `-SkipRollbackReplay` is present;
8. call `supabase db reset --local`, provision/rotate the local login again because compensation dropped the capability role, and call `supabase test db` after rollback;
9. set `SEJONG_DB_TEST_URL` from the ignored backend env without printing it, then run `pytest -q -p no:cacheprovider apps/api/tests/db/test_integration.py`;
10. restore or remove every process environment value it changed in a `finally` block.

The runner suppresses all child stdout/stderr and prints stable step IDs only. Bare `supabase start` is forbidden because v2.109.1 can start Kong even when the Data API is disabled. `supabase test db` may create a one-shot `pg_prove` test container; that does not change the PostgreSQL-only persistent runtime contract. The runner does not stop containers automatically, touch Docker volumes directly, or call a remote Supabase command.

- [x] **Step 8: Run the focused tests**

Run:

```powershell
apps/api/.venv/Scripts/python.exe -B -m unittest scripts.tests.test_supabase_tooling scripts.tests.test_security_boundaries -v
apps/api/.venv/Scripts/python.exe -m ruff check scripts/provision_local_database_login.py scripts/run_database_sql.py
apps/api/.venv/Scripts/python.exe -m mypy scripts/provision_local_database_login.py scripts/run_database_sql.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1
git diff --check
```

Expected: all tests, lint, typing, secret scan, and diff check pass. Do not run `verify_database.ps1` before migrations exist.

- [x] **Step 9: Commit Task 2**

```powershell
git add supabase/config.toml supabase/seed.sql scripts/provision_local_database_login.py scripts/run_database_sql.py scripts/verify_database.ps1 scripts/tests/test_supabase_tooling.py scripts/README.md apps/api/README.md
git commit -m "build(db): add local database verification gate"
```

## Task 3: Create the private schema, seven enums, and eight tables

**Files:**

- Create: `supabase/tests/database/001_schema_test.sql`
- Create: `supabase/migrations/20260716000100_private_schema.sql`
- Create: `database/rollbacks/20260716000100_private_schema.rollback.sql`
- Create: `database/verify_db001_absent.sql`

- [x] **Step 1: Write the failing pgTAP schema contract**

The test must call `plan(32)` and assert:

- schemas `app_private` and `app_api` exist;
- enums `intent_code`, `answer_status`, `fallback_reason`, `kb_status`, `candidate_status`, `admin_role`, `data_origin` exist in `app_private`;
- exactly these eight tables exist only in `app_private`: `kb_documents`, `kb_question_examples`, `offices`, `office_service_mappings`, `interaction_events`, `failed_questions`, `kb_candidates`, `audit_logs`;
- `offices.is_official` is generated and not caller-writable;
- `kb_documents.data_origin`, `offices.data_origin`, and `kb_candidates.data_origin` are non-null without a default;
- no column name across the eight tables matches `raw_question`, `question_text`, `answer_text`, `transcript`, `context_token`, `ip_address`, `device_id`, `secret`, or `provider_payload`;
- the default `public` schema has none of the eight business tables.

Use pgTAP catalog functions plus one `is` assertion for the forbidden-column count. Finish with `SELECT * FROM finish();` and an automatic rollback.

- [x] **Step 2: Run the pgTAP test and confirm RED**

Start the local DB while suppressing the CLI credential/status payload, then run the test:

```powershell
$startOutput = & .tools/supabase/v2.109.1/supabase.exe db start 2>&1
if ($LASTEXITCODE -ne 0) { throw "START_LOCAL_DATABASE_FAILED" }
Remove-Variable startOutput
.tools/supabase/v2.109.1/supabase.exe test db
```

Expected: failure because the private schemas and tables do not exist.

- [x] **Step 3: Implement the first migration**

Create both schemas and these enum values:

```sql
CREATE SCHEMA app_private;
CREATE SCHEMA app_api;

CREATE TYPE app_private.intent_code AS ENUM (
  'MOVE_IN_RESIDENT_REGISTRATION',
  'CERTIFICATE_ISSUANCE',
  'BULKY_WASTE',
  'LOCAL_TAX_GENERAL',
  'OUT_OF_SCOPE',
  'UNKNOWN'
);
CREATE TYPE app_private.answer_status AS ENUM ('SUCCESS', 'FOLLOWUP', 'FALLBACK', 'SYSTEM_ERROR');
CREATE TYPE app_private.fallback_reason AS ENUM (
  'INSUFFICIENT_GROUNDING', 'PERSONAL_LOOKUP', 'LEGAL_JUDGMENT', 'OUT_OF_SCOPE'
);
CREATE TYPE app_private.kb_status AS ENUM ('DRAFT', 'PENDING', 'ACTIVE', 'REJECTED', 'RETIRED');
CREATE TYPE app_private.candidate_status AS ENUM (
  'NEW', 'REASON_CONFIRMED', 'DRAFTED', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED'
);
CREATE TYPE app_private.admin_role AS ENUM ('OPERATOR', 'APPROVER');
CREATE TYPE app_private.data_origin AS ENUM ('OFFICIAL', 'MOCK');
```

Convert all eight table definitions from `database/schema-v1.draft.sql` into `app_private`, preserving UUID primary keys and timestamps, with these deliberate shape changes:

- add required/no-default `data_origin` to KB, offices, candidates;
- define `offices.is_official boolean GENERATED ALWAYS AS (data_origin = 'OFFICIAL') STORED`;
- keep `interaction_events` metadata-only and `failed_questions.masked_question` as the only question-like retained text;
- keep DB UUIDs private and all user-facing records with unique trimmed `public_id` fields;
- keep candidate content non-null at creation because DB-001 has no partial-edit interface;
- keep `audit_logs.changed_field_names` JSONB and no snapshot column;
- schema-qualify every enum and FK reference.

Do not add policies, grants, triggers, functions, indexes, official rows, or mock rows in this migration.

- [x] **Step 4: Add first-stage compensation and absence proof**

The compensation file runs only after later compensation files and contains:

```sql
BEGIN;
DROP SCHEMA IF EXISTS app_api CASCADE;
DROP SCHEMA IF EXISTS app_private CASCADE;
COMMIT;
```

`database/verify_db001_absent.sql` must raise if either schema or either Sejong role exists, while checking that `public` and Supabase-owned schemas still exist. It must not drop anything.

- [x] **Step 5: Reset and verify GREEN**

Run:

```powershell
.tools/supabase/v2.109.1/supabase.exe db reset --local
.tools/supabase/v2.109.1/supabase.exe test db
```

Expected: reset exits 0 and all 32 pgTAP assertions pass.

- [x] **Step 6: Commit Task 3**

```powershell
git add supabase/migrations/20260716000100_private_schema.sql database/rollbacks/20260716000100_private_schema.rollback.sql database/verify_db001_absent.sql supabase/tests/database/001_schema_test.sql
git commit -m "feat(db): create private domain schema"
```

## Task 4: Enforce table-level data quality and cross-table invariants

**Files:**

- Create: `supabase/tests/database/002_invariants_test.sql`
- Create: `supabase/migrations/20260716000200_invariants_and_lineage.sql`
- Create: `database/rollbacks/20260716000200_invariants_and_lineage.rollback.sql`
- Create: `scripts/test_database_concurrency.py`

- [x] **Step 1: Write failing invariant tests**

The pgTAP test must use explicit `MOCK` fixtures and prove:

- whitespace-only public IDs and required text fail;
- procedure/document JSON that is not an array, contains a non-string, or contains an empty string fails;
- empty arrays and arrays of trimmed non-empty strings pass;
- unsupported KB categories/regions/mapping intents fail;
- ACTIVE without approval fields, OFFICIAL origin, or at least one question example fails at transaction end;
- deleting the final question example from ACTIVE fails at transaction end;
- SUCCESS without sources or with a non-ACTIVE/non-OFFICIAL source fails;
- FOLLOWUP with fallback reason or any failure row fails;
- OUT_OF_SCOPE with retained text fails;
- only INSUFFICIENT_GROUNDING can be candidate eligible;
- `text_expires_at` is exactly `created_at + interval '30 days'`;
- candidate must reference an eligible INSUFFICIENT_GROUNDING failure;
- candidate and failure table-specific statuses reject irrelevant enum values;
- audit actions, target types, and changed-field arrays are allowlisted and contain non-empty strings.

- [x] **Step 2: Run the invariant test and confirm RED**

Run:

```powershell
.tools/supabase/v2.109.1/supabase.exe test db
```

Expected: assertions for JSON/text/status/cross-table rules fail.

- [x] **Step 3: Add reusable private validators**

Implement immutable, strict, schema-qualified helpers:

```sql
CREATE FUNCTION app_private.is_nonempty_text(p_value text)
RETURNS boolean
LANGUAGE sql
IMMUTABLE
STRICT
SET search_path = pg_catalog
AS $$ SELECT btrim(p_value) <> '' $$;

CREATE FUNCTION app_private.is_text_array(p_value jsonb)
RETURNS boolean
LANGUAGE sql
IMMUTABLE
STRICT
SET search_path = pg_catalog
AS $$
  SELECT jsonb_typeof(p_value) = 'array'
    AND NOT EXISTS (
      SELECT 1
      FROM jsonb_array_elements(p_value) AS item(value)
      WHERE jsonb_typeof(item.value) <> 'string'
         OR btrim(item.value #>> '{}') = ''
    )
$$;
```

Create a single `set_updated_at()` trigger function and attach it only to `kb_documents`, `failed_questions`, and `kb_candidates`.

- [x] **Step 4: Add exact checks and deferred constraint triggers**

Add named checks for all bullets in Step 1. Cross-table rules must be in trigger functions that query only schema-qualified `app_private` objects. The ACTIVE-question rule uses constraint triggers declared `DEFERRABLE INITIALLY DEFERRED` on KB status changes and question-example INSERT/UPDATE/DELETE so the approval transaction can insert ACTIVE KB and its first example before commit.

The event/failure trigger verifies identical intent and fallback reason and requires the parent event status to be FALLBACK. The candidate trigger requires an eligible INSUFFICIENT_GROUNDING failure. No trigger error includes a text field value.

Review-driven concurrency hardening makes invariant-bearing writes an explicit `READ COMMITTED` operational contract. Non-`READ COMMITTED` writes fail closed with stable `P0001` messages, and the two-connection probe covers the three stale-snapshot lineages without retaining fixture rows.

- [x] **Step 5: Add reverse-order invariant compensation**

The rollback file drops constraint triggers first, then ordinary triggers, then their functions, then every named constraint added by this migration. It does not drop a table, schema, role, or Supabase-owned object.

- [x] **Step 6: Reset and run schema plus invariant tests**

Run:

```powershell
.tools/supabase/v2.109.1/supabase.exe db reset --local
.tools/supabase/v2.109.1/supabase.exe test db
```

Expected: both files pass and transaction cleanup leaves no fixture rows.

- [x] **Step 7: Commit Task 4**

```powershell
git add supabase/migrations/20260716000200_invariants_and_lineage.sql database/rollbacks/20260716000200_invariants_and_lineage.rollback.sql supabase/tests/database/002_invariants_test.sql scripts/test_database_concurrency.py
git commit -m "feat(db): enforce privacy and lineage invariants"
```

## Task 5: Add roles, forced RLS, interaction recording, and retention

**Files:**

- Create: `supabase/tests/database/003_capabilities_test.sql`
- Create: `supabase/migrations/20260716000300_capabilities_and_functions.sql`
- Create: `database/rollbacks/20260716000300_capabilities_and_functions.rollback.sql`

- [x] **Step 1: Write failing capability/event/retention tests**

The pgTAP suite must prove:

- roles `sejong_schema_owner` and `sejong_backend` exist with `NOLOGIN`, `NOSUPERUSER`, `NOCREATEDB`, `NOCREATEROLE`, `NOREPLICATION`, `NOBYPASSRLS`;
- all eight tables have RLS enabled and forced;
- `PUBLIC`, `anon`, `authenticated`, and `sejong_backend` lack direct SELECT/INSERT/UPDATE/DELETE on every base table;
- every `app_api` SECURITY DEFINER function is owned by `sejong_schema_owner`, has fixed `search_path`, and lacks PUBLIC execute;
- identical `request_id` replay returns the existing IDs and writes no duplicate;
- conflicting replay raises `P1010`;
- SUCCESS accepts only unique ACTIVE+OFFICIAL source IDs;
- FOLLOWUP and OUT_OF_SCOPE create no failed row and reject retained text;
- support-scope INSUFFICIENT_GROUNDING with safe masked text creates eligible failure;
- PERSONAL_LOOKUP and LEGAL_JUDGMENT create ineligible failure only when masked text exists;
- a missing masked value creates event only;
- private cutoff purge changes just-before/equal/after boundary correctly;
- public purge accepts no caller time, is idempotent, NULLs only text, sets purge time, and preserves event/candidate links.

- [x] **Step 2: Run capability tests and confirm RED**

Run:

```powershell
.tools/supabase/v2.109.1/supabase.exe test db
```

Expected: roles/functions/RLS assertions fail.

- [x] **Step 3: Create locked-down capability roles and ownership**

Q-SEC-002=A accepts the implemented PostgreSQL 17 non-superuser model. Use
idempotent `DO` blocks to create both roles with every safe attribute. On replay,
unconditionally restore the runner-permitted `NOLOGIN`, `NOCREATEDB`, and
`NOCREATEROLE` attributes, then catalog-verify `NOSUPERUSER`, `NOREPLICATION`,
`NOBYPASSRLS`, role settings, and effective memberships. An unsafe existing role
fails closed; no privileged auto-downgrade/bootstrap is introduced. Revoke
`CREATE` on `public` from `PUBLIC`. Revoke all privileges on `app_private` and
`app_api` from `PUBLIC`, `anon`, and `authenticated`, then grant `USAGE` on
`app_api` only to `sejong_backend`. Transfer ownership of `app_private`,
`app_api`, all app enums/tables/sequences/functions to `sejong_schema_owner`.
Enable and force RLS on every base table, then create one owner-only `FOR ALL`
policy per table:

```sql
CREATE POLICY kb_documents_owner_all
ON app_private.kb_documents
FOR ALL
TO sejong_schema_owner
USING (true)
WITH CHECK (true);
```

Repeat with table-specific policy names. Do not create an `anon`, `authenticated`, or backend table policy.

- [x] **Step 4: Implement `record_interaction` exactly**

The function uses the signature in this plan, `SECURITY DEFINER`, and:

- fixed `SET search_path = pg_catalog`;
- non-negative response time and supported region validation;
- non-null source array containing unique non-empty source IDs;
- ACTIVE+OFFICIAL source resolution for SUCCESS;
- SUCCESS: one supported intent, null fallback reason, at least one source, null masked text;
- FOLLOWUP: supported or UNKNOWN intent, null fallback reason, zero sources, null masked text;
- FALLBACK/OUT_OF_SCOPE: OUT_OF_SCOPE intent and reason, zero sources, null masked text;
- FALLBACK/INSUFFICIENT_GROUNDING, PERSONAL_LOOKUP, or LEGAL_JUDGMENT: supported intent, zero sources, optional already-masked text;
- SYSTEM_ERROR: null fallback reason, zero sources, null masked text, event metadata only;
- office public ID resolution only to OFFICIAL office;
- request-ID idempotency by locking the matching `interaction_events` row `FOR SHARE` and comparing each metadata column with `IS NOT DISTINCT FROM`;
- `P1010` for invalid combinations or conflicting replay;
- one event plus zero/one failure in the same transaction;
- no dynamic SQL and no user text in raised messages.

Store `used_source_ids` as `to_jsonb(p_used_source_ids)` and derive `source_count` with `cardinality`. For duplicate identical metadata, return the existing interaction ID and linked failure ID without comparing or rewriting a potentially purged `masked_question`.

- [x] **Step 5: Implement retention functions**

Create private cutoff helper:

```sql
app_private.purge_expired_failed_question_text_at(p_cutoff timestamptz)
RETURNS TABLE (purged_count integer, purged_ids uuid[])
```

It updates only rows where `masked_question IS NOT NULL AND text_expires_at <= p_cutoff`, sets `masked_question=NULL`, `text_purged_at=p_cutoff`, aggregates sorted IDs, and returns zero plus an empty UUID array when no rows change. The public `app_api.purge_expired_failed_question_text()` calls it with `clock_timestamp()` and exposes no time parameter.

- [x] **Step 6: Lock function privileges**

For every new interface:

```sql
ALTER FUNCTION app_api.record_interaction(
  uuid,
  text,
  text,
  text,
  text[],
  integer,
  text,
  text,
  boolean,
  text
) OWNER TO sejong_schema_owner;
REVOKE ALL ON FUNCTION app_api.record_interaction(
  uuid,
  text,
  text,
  text,
  text[],
  integer,
  text,
  text,
  boolean,
  text
) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION app_api.record_interaction(
  uuid,
  text,
  text,
  text,
  text[],
  integer,
  text,
  text,
  boolean,
  text
) TO sejong_backend;
```

Grant backend `USAGE` on `app_api` only. Do not grant backend `USAGE` on `app_private`; function argument/return types remain resolvable through the function contract while base objects stay inaccessible.

- [x] **Step 7: Add capability compensation**

The compensation file revokes backend Task 5 function/schema grants, drops Task 5 functions, drops policies, disables forced RLS only for rollback, reassigns objects owned by `sejong_schema_owner` to `postgres`, drops owned privileges for both roles, and drops `sejong_backend` then `sejong_schema_owner`. It executes only after the Task 7 `00500` and Task 6 `00400` compensations. Existing defensive `DROP FUNCTION IF EXISTS` identities remain harmless, but the new workflow compensation owns removal of workflow functions.

- [x] **Step 8: Reset and run all current DB tests**

Run:

```powershell
.tools/supabase/v2.109.1/supabase.exe db reset --local
.tools/supabase/v2.109.1/supabase.exe test db
```

Expected: all assertions pass; no test emits retained question text.

Actual: TDD RED was the intended 6/6 missing-capability failures. After the
implementation and review fix, root independently reproduced reset, 172/172
pgTAP, `00300 → 00200 → 00100` compensation, absence proof, fresh replay, and
172/172 again. Identical/conflicting two-session replay, concurrent purge, and
backend diagnostic nonleak probes also passed. Independent code/spec reviews
are clean. Q-SEC-002=A accepts the fail-closed role behavior, so Task 5 is complete.

- [x] **Step 9: Commit Task 5**

```powershell
git add supabase/migrations/20260716000300_capabilities_and_functions.sql database/rollbacks/20260716000300_capabilities_and_functions.rollback.sql supabase/tests/database/003_capabilities_test.sql
git commit -m "feat(db): add backend capabilities and retention"
```

Actual commits: `fa6b755` (`feat(db): add backend capabilities and retention`)
and review fix `264772d` (`fix(db): stabilize capability replay guarantees`).

## Task 6: Add atomic candidate workflow and append-only audit

**Files:**

- Create: `supabase/migrations/20260716000400_candidate_workflow.sql`
- Create: `database/rollbacks/20260716000400_candidate_workflow.rollback.sql`
- Create: `supabase/tests/database/004_approval_test.sql`
- Modify: `supabase/tests/database/003_capabilities_test.sql`
- Modify: `supabase/tests/database/002_invariants_test.sql`
- Modify: `scripts/test_database_concurrency.py`
- Modify: `database/rollbacks/20260716000300_capabilities_and_functions.rollback.sql`

Applied and committed migrations `00100~00300` are immutable. All Task 6
constraints, trigger replacements, functions, grants, and audit allowlist changes
belong to the new `00400` forward migration and its matching compensation.

- [x] **Step 1: Write failing approval tests**

Use explicit MOCK and OFFICIAL fixtures to prove:

- only OPERATOR can create and submit candidates;
- only OPERATOR can confirm a NEW failure reason;
- confirmation preserves the parent event's initial automated reason, updates only the failure reason/status/re-derived eligibility, and writes exactly one `FAILED_QUESTION_REASON_CONFIRMED` audit row;
- duplicate/concurrent confirmation produces one success and one `P1003`, with one audit row;
- candidate creation requires `REASON_CONFIRMED`, eligible INSUFFICIENT_GROUNDING failure;
- concurrent confirmation/candidate creation serializes on the failure row and cannot create from NEW or corrected ineligible failures;
- submit requires creator ownership, DRAFTED state, and complete content/source fields;
- OPERATOR approval/rejection raises `P1001`;
- creator approval/rejection raises `P1002`;
- wrong candidate state raises `P1003`;
- incomplete content raises `P1004`;
- MOCK activation raises `P1005`;
- approval and rejection both require a trimmed non-empty review comment;
- approval and rejection reject review comments longer than the OpenAPI maximum
  of 1000 characters;
- approval creates exactly one ACTIVE OFFICIAL KB, exactly one generalized initial question example, candidate link/status/reviewer/timestamp/comment, and exactly one approval audit row;
- rejection requires non-empty comment and writes one rejection audit row;
- audit UPDATE and DELETE fail for backend;
- audit rows contain only allowlisted action, target/status, changed-field names, optional review comment, actor, and timestamp.
- the Task 5 capability suite's explicit backend function allowlist contains the
  exact four-argument confirmation and approval identities and rejects every
  other `app_api` EXECUTE grant.

- [x] **Step 2: Run approval tests and confirm RED**

Run:

```powershell
.tools/supabase/v2.109.1/supabase.exe test db
```

Expected: missing `00400` reason-confirmation/candidate functions and audit/lineage refinements cause failure.

- [x] **Step 3: Implement reason confirmation, candidate creation, and submission**

Implement the exact signatures from this plan. All functions are SECURITY DEFINER with fixed search path, explicit `FOR UPDATE` locks where an existing row changes, and stable SQLSTATE errors.

`confirm_failed_question_reason(uuid,text,text,text)` requires OPERATOR, locks a
NEW failure, validates one stored failure reason, and leaves
`interaction_events.fallback_reason` unchanged. It updates only the failure's
reason, `candidate_eligible = (reason = 'INSUFFICIENT_GROUNDING')`, and status to
`REASON_CONFIRMED`. It writes one metadata-only audit row with action
`FAILED_QUESTION_REASON_CONFIRMED`, target `FAILED_QUESTION`, status
`NEW → REASON_CONFIRMED`, and only the actual changed field names among
`status`, `fallback_reason`, and `candidate_eligible`. Wrong role is `P1001`,
wrong/duplicate state is `P1003`, and invalid reason/lineage is `P1010`.

Confirmation changed-field arrays use canonical order and contain only fields
whose stored value actually changed: same-reason confirmation records
`["status"]`; a reason-only change adds `fallback_reason`; a change that also
flips eligibility adds `candidate_eligible` last.

Replace the earlier lineage trigger behavior in this forward migration so only a
NEW failure must match its immutable parent event. A confirmed failure may retain
an operator-corrected reason. Direct changes that invalidate an existing
candidate remain forbidden. Candidate creation locks the failure and requires
`REASON_CONFIRMED + INSUFFICIENT_GROUNDING + candidate_eligible=true`, writes one
DRAFTED candidate and `CANDIDATE_CREATED` audit row. Submission verifies OPERATOR
role, creator identity, DRAFTED state, complete non-empty content, valid arrays,
and then moves to PENDING_APPROVAL with one `CANDIDATE_SUBMITTED` audit row.

Allowed audit actions are exactly:

```text
CANDIDATE_CREATED
CANDIDATE_SUBMITTED
CANDIDATE_APPROVED
CANDIDATE_REJECTED
FAILED_QUESTION_REASON_CONFIRMED
```

Allowed target types are `KB_CANDIDATE` and `FAILED_QUESTION`. Candidate changed-field lists are fixed server values, not caller inputs; confirmation derives its allowlisted changed-field names from actual changes and never stores a question/reason snapshot.

Add action-shape constraints so allowlisted values cannot be cross-combined:
candidate creation is `NULL → DRAFTED` with `["review_status"]`; submission is
`DRAFTED → PENDING_APPROVAL` with `["review_status"]`; approval is
`PENDING_APPROVAL → APPROVED` with
`["review_status","reviewed_by","review_comment","approved_at","activated_kb_id"]`;
rejection is `PENDING_APPROVAL → REJECTED` with
`["review_status","reviewed_by","review_comment"]`; confirmation is
`NEW → REASON_CONFIRMED` with the actual canonical field list above. Candidate
review comments and audit review comments are trimmed, non-empty where required,
and at most 1000 characters.

Harden candidate row state shape in the same migration: DRAFTED and
PENDING_APPROVAL have null reviewer/comment/approval/link fields; APPROVED has
reviewer, comment, approval time, and activated KB; REJECTED has reviewer and
comment but no approval time or activated KB. The existing different-reviewer
constraint remains mandatory.

- [x] **Step 4: Implement atomic approval**

`approve_kb_candidate` must:

1. accept exact signature `approve_kb_candidate(uuid,text,text,text)`, require `APPROVER`, a trimmed non-empty review comment of at most 1000 characters, lock candidate `FOR UPDATE`, and reject creator identity;
2. require `PENDING_APPROVAL`, complete content/source, and `OFFICIAL` origin;
3. generate public ID as `KB-` plus all 32 uppercase hexadecimal characters of candidate UUID with hyphens removed, making it a deterministic one-to-one mapping;
4. insert one ACTIVE KB with candidate content, creator, approver, and approval time;
5. insert candidate `representative_question` as the first question example;
6. update candidate to APPROVED and set reviewer/time/activated KB ID/review comment;
7. insert one approval audit row with the review comment;
8. return the generated public ID;
9. rely on the transaction and deferred ACTIVE-question trigger so any failure rolls back all four writes.

- [x] **Step 5: Implement atomic rejection**

`reject_kb_candidate` requires APPROVER, a different actor, PENDING_APPROVAL, and a trimmed non-empty comment of at most 1000 characters. It updates the candidate and inserts one audit row in the same transaction. It never copies candidate question/answer content into audit.

- [x] **Step 6: Apply ownership and execute grants**

For each of the five workflow interfaces, set owner, revoke PUBLIC/anon/authenticated, and grant only `sejong_backend`, using exact argument type lists. The backend retains no direct failed-question, candidate, or audit-table INSERT/UPDATE/DELETE grant.

Update `003_capabilities_test.sql` rather than weakening its global function
allowlist: add `confirm_failed_question_reason(uuid,text,text,text)` and replace
the old planned three-argument approval identity with
`approve_kb_candidate(uuid,text,text,text)` in both allowlist assertions.

- [x] **Step 7: Extend compensation and run tests**

The `00400` compensation revokes workflow execute grants, drops the five workflow
functions, restores replaced Task 4 trigger/constraint definitions, removes the
reason-confirmation audit allowlist extension, and leaves Task 5 roles/RLS/event/
retention intact. It must run after `00500` and before `00300`. Run:

Update the `00300` compensation guard so it raises
`WORKFLOW_COMPENSATION_REQUIRED` while any `00400` workflow function remains,
and remove its obsolete predeclared Task 6 drops. This makes reverse lineage
ownership exact instead of letting the Task 5 compensation partially remove a
later migration.

```powershell
.tools/supabase/v2.109.1/supabase.exe db reset --local
.tools/supabase/v2.109.1/supabase.exe test db
```

Expected: all suites pass.

- [x] **Step 8: Commit Task 6**

```powershell
git add supabase/migrations/20260716000400_candidate_workflow.sql database/rollbacks/20260716000400_candidate_workflow.rollback.sql database/rollbacks/20260716000300_capabilities_and_functions.rollback.sql supabase/tests/database/002_invariants_test.sql supabase/tests/database/003_capabilities_test.sql supabase/tests/database/004_approval_test.sql scripts/test_database_concurrency.py
git commit -m "feat(db): make KB approval atomic"
```

**Actual result (2026-07-17 KST):**

- Started from `dee1ccb`; implementation commits were `cd18ff6`, semantic review
  fix `2ba566d`, and formatting-only gate fix `72b7ab1`.
- Initial RED stopped at the missing workflow interface. Independent review then
  reproduced focused RED 5/62 plus a deterministic replay/confirmation `40P01`
  deadlock before the lock-order, monotonic-lineage, and collision-diagnostic fix.
- Final focused workflow pgTAP was 62/62; full reset/replay was 234/234.
- Forward and replay concurrency passed 4 scenarios with 2 connections;
  compensated Task 1~5 passed 172/172 and the original 3 concurrency scenarios.
- The `00300` compensation guard failed closed as expected while `00400` remained;
  004 compensation restored the exact Task 4 trigger/validator definitions.
- Ruff format/check, Ruff lint, mypy, tooling target, concurrency, secret scan,
  `git diff --check`, and independent code review were clean. Full evidence is
  in `.superpowers/sdd/task-6-report.md` and
  `docs/implementation-notes/IMP-20260717-001-db-001-task-6-atomic-candidate-workflow.md`.

## Task 7: Add ACTIVE+OFFICIAL citizen reads and indexes

**Files:**

- Created: `supabase/migrations/20260716000500_indexes_and_read_interfaces.sql`
- Created: `database/rollbacks/20260716000500_indexes_and_read_interfaces.rollback.sql`
- Created: `supabase/tests/database/005_citizen_reads_test.sql`

- [x] **Step 1: Write failing citizen-read tests**

Create synthetic rows covering ACTIVE OFFICIAL, ACTIVE MOCK, DRAFT OFFICIAL, PENDING OFFICIAL, RETIRED OFFICIAL, and an office/mapping matrix. Prove:

- `list_active_kb` returns only matching-intent ACTIVE+OFFICIAL rows;
- each returned KB has its question examples as a JSON array and authoritative source metadata from the row;
- `list_offices` returns only matching region+intent OFFICIAL offices;
- mock offices and non-matching mappings never appear;
- PUBLIC, anon, and authenticated cannot execute either function;
- backend can execute both functions but still cannot select base tables;
- the five approved indexes exist with exact predicates/columns.

- [x] **Step 2: Run citizen-read tests and confirm RED**

Run:

```powershell
.tools/supabase/v2.109.1/supabase.exe test db
```

Expected: read functions and indexes are missing.

- [x] **Step 3: Add the five indexes**

Create:

```sql
CREATE INDEX idx_kb_active_official_category
  ON app_private.kb_documents (category)
  WHERE status = 'ACTIVE' AND data_origin = 'OFFICIAL';
CREATE INDEX idx_events_occurred
  ON app_private.interaction_events (occurred_at DESC);
CREATE INDEX idx_failures_status
  ON app_private.failed_questions (status, fallback_reason);
CREATE INDEX idx_failure_text_expiry
  ON app_private.failed_questions (text_expires_at)
  WHERE masked_question IS NOT NULL;
CREATE INDEX idx_candidates_status
  ON app_private.kb_candidates (review_status);
```

- [x] **Step 4: Implement exact read functions**

Use the signatures in this plan. `list_active_kb` rejects OUT_OF_SCOPE/UNKNOWN with `P1010`, filters ACTIVE+OFFICIAL, aggregates question examples in deterministic lexical order, and returns authoritative source fields. `list_offices` rejects unsupported region/intent with `P1010`, filters OFFICIAL provenance, joins mapping, and orders by office public ID. Both are `STABLE`, `SECURITY DEFINER`, fixed-search-path functions with all objects schema-qualified.

- [x] **Step 5: Apply grants and add compensation**

Set owner to `sejong_schema_owner`, revoke PUBLIC/anon/authenticated execution, and grant only `sejong_backend`. The compensation drops functions first and then the five indexes; it does not alter tables or roles.

- [x] **Step 6: Reset and run the complete pgTAP suite**

Run:

```powershell
.tools/supabase/v2.109.1/supabase.exe db reset --local
.tools/supabase/v2.109.1/supabase.exe test db
```

Expected: all five database test files pass.

- [x] **Step 7: Commit Task 7**

```powershell
git add supabase/migrations/20260716000500_indexes_and_read_interfaces.sql database/rollbacks/20260716000500_indexes_and_read_interfaces.rollback.sql supabase/tests/database/005_citizen_reads_test.sql
git commit -m "feat(db): expose official citizen read capabilities"
```

**Actual Task 7 result (2026-07-17 KST):**

- Base `e05e036`; implementation commit `37b5e2c`; test-hardening commit
  `59a69bd`. Applied migrations `00100~00400` remained unchanged.
- The initial RED kept the previous 234 assertions green, failed 9 of the first
  11 new catalog checks, then stopped on the absent function as expected.
- Focused citizen-read pgTAP passed 40/40 and the full five-file suite passed
  274/274. The hardening commit made the no-dynamic-SQL and per-function stacked
  diagnostic checks non-vacuous without changing production behavior.
- `00500` compensation removed exactly two functions and five indexes; the
  preserved Task 1~6 baseline passed 234/234 plus four two-connection scenarios.
  Fresh five-migration replay passed 274/274 plus the same four scenarios.
- Root independently reproduced forward `274+4`, compensated `234+4`, and final
  replay `274+4`. Final catalog evidence was
  `functions=2 posture=2 acl=2 indexes=5 rows=0 backend_select=0`.
- Independent review after `59a69bd` reported Critical/Important/Minor 0.
  Persistent official/mock rows, environment/DeepSeek access, remote operations,
  dependencies, contracts, and manifest versions all remained unchanged. Full
  evidence is in `.superpowers/sdd/task-7-report.md` and
  `docs/implementation-notes/IMP-20260717-002-db-001-task-7-official-citizen-reads.md`.

## Task 8: Add the lazy typed FastAPI database boundary

**Files:**

- Create: `apps/api/src/sejong_ai_api/db/__init__.py`
- Create: `apps/api/src/sejong_ai_api/db/errors.py`
- Create: `apps/api/src/sejong_ai_api/db/models.py`
- Create: `apps/api/src/sejong_ai_api/db/pool.py`
- Create: `apps/api/src/sejong_ai_api/db/repository.py`
- Create: `apps/api/tests/db/__init__.py`
- Create: `apps/api/tests/db/test_errors.py`
- Create: `apps/api/tests/db/test_models.py`
- Create: `apps/api/tests/db/test_repository.py`
- Modify: `apps/api/tests/test_architecture.py`

- [x] **Step 1: Write failing error/model tests**

Define expected public Python API in tests:

```python
class FakePsycopgError(Exception):
    def __init__(self, sqlstate: str, message: str) -> None:
        super().__init__(message)
        self.sqlstate = sqlstate

def test_sqlstate_maps_without_parsing_message() -> None:
    for sqlstate, code in {
        "P1001": DatabaseRuleCode.FORBIDDEN_ACTOR_ROLE,
        "P1002": DatabaseRuleCode.SELF_APPROVAL,
        "P1003": DatabaseRuleCode.INVALID_CANDIDATE_STATE,
        "P1004": DatabaseRuleCode.INCOMPLETE_CANDIDATE,
        "P1005": DatabaseRuleCode.DISALLOWED_ORIGIN,
        "P1010": DatabaseRuleCode.INVALID_INTERACTION,
    }.items():
        error = map_database_error(FakePsycopgError(sqlstate, "synthetic private text"))
        assert error.code is code
        assert "synthetic private text" not in str(error)

def test_actor_and_event_validation_rejects_unsafe_combinations() -> None:
    with pytest.raises(ValueError):
        Actor(actor_id=" ", role=AdminRole.OPERATOR)
    with pytest.raises(ValueError):
        InteractionWrite(
            request_id=uuid4(),
            intent=Intent.OUT_OF_SCOPE,
            answer_status=AnswerStatus.FALLBACK,
            fallback_reason=FallbackReason.OUT_OF_SCOPE,
            used_source_ids=(),
            response_time_ms=1,
            selected_region=None,
            routed_office_public_id=None,
            is_test=False,
            masked_question="must not persist",
        )
```

- [x] **Step 2: Run focused tests and confirm RED**

Run:

```powershell
uv run --directory apps/api --frozen pytest -q -p no:cacheprovider tests/db/test_errors.py tests/db/test_models.py
```

Expected: import failures for missing DB modules.

- [x] **Step 3: Implement frozen typed models**

Use `str, Enum` enums whose values exactly match PostgreSQL enums. Use frozen, slotted dataclasses for:

```python
Actor(actor_id: str, role: AdminRole)
InteractionWrite(request_id, intent, answer_status, fallback_reason, used_source_ids,
                 response_time_ms, selected_region, routed_office_public_id,
                 is_test, masked_question)
InteractionWriteResult(interaction_id, failed_question_id)
FailureReasonConfirmation(failed_question_id, actor, fallback_reason)
CandidateDraft(failed_question_id, actor, title, representative_question, category,
               answer_summary, procedure_steps, required_documents, processing_time,
               fee, department, source_title, source_url, last_verified_at, caution,
               data_origin)
KnowledgeRecord(public_id, category, service_name, answer_summary, procedure_steps,
                required_documents, processing_time, fee, department, source_title,
                source_url, last_verified_at, caution, question_examples)
OfficeRecord(public_id, region, office_name, address, phone, opening_hours, map_url,
             department_label, source_title, source_url, last_verified_at)
PurgeResult(purged_count, purged_ids)
```

Backend validation duplicates the DB's simple structural checks: trimmed IDs/text, supported intent/region, unique sources, non-negative response time, exact fallback matrix, no OUT_OF_SCOPE retained text, non-empty string arrays, and actor role checks. It does not attempt cross-row validation that belongs to the transaction.

- [x] **Step 4: Implement stable domain errors**

`DatabaseRuleError` exposes only `code` and a stable safe message from an internal constant map. `map_database_error(exc)` reads only `exc.sqlstate`; listed states map to `DatabaseRuleError`, while unlisted DB exceptions become `DatabaseUnavailableError("DATABASE_OPERATION_FAILED")` with the original exception chained but not stringified or logged.

- [x] **Step 5: Write failing repository/pool tests**

Use async fake pool/connection/cursor objects to verify methods call only these fixed statements with positional parameters: `SELECT * FROM app_api.list_active_kb(%s)`, `SELECT * FROM app_api.list_offices(%s, %s)`, `SELECT * FROM app_api.record_interaction(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)`, `SELECT app_api.confirm_failed_question_reason(%s, %s, %s, %s)`, `SELECT app_api.create_kb_candidate(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)`, `SELECT app_api.submit_kb_candidate(%s, %s, %s)`, `SELECT app_api.approve_kb_candidate(%s, %s, %s, %s)`, `SELECT app_api.reject_kb_candidate(%s, %s, %s, %s)`, and `SELECT * FROM app_api.purge_expired_failed_question_text()`. Verify commit on success, rollback on failure, typed row mapping, and absence of question/answer text in exception output. Extend `test_architecture.py` so importing `sejong_ai_api.main` does not import `psycopg` or construct a pool.

- [x] **Step 6: Implement explicit lazy pool creation**

`pool.py` must contain only:

```python
from psycopg_pool import AsyncConnectionPool

def create_pool(database_url: str) -> AsyncConnectionPool:
    if not database_url.strip():
        raise ValueError("DATABASE_URL_REQUIRED")
    return AsyncConnectionPool(
        conninfo=database_url,
        min_size=1,
        max_size=4,
        open=False,
        kwargs={"autocommit": False},
    )
```

No module reads environment variables and no pool opens at import time.

- [x] **Step 7: Implement the repository protocol and adapter**

`SejongRepository` declares these exact async methods and return types: `list_active_kb(intent: Intent) -> Sequence[KnowledgeRecord]`, `list_offices(region: Region, intent: Intent) -> Sequence[OfficeRecord]`, `record_interaction(event: InteractionWrite) -> InteractionWriteResult`, `confirm_failed_question_reason(failed_question_id: UUID, actor: Actor, fallback_reason: FallbackReason) -> None`, `create_kb_candidate(draft: CandidateDraft) -> UUID`, `submit_kb_candidate(candidate_id: UUID, actor: Actor) -> None`, `approve_kb_candidate(candidate_id: UUID, actor: Actor, review_comment: str) -> str`, `reject_kb_candidate(candidate_id: UUID, actor: Actor, review_comment: str) -> None`, and `purge_expired_failed_question_text() -> PurgeResult`. Import `Sequence` from `collections.abc`; the concrete adapter returns immutable tuples and both read methods allow an empty result.

`PsycopgSejongRepository` receives an already-created pool and uses `async with pool.connection()` plus `async with connection.transaction()` for writes. Reads use a connection context and row factory; no method accepts raw question, answer, context token, role header, or arbitrary SQL. Reason confirmation and candidate approval/rejection accept a pre-resolved `Actor` rather than an HTTP header value; both review paths require a validated non-empty comment.

All SQL strings are module constants with fixed `app_api` function names. Parameters are passed separately. Catch `psycopg.Error`, call `map_database_error`, and raise the mapped exception without logging values.

- [x] **Step 8: Run API verification**

Run:

```powershell
uv run --directory apps/api --frozen ruff format --check src tests
uv run --directory apps/api --frozen ruff check src tests
uv run --directory apps/api --frozen mypy src tests
uv run --directory apps/api --frozen pytest -q -p no:cacheprovider
```

Expected: all checks pass, `/health` behavior is unchanged, `/ready` remains 503, and no public route imports the repository.

- [x] **Step 9: Commit Task 8**

```powershell
git add apps/api/src/sejong_ai_api/db apps/api/tests/db apps/api/tests/test_architecture.py
git commit -m "feat(api): add lazy typed database boundary"
```

**Actual Task 8 evidence (2026-07-17 KST):**

- Base `ab86c09`; implementation commit `3cae552`, exactly the ten declared Task
  8 files and no route, contract, migration, seed, dependency, lock, or version
  change.
- Phase 1 RED was two missing `sejong_ai_api.db` imports; focused GREEN was
  81 passed. Phase 2 RED was the missing pool module; focused GREEN was 31
  passed plus four unittest subtests.
- An interim ACTIVE-read invariant review added two failing question-example
  tests before the minimal validator made both pass.
- Fresh agent and root verification passed Ruff format for 22 files, Ruff lint,
  strict Mypy for 22 files, and full API pytest with 156 passed plus four
  unittest subtests. One pinned Starlette/httpx deprecation warning is non-
  failing and requires a separately approved dependency change.
- Secret, package, whitespace, exact owned-file, and Task-8 scope checks passed.
  Global `check_scope_drift.py` remains baseline-red only for
  `PACKAGE_MANIFEST.json` and ignored `.tools/isolated-repo`; no Task 8 file is
  reported.
- Independent review of `ab86c09..3cae552` reported Critical 0, Important 0,
  Minor 0. Full evidence: `.superpowers/sdd/task-8-report.md` and
  `docs/implementation-notes/IMP-20260717-003-db-001-task-8-lazy-typed-database-boundary.md`.

## Task 9: Prove concurrency, idempotency, retention boundaries, and rollback/replay

**Files:**

- Create: `apps/api/tests/db/test_integration.py`
- Modify: `scripts/verify_database.ps1`
- Modify: `scripts/tests/test_supabase_tooling.py`

- [x] **Step 1: Write local-only integration tests**

Mark the module with `pytestmark = pytest.mark.skipif(not os.getenv("SEJONG_DB_TEST_URL"), reason="local DB gate only")`. Tests must use unique synthetic IDs and transaction cleanup. Create exactly these eight async tests: `test_identical_request_replay_writes_one_event`, `test_conflicting_request_replay_maps_p1010`, `test_two_concurrent_reason_confirmations_write_one_audit`, `test_candidate_creation_requires_confirmed_reason`, `test_two_concurrent_approvals_create_one_active_kb_and_audit`, `test_purge_boundary_is_exact_and_idempotent`, `test_backend_login_cannot_select_private_tables`, and `test_mock_and_non_active_rows_never_reach_citizen_reads`.

For each concurrent test, use two independent connections released by one `asyncio.Event`. Reason confirmation must produce one `REASON_CONFIRMED` failure, preserve the event reason, write one metadata audit, and map the loser to `P1003`. Approval must return one KB public ID, map the loser to `P1003`, and leave one KB, one candidate link, and one approval audit. Test strings are synthetic and marked MOCK except the minimal OFFICIAL approval fixture required to prove activation.

- [x] **Step 2: Run the integration test without a DB URL**

Run:

```powershell
uv run --directory apps/api --frozen pytest -q -p no:cacheprovider tests/db/test_integration.py
```

Expected: all tests skip with the exact reason `local DB gate only`; no implicit connection occurs.

- [x] **Step 3: Complete runner tests for failure and environment restoration**

Add synthetic child-command fixtures to prove the PowerShell runner:

- preserves child exit code for DB test failures;
- suppresses child output containing sentinel DSNs/questions;
- restores `SEJONG_ADMIN_DATABASE_URL` and `SEJONG_DB_TEST_URL` on success and failure;
- runs compensation files in exact `00600`, `00500`, `00400`, `00300`, `00200`, `00100` order;
- runs absence proof before the second reset;
- never reads or replaces `LLM_API_KEY`.

- [x] **Step 4: Run the full disposable-local DB gate**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_database.ps1
```

Expected stable phases all pass:

```text
PREFLIGHT-DOCKER
VERIFY-SUPABASE-VERSION
START-LOCAL-DATABASE
RESET-DATABASE-ONE
PROVISION-LOCAL-DB-LOGIN-ONE
TEST-PGTAP-ONE
ROLLBACK-DB001
VERIFY-DB001-ABSENT
RESET-DATABASE-TWO
PROVISION-LOCAL-DB-LOGIN-TWO
TEST-PGTAP-TWO
TEST-DATABASE-INTEGRATION
```

No DSN, key, password, question, SQL statement, Docker credential, or Supabase status payload may appear in stdout/stderr.

- [x] **Step 5: Run the no-Docker gate again**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1
```

Expected: existing 24-stage gate still exits 0 and does not start or require Docker.

### Task 9 historical RED and resolved Q-DB-003 — 2026-07-17 KST

The following evidence preserves the pre-remediation RED. The complete gate now
passes and the Task 9 checkboxes are checked; do not reinterpret the history as
the final state.

- With both DB URL environment names absent from the child process, exactly eight
  integration tests skip with reason `local DB gate only` and no implicit
  connection.
- The stale compensation-order test failed first. After the runner-only fix,
  `LocalDatabaseToolingContractTests` passes 16/16 and proves exact
  `00500 → 00400 → 00300 → 00200 → 00100`, child exit preservation, sentinel
  suppression, environment restoration, absence-before-reset ordering, and no
  LLM key token in runner source.
- The disposable gate passes reset one, pgTAP 274/274, five-file rollback,
  DB-001 absence, reset/replay two, and pgTAP 274/274. Real-DB integration is
  exactly 6 passed and 2 failed; both failures are backend approval paths.
- Safe catalog evidence is `validate_active_kb_question()`
  `prosecdef=false` and backend private-schema usage=false. The SECURITY DEFINER
  approval function reaches commit, where the deferred SECURITY INVOKER trigger
  cannot read its private tables. SQLSTATE `42501` is reduced to the fixed
  `DatabaseUnavailableError`; native diagnostics are not exposed.
- Both failed approval transactions roll back atomically: candidate remains
  PENDING_APPROVAL, activated link is NULL, and activated KB, required question,
  and approval audit counts are zero. Cleanup leaves events, failures,
  candidates, KB documents, questions, offices, mappings, and audits all zero.

`Q-DB-003` is resolved by D-028/ADR-0012. After option A was recommended, the
user wrote `이거 끝나면 계속해서 진행해줘. 5시간 동안 루프 ㄱㄱ`; this is recorded as
approval of the immediately preceding recommendation, not as a literal typed
`A`. The linked Task 9A plan adds a new versioned `00600` that makes only
`app_private.validate_active_kb_question()` SECURITY DEFINER, reasserts owner,
pins `search_path=pg_catalog, pg_temp` with the temporary schema last, and revokes
direct EXECUTE; matching compensation restores SECURITY INVOKER. Do not grant
backend private-schema access, add a repository/admin-DSN workaround, modify an
applied migration, or proceed to Task 10 before the remediation and full Task 9
gate pass. API contracts, data, package dependencies, and remote/public
deployment remain unchanged. Historical 6/8 evidence remains in
`docs/implementation-notes/IMP-20260717-004-db-001-task-9-deferred-trigger-permission-blocker.md`.

### Task 9 completion evidence — 2026-07-17 KST

- RED: real integration 6 pass/2 fail; corrected `006` pgTAP 2/8 meaningful
  failures after collation correction; two focused tooling order failures.
- GREEN: focused `006` 8/8, full pgTAP `Files=6, Tests=282`, `00600`-only full
  posture PASS, compensated prior five `Files=5, Tests=274`.
- retained diagnostic branch integration 8/8, then branch removal and integration
  8/8. Review fix `228d8cb` consolidated cleanup into one identifier-scoped admin
  transaction without changing the eight public assertions.
- full gate passed `006→005→004→003→002→001`, absence, reset/replay, second
  pgTAP 282, and integration 8/8. Tooling 16/16, Ruff format/lint, strict Mypy,
  root/web/API/contract/secret/package/diff and synthetic eight-table zero passed.
- implementation commits: `5266abc` (authorized four-path SQL/test correction;
  stale `002_invariants_test.sql` assertion only, immutable migration edit 0),
  `04a944f` (Task 9 three paths), `228d8cb` (integration evidence fix one path).
- independent initial specification review found Important 1/Minor 1; `228d8cb`
  resolved both. Final specification and quality reviews are each 0/0/0.
- root coordinator independently reran full DB gate exit 0, pgTAP 282, root gate
  exit 0, tooling 16/16, no-URL exact 8 skips, zero-row PASS, protected-scope diff
  0, and clean worktree.
- A-021 remains a B/High local follow-up and public-release blocker. Task 10 must
  preserve that caveat and must not mark public deployment ready.

- [x] **Step 6: Commit Task 9**

```powershell
git add apps/api/tests/db/test_integration.py scripts/verify_database.ps1 scripts/tests/test_supabase_tooling.py
git commit -m "test(db): verify rollback replay and concurrent approval"
```

## Task 10: Synchronize schema authority, versions, changelog, and handoff evidence

**Files:**

- Modify: `database/schema-v1.draft.sql`
- Modify: `database/README.md`
- Modify: `SECURITY.md`
- Modify: `apps/api/README.md`
- Modify: `scripts/README.md`
- Modify: `scripts/verify_database.ps1`
- Modify: `scripts/tests/test_supabase_tooling.py`
- Modify: `docs/03_ARCHITECTURE.md`
- Modify: `docs/04_DOMAIN_AND_STATE_MODEL.md`
- Modify: `docs/07_SECURITY_PRIVACY.md`
- Modify: `docs/08_TEST_STRATEGY.md`
- Modify: `docs/13_IMPLEMENTATION_WORKFLOW.md`
- Modify: `docs/14_REPOSITORY_STRUCTURE.md`
- Modify: `docs/15_DEPLOYMENT_AND_OPERATIONS.md`
- Modify: `docs/16_HANDOFF_GUIDE.md`
- Modify: `docs/11_AMBIGUITY_REGISTER.md`
- Modify: `docs/12_VERSIONING_AND_RELEASES.md`
- Modify: `docs/adr/0011-layered-database-and-backend-enforcement.md`
- Modify: `docs/decisions/DECISION_LOG.md` (D-018/D-025 status only)
- Modify: `docs/discovery/DB_001_DISCOVERY_REPORT.md` (append-only current status)
- Modify: `docs/source-of-truth/TEAM_DECISIONS.md` (local/public boundary only)
- Modify: `docs/superpowers/specs/2026-07-16-db-001-layered-enforcement-design.md`
- Modify: `CODEX_FILE_INDEX.md`
- Modify: `README.md`
- Modify: `TASKS.md`
- Inspect and preserve DB/repo/test axes unchanged until D-031 exact runtime/full gate passes: `versions/manifest.json`
- Modify: `CHANGELOG.md`
- Create: `docs/test-reports/DB-001-LOCAL-BASELINE.md`
- Modify: `docs/test-reports/README.md`
- Create: `docs/handoffs/HANDOFF-20260717-DB-001-LOCAL-BASELINE.md`
- Modify: `docs/implementation-notes/IMP-20260716-006-db-001-layered-enforcement.md`
- Create: `docs/implementation-notes/IMP-20260717-007-db-001-local-baseline-closeout.md`
- Modify: `docs/implementation-notes/INDEX.md`
- Preserve unchanged: `PACKAGE_MANIFEST.json` (the original 2026-07-14 package snapshot, not an active generated-file inventory)

The additional active files above contained materially stale pre-DB, Tasks 0~5, or public-boundary
claims discovered during Task 10 preflight. Historical task notes and legacy remain unchanged.

- [x] **Step 1: Make migration lineage authoritative**

Change the logical draft header to state that it is a readable logical projection of migration baseline `0.3.0-local`, not executable authority. Update its shape to match the seven enums/eight tables/provenance changes without copying grants/functions into the projection. `database/README.md` must state:

```text
Executable authority: supabase/migrations/ in timestamp order.
Compensation: database/rollbacks/ in reverse timestamp order, disposable local DB only.
Logical projection: database/schema-v1.draft.sql.
Official seed authority: not populated; DATA-SEED-001 remains blocked on PM-approved DATA-001.
```

- [x] **Step 2: Update operating and security documentation**

Document exact bootstrap, runner-owned loopback start, full DB verify, optional stop, local credential rotation, rollback/replay, and no-seed readiness behavior. The runner must reject Docker Engine below 28 and any network/container/runtime binding drift before reset or credential handling. Explicitly warn that the local stack has default development credentials, no TLS/rate limits, and must not be publicly exposed. Preserve separate approval gates for remote DB, public admin, data deletion, production backup, and CORS/domain changes.

- [x] **Step 3: Update task state, dependencies, and versions after fresh safe-runtime evidence passed**

Set DB-001 to Done only after Task 9 evidence plus the Task 10 exact-loopback/full-gate/review evidence.
Unblock dependencies only by replacing `DB-001` with their remaining real dependencies; do not mark
DATA-001, DATA-SEED-001, READY-001, AI-001, LOG-001, or BACKUP-001 done.

Task 9 evidence alone is insufficient after the Task 10 port finding. Q-SEC-004=A/D-029 applied
`default-local-port-binding` and Q-SEC-005=A/D-030 applied `local-only-port-binding`, but both actual
HostIP-omitted probes resolved to `127.0.0.1` plus IPv6 wildcard `::`. Explicit `127.0.0.1` controls were
single-loopback. Until D-031 implementation and the exact gate pass, keep DB-001
Blocked, preserve every downstream `DB-001` dependency, and keep every manifest axis at its current HEAD
value. Apply the following promotion only after exact single-loopback runtime, fresh full DB/root/static
verification, and independent reviews all pass.

Apply version changes:

```json
{
  "repo_guidance": "1.5.0",
  "application": "0.1.0",
  "web": "0.1.0",
  "api": "2.0.1-draft",
  "shared_contracts": "0.2.1",
  "database_schema": "0.3.0-local",
  "official_data": "0.0.0-not-populated",
  "mock_data": "0.0.0-not-populated",
  "prompt_set": "0.0.2-deepseek-v4-flash-selected",
  "test_suite": "0.5.0-db-baseline",
  "documentation": "2.4.0"
}
```

Set documentation to `2.4.0` for the new executable DB baseline. Do not change product spec or API wire versions.

- [x] **Step 4: Write the blocked candidate DB report and implementation note**

The report records exact CLI/PostgreSQL/Docker versions, all six migration/compensation files and hashes, pgTAP assertion totals, API test total, reset count, `00600 → 00500 → 00400 → 00300 → 00200 → 00100` rollback order, reason-confirmation and approval concurrency results, secret-output scan result, root gate result, and `/ready=503`. The implementation note follows the repository template and includes 6W1H, commands/results, versions before/after, security/privacy/data impact, rollback, risks, and human/AI boundary.

- [x] **Step 5: Preserve the original package and version manifests and inspect active files**

Run:

```powershell
git diff --exit-code -- PACKAGE_MANIFEST.json
rg --files -g '!legacy/**' -g '!.tools/**' -g '!supabase/.temp/**' -g '!supabase/.branches/**'
```

Expected: the original package snapshot is unchanged. The manifest's DB/repo/test axes stay unpromoted;
documentation may advance for D-031 design lineage. The active file inventory contains all DB-001 tracked
files while ignored `.tools/`, `.env`, Supabase temporary directories, Docker state, and backups are absent.

- [x] **Step 6: Rerun final verification-before-completion after closeout docs and review fixes**

Invoke `superpowers:verification-before-completion`, then run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_database.ps1 -SkipStart
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1
apps/api/.venv/Scripts/python.exe -B scripts/validate_codex_package.py
apps/api/.venv/Scripts/python.exe -B -c "import json, pathlib; json.loads(pathlib.Path('versions/manifest.json').read_text(encoding='utf-8')); json.loads(pathlib.Path('PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1
git diff --check
git status --short
```

Expected: the DB runner first proves an actual loopback-only Docker port and only then both verification gates exit 0; package/JSON/secret/diff checks pass, and Git status lists only intended DB-001 docs/report/note/security-runner changes before the final commit. The known historical `check_scope_drift.py` false positive against the immutable package snapshot is not used as a DB-001 completion gate.

- [x] **Step 7: Complete final independent reviews and resolve all Critical/Important findings**

Invoke `superpowers:requesting-code-review`. The specification reviewer checks every approved-spec requirement. The code-quality reviewer checks SQL injection, `SECURITY DEFINER` search paths, grants/RLS, race behavior, error privacy, env preservation, compensation scope, tests, and documentation/version drift. Resolve all P0/P1 findings and rerun Step 6.

- [x] **Step 8: Parent commits Task 10 after final diff inspection**

```powershell
git add database docs CODEX_FILE_INDEX.md README.md TASKS.md versions/manifest.json CHANGELOG.md scripts/README.md apps/api/README.md
git commit -m "docs(db): record executable local baseline"
```

## Acceptance traceability

| Approved requirement | Implemented by | Proved by |
|---|---|---|
| private base schema, no browser direct access | Tasks 3, 5 | schema and capability pgTAP |
| eight tables, explicit OFFICIAL/MOCK provenance | Tasks 3, 4 | schema/invariant pgTAP |
| raw question/answer/transcript/token/IP/device absent | Tasks 3, 4, 8 | catalog and Python privacy tests |
| OUT_OF_SCOPE text 0, FOLLOWUP failure 0 | Task 5 | capability pgTAP and integration |
| 30-day NULL purge, row/FK preserved | Tasks 4, 5, 9 | boundary/idempotency tests |
| ACTIVE+OFFICIAL KB/office only | Task 7 | citizen-read pgTAP/integration |
| author cannot self-approve | Tasks 6, 8 | approval pgTAP/model tests |
| reason confirmation preserves event and gates candidate eligibility | Tasks 6, 8, 9 | approval pgTAP/repository/two-connection tests |
| atomic approval and concurrency safety | Tasks 6, 9 | pgTAP plus two-connection test |
| audit metadata only and append-only | Tasks 4, 6 | catalog/grant/approval tests |
| fixed-search-path SECURITY DEFINER and narrow execute grants | Tasks 5-7 | catalog privilege tests |
| DB and backend duplicate enforcement | Tasks 4-8 | SQL and Python unit/integration tests |
| exact pinned CLI, local-only, no new production dependency | Tasks 1, 2 | tooling contract and manifest review |
| compensation rollback and fresh replay | Tasks 2, 9 | explicit DB gate |
| no approved seed keeps readiness 503 | Tasks 2, 8-10 | API/root gates and report |
| remote/public/destructive real-data work excluded | all tasks | command allowlist, docs, code review |

## Human approval boundaries during execution

Work stops and returns to the user before any of these changes:

- replacing Supabase CLI `v2.109.1` or its digest;
- adding a production dependency;
- changing a public HTTP schema, route, status, or error code;
- adding official/mock seed or marking data ACTIVE;
- linking/pushing a remote Supabase project or exposing local ports publicly;
- changing retention from 30 days or storing new text/identifier fields;
- changing admin actor/approval policy;
- running compensation against anything other than the disposable local project;
- altering deployment, CORS, domain, cloud backup, cost, or quota policy.

## Rollback and recovery summary

- Before the executable DB baseline exists: revert the task commit.
- On the disposable local DB: run compensation in `00600 → 00500 → 00400 → 00300 → 00200 → 00100`, execute absence proof, then reset/replay.
- After a migration commit is shared: never edit an applied migration; add a reviewed forward migration.
- Do not delete Docker volumes directly. `supabase stop` is allowed as a non-destructive local stop; volume deletion needs an explicit user decision if non-reproducible data exists.
- `apps/api/.env` is ignored and preserved. If local credential provisioning fails, rerun it after reset; do not copy credentials into tracked files.
- Official data has no row in this plan, so rollback cannot delete PM-approved official records.

## Verified local/private completion state

- DB-001 is Done with reproducible local evidence.
- PostgreSQL and FastAPI both enforce the approved structural safety rules.
- `/health=200` and `/ready=503` remain unchanged because no approved official seed exists.
- DATA-001 remains owned by AI/Data·Backend with PM approval target 2026-07-20.
- The next vertical slice is DATA-SEED-001 only after DATA-001 approval; READY-001 follows the seed, not this database baseline.
- A-021/Q-SEC-003 default B keeps remote/public deployment, public admin/API, and public backend DB credentials blocked; no `00700` is created without a human decision.

## Current closeout state

- DB-001 is Done for disposable local/private use and `database_schema=0.3.0-local` is active.
- DATA-SEED-001, READY-001, LOG-001, and BACKUP-001 removed only the satisfied direct DB-001 dependency;
  their remaining real blockers keep them Blocked.
- Q-SEC-006=A/D-031 and Q-TOOL-001=A/D-032 produced the pinned patched runtime and actual full gate.
- Runner descendant-cleanup finding is fixed by `73f300b`; focused/full tests, independent review 0/0/0 and
  final-code DB gate passed. Final specification and quality docs reviews are also APPROVED 0/0/0,
  full final verification passed, and the closeout commit is complete.
