# DATA-SEED-001 Immutable Official Release and Local Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** PM이 승인한 DATA-001의 19 KB·3기관·10매핑만 불변 공식 release로 승격하고, 기존 PostgreSQL schema의 빈 disposable local DB에 transactional seed·compensation·replay를 재현 가능하게 검증한다.

**Architecture:** canonical staging과 hash-bound approval manifest를 dependency-free Python projection/generator가 검증한 뒤, same-parent prepare와 별도 dispatcher activation의 두 단계로 release를 게시한다. 생성 SQL은 exact local migration principal, 8-table `ACCESS EXCLUSIVE` lock, empty preflight와 양방향 semantic equality를 transaction 안에서 강제하고, 저장소 runner가 patched Supabase gate와 실제 DB seed→compensation→seed replay를 검증한다. 새 migration/API/runtime readiness는 만들지 않는다.

**Tech Stack:** Python 3.12.13 standard library, `unittest`, existing psycopg 3.3.4, PowerShell 5.1, PostgreSQL 17, pinned project-local Supabase CLI v2.109.1, Docker Desktop, JSON Schema Draft 2020-12 documents, Git.

## Global Constraints

- canonical input은 정확히 `data/staging/data-001/0.1.0-draft.1/`이고 alias·absolute path·symlink/junction/reparse component를 거부한다.
- initial release는 정확히 `0.1.0-initial.1`, `release_id=sejong-official-0.1.0-initial.1`이다.
- `released_at`은 written specification 승인 시각 `2026-07-19T09:20:31+09:00`으로 고정한다. 이는 실제 파일시스템 clock이 아니라 initial release에 대한 인간 governance 승인 시각이다.
- reviewer는 `PM-LOCAL-001`, author는 `AI-DATA-BACKEND`, approved projection은 KB 19·office 3·mapping 10이다.
- `KB-WASTE-03`, `OFFICE-AREUM:LOCAL_TAX_GENERAL`, `OFFICE-DODAM:BULKY_WASTE`와 mock은 release/DB에서 0건이어야 한다.
- release 경로는 `data/official/releases/0.1.0-initial.1/`이며 create-once다. 성공한 release byte를 수정·삭제·덮어쓰지 않는다.
- `supabase/seed.sql`은 별도 activation 뒤 release의 `seed.sql`과 byte-identical이어야 한다. `[db.seed].enabled=false`는 유지한다.
- supported importer는 `scripts/verify_data_seed.ps1 -ReleaseVersion 0.1.0-initial.1` 하나다. manual SQL 실행은 지원하지 않는다.
- admin DSN identity는 user `postgres`, host `127.0.0.1`, port `54322`, database `postgres`와 정확히 일치해야 하며 값은 출력·파일 저장하지 않는다.
- SQL은 `session_user/current_user/current_database`, `postgres → sejong_schema_owner` membership의 `admin_option/inherit_option/set_option`, role switch 결과를 fail closed로 확인한다.
- transaction advisory lock key는 `20260719001`, `lock_timeout`은 `5s`로 고정한다.
- table lock 순서는 `kb_documents`, `kb_question_examples`, `offices`, `office_service_mappings`, `interaction_events`, `failed_questions`, `kb_candidates`, `audit_logs`다.
- seed와 compensation은 explicit columns와 generated expected-row CTE를 사용하고, 모든 seed-owned column을 양방향 `EXCEPT ALL`로 비교한다.
- compensation은 exact seed projection이고 operational/reference table이 비어 있는 disposable local DB에서만 허용한다.
- citizen raw question, PII, transcript, context token, IP/device ID, provider payload, secret, approval comment를 application table/log에 넣지 않는다.
- 새 production/dev dependency, migration, role/grant, public API, UI, LLM, remote/cloud operation, `/ready=200` 전환은 금지한다.
- `official_data=0.1.0-initial.1`은 release 검증과 실제 DB seed/compensation/replay가 모두 성공한 뒤에만 기록한다.

---

## 상태

- Plan ID: `DATA-SEED-001-PLAN`
- 상태: **Blocked** — filesystem release/dispatcher와 offline root gate는 완료, actual DB는
  seed write 전 A-030/Q-SEED-002 membership-contract 결정 대기
- 명세 승인: 2026-07-19T09:20:31+09:00, 사용자의 직전 승인 요청에 대한 `ㅇㅋ 승인`
- 실행 승인: 2026-07-19T09:52:08+09:00, 사용자 `ㅇㅋ 전체 승인 구현 ㄱㄱ`
- 승인 명세: `docs/superpowers/specs/2026-07-19-data-seed-immutable-release-design.md`
- 결정/ADR: D-036, D-038, A-028, ADR-0015, ADR-0016
- 실행 결과: Task 5 `.1` 19/3/10 filesystem publication/review PASS; Task 6 actual DB Blocked;
  Task 7A no-Docker root gate/review PASS; Task 7B documentation/version blocked-state synchronization
- 계획 시점 branch: `main`; 승인 뒤 `codex/data-seed-001-initial-release`
- 현재 상태: filesystem release 1개(`.1` 19/3/10), byte-active dispatcher,
  `[db.seed].enabled=false`; actual DB seed 0, `official_data=0.0.0-not-populated`, `/ready=503`,
  repo-owned runtime container/port listener 0

## 목표와 비목표

목표:

- exact PM-approved bytes에서 deterministic 19/3/10 official release를 생성한다.
- approval/content/release/semantic hash 계보를 재현한다.
- prepare와 dispatcher activation을 독립적으로 실패·복구·재시도할 수 있게 한다.
- fresh migration-only local DB에서 seed, second-seed rejection, forced rollback, compensation guard, replay, concurrency를 검증한다.
- 시민 read capability가 승인된 19 KB만 반환하고 제외 record/mock이 0임을 증명한다.
- official data version, lineage, test report, TASKS와 인수인계 문서를 실제 결과에 맞게 동기화한다.

비목표:

- WASTE-03의 20번째 ACTIVE 승격, REG-001, READY-001, retrieval/chat/admin 기능.
- DB release ledger, migration, SECURITY DEFINER, 새 privilege나 dependency.
- non-empty/remote/live DB의 데이터 전환 또는 compensation.
- immutable release의 in-place correction/deletion.

## 사용자 가치와 인수 기준

- 승인한 35개 disposition 중 정확한 19/3/10만 시민 근거 후보가 되고 보류·반려·mock은 섞이지 않는다.
- 같은 input과 explicit release timestamp로 서로 다른 temp root에서 생성한 7개 release 파일이 byte-identical하다.
- release path가 이미 있으면 identical 여부와 무관하게 write 0으로 실패한다.
- prepare 실패는 release absent, activation 실패는 verified release retained + 이전 dispatcher restored 상태다.
- fresh DB seed 후 exact 19 ACTIVE/OFFICIAL KB, 3 OFFICIAL office, 10 mapping과 authored question examples가 존재한다.
- 두 번째 seed, altered/non-empty DB compensation, wrong principal/DSN, concurrent conflicting write는 partial mutation 0으로 실패한다.
- seed→compensation→seed가 같은 semantic SHA-256과 citizen result를 만든다.
- `supabase/seed.sql`과 release seed가 byte-identical이고 root verify가 Docker 없이 이를 계속 검사한다.
- API/DB schema/application/web/mock/prompt version과 `/ready=503`은 변하지 않는다.

## 권위 근거

- RFP: DAR-001, DAR-002, SER-001, SER-003, COR-001
- source-of-truth: `TEAM_DECISIONS`, `PROJECT_PLAN` §6, `KB_GUIDE`, `APPROVAL_POLICY`, `PRIVACY_POLICY`
- ADR: ADR-0003, ADR-0008, ADR-0011, ADR-0015, ADR-0016
- executable DB authority: `supabase/migrations/20260716000100` through `20260717000600`
- approved DATA input: `data/staging/data-001/0.1.0-draft.1/approval_manifest.json`
- previous notes: IMP-20260719-004, IMP-20260719-006, IMP-20260719-007

## 현재 상태와 조사 결과

- DATA-001 canonical manifest는 `APPROVED_FOR_INITIAL_RELEASE`, 35개 decision/comment와 exact 19/3/10 projection을 가진다.
- 계획 작성 시점에는 official release directory가 없고 dispatcher가 data-free였다. Task 5 후
  `data/official/releases/0.1.0-initial.1/`이 게시됐고 `supabase/seed.sql`은 release seed와
  byte-identical이다. 자동 reset seed는 계속 disabled다.
- DB schema는 migration 6개, table 8개, disposable local `0.3.0-local`; public release는 Q-SEC-003/A-021로 별도 차단된다.
- Task 7A가 no-Docker root verify에 DATA-SEED unit, `verify-release`, `verify-local-seed`를 추가했고
  actual root gate를 PASS했다.
- `scripts/run_database_sql.py`는 의도적으로 `database/` 아래 SQL만 허용하므로 release SQL 실행에 재사용하지 않는다.
- `database/README.md`의 stale release/dispatcher 상태를 Task 7B에서 actual Blocked 결과로 정정한다.
- 현재 A blocker는 A-030/Q-SEED-002다. A는 successor `.2` release, B는 grantor membership
  정규화 migration이며 인간 선택 전 둘 다 구현하지 않는다.

## 미지의 영역과 인터뷰

| ID | 영향 | 질문 | 상태 | 결정 |
|---|---|---|---|---|
| Q-SEED-001 | data architecture/rollback | official release·seed 방식 | Resolved | A / D-036 / ADR-0016 |
| DATA-SEED-SPEC | public data/DB | written specification 승인 | Resolved | 2026-07-19T09:20:31+09:00 승인 |
| DATA-SEED-PLAN | implementation/data mutation | 이 실행계획으로 release/DB 작업 시작 | Resolved / In Progress | 2026-07-19T09:52:08+09:00 전체 승인; D-039 |
| Q-SEC-003 | public deployment | privileged function hardening | Open but out of scope | default B; public/remote 금지 |
| RELEASE-TIME | lineage | `released_at` literal | Resolved default | written specification 승인 시각 `2026-07-19T09:20:31+09:00`; ambient clock 사용 금지 |

## 권위 파일 맵

| Path | 책임 |
|---|---|
| `data/schemas/data-seed/v1/*.schema.json` | release manifest와 projected KB/office/mapping의 strict contract |
| `scripts/data_seed_release.py` | strict JSON, input trust, canonical projection/hash, release verification |
| `scripts/data_seed_sql.py` | explicit SQL literal, expected-row CTE, seed/compensation serialization |
| `scripts/promote_data_seed.py` | prepare/verify-release/activate/verify-local CLI와 path boundary |
| `scripts/verify_data_seed_db.py` | exact DSN/session 확인, DB cycle와 semantic hash evidence |
| `scripts/test_data_seed_concurrency.py` | two-connection lock/preflight race 검증 |
| `scripts/verify_data_seed.ps1` | patched DB gate→reset→failure/concurrency/cycle orchestration, env 복원 |
| `scripts/tests/test_data_seed_release.py` | trust/projection/canonicalization/SQL unit tests |
| `scripts/tests/test_promote_data_seed.py` | path/reparse/publication/activation failure tests |
| `scripts/tests/test_verify_data_seed_db.py` | DSN identity, query projection, stable output tests |
| `scripts/tests/test_verify_data_seed_runner.py` | PowerShell runner allowlist/order/env/static regression tests |
| `data/official/releases/0.1.0-initial.1/` | immutable 7-file official release authority |
| `supabase/seed.sql` | verified byte-identical local dispatcher; automatic reset seed disabled |
| `docs/data-lineage/DATA-SEED-001-0.1.0-initial.1.md` | approval→release→DB hashes, exact commands and recovery boundary |
| `docs/test-reports/DATA-SEED-001-LOCAL-VERIFICATION.md` | real disposable DB counts/hash/replay/concurrency evidence |

## 내부 인터페이스

`scripts/data_seed_release.py`의 exact type/signature contract:

| 이름 | 반환/필드 계약 |
|---|---|
| `ReleaseIssue` | frozen/orderable dataclass: `code`, `artifact`, optional `record_id`, optional `field` |
| `ReleaseBundle` | frozen dataclass: manifest dict, approval/KB/office/mapping/seed/compensation bytes, semantic SHA-256 |
| `load_json_object_strict(path: Path)` | `dict[str, object]`; duplicate/non-object/invalid UTF-8를 stable error로 거부 |
| `validate_approved_input(repository_root: Path, draft_dir: Path)` | immutable `Sequence[ReleaseIssue]` |
| `build_seed_projection(draft_dir: Path, release_version: str)` | four-array `dict[str, object]` |
| `canonical_json_bytes(value: object, trailing_newline: bool)` | canonical UTF-8 `bytes` |
| `semantic_sha256(projection: Mapping[str, object])` | lower-case 64-char SHA-256 `str` |
| `build_release_bundle(repository_root, draft_dir, release_version, released_at)` | `ReleaseBundle` |
| `verify_release_directory(repository_root: Path, release_dir: Path)` | issue-free summary `dict[str, object]` or stable failure |

`scripts/data_seed_sql.py`의 exact signature contract:

| 이름 | 반환 계약 |
|---|---|
| `sql_literal(value: object)` | safely quoted SQL literal `str` |
| `render_expected_rows(projection: Mapping[str, object])` | fixed expected-row CTE `str` |
| `render_seed_sql(projection: Mapping[str, object])` | deterministic UTF-8/LF `bytes` |
| `render_compensation_sql(projection: Mapping[str, object])` | deterministic UTF-8/LF `bytes` |

`scripts/promote_data_seed.py` subcommands and stable success output:

```text
prepare             -> [PASS] step=PREPARE-DATA-SEED release=0.1.0-initial.1 kb=19 office=3 mapping=10
verify-release      -> [PASS] step=VERIFY-DATA-SEED-RELEASE release=0.1.0-initial.1 issues=0
activate-local-seed -> [PASS] step=ACTIVATE-LOCAL-SEED release=0.1.0-initial.1 changed=0|1
verify-local-seed   -> [PASS] step=VERIFY-LOCAL-SEED release=0.1.0-initial.1 active=1
```

실패 출력은 `[FAIL] step=<ID> reason=<stable-code> issues=<count>`만 허용하고 content/comment/DSN은 금지한다.

## 제안 설계

- 데이터 흐름: approved staging bytes → strict trust validation → approved projection → canonical JSON/SQL → immutable release → byte-identical dispatcher → disposable DB verification.
- 컴포넌트 경계: pure generator는 DB/filesystem publication을 수행하지 않고, CLI만 exact-path publication을 소유하며, PowerShell runner만 Docker/patched CLI/DSN orchestration을 소유한다.
- API/DB 변경: migration/schema/public API 변경 0. 기존 table에 initial approved row만 삽입한다.
- 보안/개인정보: path/reparse fail closed, no dynamic SQL/runtime interpolation, secret-free output, official authored generalized examples only.
- 실패/장애: prepared-but-inactive는 유효 상태, import 실패는 transaction rollback, compensation mismatch는 delete 전 abort, immutable correction은 새 version/승인으로만 수행한다.

---

### Task 0: 승인된 실행 시작을 고정하고 격리한다

**Files:**
- Modify: this plan
- Modify: `docs/implementation-notes/IMP-20260719-007-data-seed-001-명세-승인과-실행계획.md`
- Create at execution: DATA-SEED implementation note

**Interfaces:** Consumes user plan approval. Produces an isolated branch/worktree and clean baseline; release timestamp is already fixed by governance approval.

- [x] **Step 1: 계획 승인 metadata를 기록한다**

계획 `상태`를 `Approved / In Progress`로 바꾸고 승인 문구·시각을 진행 기록에 남긴다. Task 5의 `--released-at`은 이미 고정된 `2026-07-19T09:20:31+09:00`만 사용한다.

- [x] **Step 2: 실행용 구현 노트를 생성한다**

```powershell
python scripts/new_implementation_note.py --title "DATA-SEED-001 불변 공식 release와 local seed 검증" --task-id DATA-SEED-001 --type implementation-data-security
```

Expected: 새 note와 INDEX row 생성, 생성 시 version snapshot 기록.

- [x] **Step 3: worktree를 격리한다**

`superpowers:using-git-worktrees`를 읽고 `codex/data-seed-001-initial-release`를 `.worktrees/data-seed-001-initial-release`에 만든다. `.worktrees` ignore, branch/head, clean status를 확인한다.

- [x] **Step 4: clean baseline을 실행한다**

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1
```

Expected: exit 0, DATA-001 validator PASS, official release 0, data-free dispatcher, `/ready=503`.

- [x] **Step 5: 시작 상태를 commit한다**

```powershell
git add -- docs/superpowers/plans/2026-07-19-data-seed-immutable-release-and-local-verification.md docs/implementation-notes/IMP-20260719-008-data-seed-001-불변-공식-release와-local-seed-검증.md docs/implementation-notes/INDEX.md
git commit -m "docs(data): start approved DATA-SEED plan"
```

### Task 1: release schema와 승인 입력 trust boundary를 TDD로 만든다

**Files:**
- Create: `data/schemas/data-seed/v1/release-manifest.schema.json`
- Create: `data/schemas/data-seed/v1/kb-records.schema.json`
- Create: `data/schemas/data-seed/v1/offices.schema.json`
- Create: `data/schemas/data-seed/v1/office-service-mappings.schema.json`
- Create: `scripts/data_seed_release.py`
- Create: `scripts/tests/test_data_seed_release.py`

**Interfaces:** Produces `ReleaseIssue`, strict loader, approved-input validator and schema contracts for Task 2.

- [x] **Step 1: RED input/schema tests를 작성한다**

```python
def test_duplicate_json_member_is_rejected(self) -> None:
    path = self.write_raw('{"schema_version":1,"schema_version":1}\n')
    with self.assertRaisesRegex(ValueError, "JSON_DUPLICATE_MEMBER"):
        load_json_object_strict(path)

def test_noncanonical_or_stale_approval_is_rejected(self) -> None:
    draft = self.copy_canonical_draft()
    self.mutate_manifest(draft, state="PENDING_PM_REVIEW")
    codes = {issue.code for issue in validate_approved_input(self.root, draft)}
    self.assertIn("APPROVAL_STATE_INVALID", codes)

def test_exact_projection_and_exclusions_are_required(self) -> None:
    draft = self.copy_canonical_draft()
    self.approve_waste_03(draft)
    codes = {issue.code for issue in validate_approved_input(self.root, draft)}
    self.assertIn("APPROVED_PROJECTION_INVALID", codes)
```

- [x] **Step 2: RED를 확인한다**

```powershell
apps/api/.venv/Scripts/python.exe -B -m unittest -v scripts.tests.test_data_seed_release
```

Expected: import/module/schema absence로 FAIL.

- [x] **Step 3: 네 strict schema를 구현한다**

각 root/record는 `additionalProperties:false`, exact version, official/ACTIVE status, author/reviewer/timestamps, 19/3/10 count와 required fields를 표현한다. 배열 order/duplicate/cross-file 제약은 Python validator가 보완한다.

- [x] **Step 4: strict loader와 trust validator 최소 구현을 작성한다**

`object_pairs_hook`로 duplicate member를 거부하고, exact repository-relative path/reparse 검사 후 기존 `validate_staging`을 호출한다. manifest state/reviewer/author/35 decisions/comments/hash/count/excluded ID를 값 원문 없이 검증한다.

- [x] **Step 5: focused test와 기존 DATA-001 회귀를 실행한다**

```powershell
apps/api/.venv/Scripts/python.exe -B -m unittest -v scripts.tests.test_data_seed_release
apps/api/.venv/Scripts/python.exe -B -m unittest -v scripts.tests.test_data_staging_validation
apps/api/.venv/Scripts/python.exe -B scripts/validate_data_staging.py validate --draft-dir data/staging/data-001/0.1.0-draft.1
```

Expected: 새 suite PASS, 기존 63-test/canonical validator PASS.

- [x] **Step 6: commit한다**

```powershell
git add data/schemas/data-seed/v1 scripts/data_seed_release.py scripts/tests/test_data_seed_release.py
git commit -m "test(data): define DATA-SEED release trust boundary"
```

### Task 2: deterministic projection, semantic hash, seed/compensation SQL을 TDD로 생성한다

**Files:**
- Modify: `scripts/data_seed_release.py`
- Create: `scripts/data_seed_sql.py`
- Modify: `scripts/tests/test_data_seed_release.py`

**Interfaces:** Consumes approved input. Produces `ReleaseBundle`, canonical semantic projection and deterministic SQL bytes for Task 3.

- [x] **Step 1: RED projection/hash tests를 작성한다**

```python
def test_projection_is_exact_19_3_10(self) -> None:
    projection = build_seed_projection(self.draft, RELEASE_VERSION)
    self.assertEqual(19, len(projection["kb_documents"]))
    self.assertEqual(3, len(projection["offices"]))
    self.assertEqual(10, len(projection["office_service_mappings"]))
    ids = {row["public_id"] for row in projection["kb_documents"]}
    self.assertNotIn("KB-WASTE-03", ids)

def test_semantic_hash_uses_exact_canonical_bytes(self) -> None:
    projection = build_seed_projection(self.draft, RELEASE_VERSION)
    expected = hashlib.sha256(canonical_json_bytes(projection, trailing_newline=False)).hexdigest()
    self.assertEqual(expected, semantic_sha256(projection))

def test_sql_has_fixed_role_lock_and_bidirectional_guards(self) -> None:
    sql = render_seed_sql(self.projection).decode("utf-8")
    self.assertIn("pg_advisory_xact_lock(20260719001)", sql)
    self.assertIn("SET LOCAL lock_timeout = '5s'", sql)
    self.assertGreaterEqual(sql.count("EXCEPT ALL"), 8)
```

- [x] **Step 2: RED를 확인한다**

Expected: projection/SQL functions absence로 FAIL.

- [x] **Step 3: canonical projection과 normalization을 구현한다**

KB/질문/기관/매핑 field allowlist를 literal tuple로 선언한다. public ID/key는 Python code-point lexical order, nested authored arrays는 source order, timestamps는 UTC second precision `Z`, JSON은 `ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False`를 사용한다.

- [x] **Step 4: safe SQL serializer를 구현한다**

`None→NULL`, bool/date/timestamp/text/jsonb를 explicit cast와 single-quote doubling으로 직렬화한다. generated SQL은 `BEGIN`, assertions, fixed locks, empty preflight, explicit inserts, expected-row CTE, bidirectional comparisons, exclusions, `COMMIT` 순서다. runtime input/dynamic SQL은 없다.

- [x] **Step 5: compensation generator를 구현한다**

같은 role/lock/expected-row guard 뒤 operational/reference empty와 exact semantic equality를 검사하고 mapping→KB/office FK-safe delete 및 absence assertion을 수행한다.

- [x] **Step 6: deterministic/fuzz-like escaping 회귀를 실행한다**

서로 다른 temp root에서 동일 explicit timestamp로 bundle 두 개를 만들고 7개 byte hash가 모두 같은지, quote/backslash/Unicode/date/null이 SQL과 projection에서 정확한지 검사한다.

- [x] **Step 7: commit한다**

```powershell
git add scripts/data_seed_release.py scripts/data_seed_sql.py scripts/tests/test_data_seed_release.py
git commit -m "feat(data): generate deterministic official seed artifacts"
```

### Task 3: recoverable prepare/activation CLI를 TDD로 만든다

**Files:**
- Create: `scripts/promote_data_seed.py`
- Create: `scripts/tests/test_promote_data_seed.py`
- Modify: `scripts/data_seed_release.py`

**Interfaces:** Produces the only filesystem publication commands; no real release is created in this task.

- [x] **Step 1: RED publication tests를 작성한다**

```python
def test_existing_release_fails_without_byte_change(self) -> None:
    release = self.create_existing_release(b"sentinel")
    before = self.hash_tree(release)
    self.assertEqual(2, cli(["prepare", *self.valid_args()]))
    self.assertEqual(before, self.hash_tree(release))

def test_prepare_failure_leaves_release_absent(self) -> None:
    with mock.patch("scripts.promote_data_seed._write_bundle", side_effect=OSError):
        self.assertEqual(2, cli(["prepare", *self.valid_args()]))
    self.assertFalse(self.release.exists())

def test_activation_failure_restores_dispatcher(self) -> None:
    prior = self.dispatcher.read_bytes()
    with mock.patch("os.replace", side_effect=OSError):
        self.assertEqual(2, cli(["activate-local-seed", *self.release_args()]))
    self.assertEqual(prior, self.dispatcher.read_bytes())
```

- [x] **Step 2: RED를 확인한다**

Expected: CLI absence로 FAIL.

- [x] **Step 3: exact CLI/parser/path boundary를 구현한다**

subcommand별 required args만 허용하고 exact draft/release/version을 비교한다. path component의 reparse flag를 검사하며 error output에는 stable code/count만 표시한다.

- [x] **Step 4: same-parent prepare를 구현한다**

exact sibling `.0.1.0-initial.1.prepare`를 exclusive create하고 현재 process가 만든 경로만 failure cleanup한다. 모든 file write/flush/verify 뒤 single rename하며 기존 target/temp는 자동 삭제하지 않고 fail closed한다.

- [x] **Step 5: atomic dispatcher activation을 구현한다**

release를 재검증하고 previous bytes를 memory에 보관한 뒤 sibling temp write/flush/replace/hash check를 수행한다. post-check 실패 시 previous bytes를 새 sibling temp로 restore/replace하고 byte-verify한다. equal dispatcher reactivation만 `changed=0`으로 성공한다.

- [x] **Step 6: path/reparse/partial/drift tests를 실행한다**

absolute/alias/`..`/symlink/junction/reparse, existing temp/release, malformed bytes, dispatcher unrelated drift, prepare/activation failure injection을 모두 PASS시킨다.

- [x] **Step 7: commit한다**

```powershell
git add scripts/promote_data_seed.py scripts/data_seed_release.py scripts/tests/test_promote_data_seed.py
git commit -m "feat(data): add guarded official release publication"
```

### Task 4: supported disposable DB verifier와 concurrency gate를 TDD로 만든다

**Files:**
- Create: `scripts/verify_data_seed_db.py`
- Create: `scripts/test_data_seed_concurrency.py`
- Create: `scripts/verify_data_seed.ps1`
- Create: `scripts/tests/test_verify_data_seed_db.py`
- Create: `scripts/tests/test_verify_data_seed_runner.py`

**Interfaces:** Consumes exact release and in-memory admin DSN. Produces stable evidence for actual seed/compensation/replay without changing migration authority.

- [x] **Step 1: RED DSN/session/unit tests를 작성한다**

```python
def test_dsn_identity_requires_exact_local_admin(self) -> None:
    accepted = parse_and_validate_dsn("user=postgres host=127.0.0.1 port=54322 dbname=postgres")
    self.assertEqual(("postgres", "127.0.0.1", 54322, "postgres"), accepted.identity)
    for value in self.wrong_user_host_port_database_cases():
        with self.assertRaisesRegex(ValueError, "ADMIN_DSN_IDENTITY_INVALID"):
            parse_and_validate_dsn(value)

def test_output_never_contains_dsn_or_release_content(self) -> None:
    output = run_cli_with_fake_connection(self.secret_dsn)
    self.assertNotIn(self.secret_dsn, output)
    self.assertRegex(output, r"^\[(PASS|FAIL)\] step=[A-Z0-9-]+")
```

- [x] **Step 2: RED PowerShell runner tests를 작성한다**

runner source/stub tests는 patched `verify_database.ps1` 선행, exact version allowlist, status DSN memory-only, reset ordering, child timeout, env restore, stock Supabase/direct manual SQL 금지를 확인한다.

- [x] **Step 3: Python DB verifier를 구현한다**

`psycopg.conninfo.conninfo_to_dict`로 identity를 확인하고 release path/hash를 재검증한다. `failure-rollback`, `seed-cycle`, `verify-final` subcommand는 release SQL을 memory에서 실행하고 exact DB projection을 query/canonicalize/hash한다. expected DB error는 transaction rollback 뒤 stable status만 반환한다.

- [x] **Step 4: concurrency probe를 구현한다**

두 connection/barrier로 (a) capability write가 먼저 commit되어 seed locked preflight가 실패, (b) seed lock이 먼저 잡혀 capability write가 commit 뒤까지 block되는 순서를 timeout 안에 증명한다. 각 scenario는 fresh reset을 사용하고 partial seed 0을 확인한다.

- [x] **Step 5: PowerShell orchestration을 구현한다**

순서는 patched `verify_database.ps1` full gate → status/DSN capture → exact identity check → fresh reset → forced failure → reset → concurrency A → reset → concurrency B → reset → final seed/second-seed/blocked-compensation/successful-compensation/reseed → final verify다. `finally`에서 DSN env를 원래 상태로 복원하고 value를 출력하지 않는다.

- [x] **Step 6: unit/static runner tests를 실행한다**

```powershell
apps/api/.venv/Scripts/python.exe -B -m unittest -v scripts.tests.test_verify_data_seed_db scripts.tests.test_verify_data_seed_runner
```

Expected: Docker/DB 없이 PASS; invalid/stub child cases exit code와 env restoration exact.

- [x] **Step 7: commit한다**

```powershell
git add scripts/verify_data_seed_db.py scripts/test_data_seed_concurrency.py scripts/verify_data_seed.ps1 scripts/tests/test_verify_data_seed_db.py scripts/tests/test_verify_data_seed_runner.py
git commit -m "test(data): add disposable official seed verification gate"
```

### Task 5: approved release를 실제로 prepare하고 local dispatcher를 활성화한다

**Files:**
- Create: `data/official/releases/0.1.0-initial.1/release_manifest.json`
- Create: `data/official/releases/0.1.0-initial.1/approval_manifest.json`
- Create: `data/official/releases/0.1.0-initial.1/kb_records.json`
- Create: `data/official/releases/0.1.0-initial.1/offices.json`
- Create: `data/official/releases/0.1.0-initial.1/office_service_mappings.json`
- Create: `data/official/releases/0.1.0-initial.1/seed.sql`
- Create: `data/official/releases/0.1.0-initial.1/compensation.sql`
- Modify: `supabase/seed.sql`

**Interfaces:** Consumes the fixed governance timestamp and verified generator. Produces prepared+active immutable filesystem release; DB is still unchanged at the end of this task.

- [x] **Step 1: canonical input을 다시 검증한다**

```powershell
apps/api/.venv/Scripts/python.exe -B scripts/validate_data_staging.py validate --draft-dir data/staging/data-001/0.1.0-draft.1
```

Expected: exact approved 19/3/10, issue 0.

- [x] **Step 2: 고정된 governance timestamp로 prepare한다**

승인 명세에 기록한 timezone-aware literal을 직접 argument로 사용한다. shell 변수나 `Get-Date`를 production command에 사용하지 않는다.

```powershell
apps/api/.venv/Scripts/python.exe -B scripts/promote_data_seed.py prepare --draft-dir data/staging/data-001/0.1.0-draft.1 --release-version 0.1.0-initial.1 --released-at 2026-07-19T09:20:31+09:00
```

Expected: PASS 19/3/10.

- [x] **Step 3: release를 독립 재검증한다**

```powershell
apps/api/.venv/Scripts/python.exe -B scripts/promote_data_seed.py verify-release --release-dir data/official/releases/0.1.0-initial.1
```

Expected: schema/hash/order/exclusions/semantic SQL issue 0.

- [x] **Step 4: dispatcher를 활성화하고 byte equality를 검증한다**

```powershell
apps/api/.venv/Scripts/python.exe -B scripts/promote_data_seed.py activate-local-seed --release-dir data/official/releases/0.1.0-initial.1
apps/api/.venv/Scripts/python.exe -B scripts/promote_data_seed.py verify-local-seed --release-dir data/official/releases/0.1.0-initial.1
```

Expected: first activation changed=1, verify active=1; repeat activation changed=0.

- [x] **Step 5: protected diff를 검토한다**

staging hashes/approval bytes는 변경 0, migration/config/API/product code 변경 0, release 7 files와 dispatcher만 생성/변경됐는지 확인한다.

- [x] **Step 6: commit한다**

```powershell
git add data/official/releases/0.1.0-initial.1 supabase/seed.sql
git commit -m "data: publish initial approved official release"
```

### Task 6: 실제 disposable local DB에서 seed/compensation/replay를 검증한다

**Files:**
- Create: `docs/test-reports/DATA-SEED-001-LOCAL-VERIFICATION.md`
- Modify: implementation note

**Interfaces:** Produces actual PostgreSQL evidence required before official-data version promotion.

- [x] **Step 1: Docker/patched runtime preflight를 읽기 전용 확인한다**

Docker Engine 28+, pinned patched CLI hash, target port ownership을 확인한다. unrelated container/volume을 stop/delete/prune하지 않는다.

- [x] **Step 2: supported runner를 실행한다 — 3회 시도, actual Blocked**

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify_data_seed.ps1 -ReleaseVersion 0.1.0-initial.1
```

Expected: patched DB baseline/pgTAP 282/backend integration 8/8, forced rollback 0 partial, two concurrency cases PASS, seed 19/3/10, second seed rejected unchanged, compensation guards PASS, compensation→reseed same hash, final citizen read exact 19.

- [ ] **Step 3: exclusions와 final DB state를 확인한다 — seed write 전 blocker로 미도달**

runner의 structured query evidence로 WASTE-03/rejected mapping/mock 0, operational tables 0, final semantic SHA가 manifest와 같음을 확인한다. DSN/content/comment는 report에 기록하지 않는다.

- [x] **Step 4: actual report를 작성한다**

engine/CLI/DB version, release/semantic hashes, counts, step IDs/duration, second-seed/rollback/concurrency/compensation 결과, final runtime cleanup 경계를 기록한다. 실제 값이 없는 항목을 성공으로 쓰지 않는다.

- [x] **Step 5: 실패 처리한다 — `.1`/role/grant 무변경, version 미승격, cleanup**

어느 actual gate라도 실패하면 `official_data` version을 올리지 않고 plan을 `Blocked` 또는 `In Progress`로 유지한다. immutable release를 수정/삭제하지 않고 원인을 진단해 새 code commit으로 보정한 뒤 전체 actual cycle을 처음부터 다시 실행한다.

- [x] **Step 6: evidence를 commit한다**

```powershell
git add -- docs/test-reports/DATA-SEED-001-LOCAL-VERIFICATION.md docs/implementation-notes/IMP-20260719-008-data-seed-001-불변-공식-release와-local-seed-검증.md docs/implementation-notes/INDEX.md
git commit -m "test(data): verify initial seed compensation replay"
```

### Task 7: root 회귀 gate, lineage, 버전과 문서를 동기화한다

**Files:**
- Modify: `scripts/verify.ps1`
- Modify: `scripts/tests/test_verify_runner.py`
- Create: `docs/data-lineage/DATA-SEED-001-0.1.0-initial.1.md`
- Modify: `data/README.md`
- Modify: `data/official/README.md`
- Modify: `database/README.md`
- Modify: `docs/source-of-truth/TEAM_DECISIONS.md`
- Modify: `docs/source-of-truth/PROJECT_PLAN.md`
- Modify: `docs/source-of-truth/RFP_MATRIX.md` only if actual count wording needs synchronization
- Modify: `docs/11_AMBIGUITY_REGISTER.md`
- Modify: `docs/decisions/DECISION_LOG.md`
- Modify: `TASKS.md`
- Modify: `CHANGELOG.md`
- Modify: `versions/manifest.json`
- Modify: implementation note and INDEX

**Interfaces:** Makes immutable release validation part of every no-Docker root gate and exposes accurate lineage/status to later READY/AI slices.

- [x] **Step 1: RED root-runner tests를 작성한다**

`verify.ps1`이 focused DATA-SEED unit suites, `verify-release`, `verify-local-seed`를 DATA-001 뒤에 실행하고 failure exit를 보존하는지 static/stub test로 먼저 실패시킨다. Root gate는 Docker/DB를 시작하지 않는다.

- [x] **Step 2: root verify stages를 최소 구현한다**

canonical release marker/schema/dispatcher 존재를 확인하고 locked API Python으로 unit suites와 두 CLI verify subcommand를 실행한다. source/comment/DSN은 출력하지 않는다.

- [x] **Step 3: lineage와 stale docs를 갱신한다**

approval/release artifact hash, semantic hash, Task 6 evidence와 immutable correction 절차를 기록한다. `database/README.md`의 Q-SEC-006 미해결 설명을 D-031/0.3.0-local actual 기준으로 정정하되 public Q-SEC-003 차단은 유지한다.

- [x] **Step 4: version을 actual Blocked 결과에 맞게 갱신한다**

Actual DB full cycle이 실패했으므로 계획한 success version을 사용하지 않는다.
`official_data: 0.0.0-not-populated`를 유지하고, Task 7A filesystem/no-Docker gate만
`test_suite: 0.8.1-data-seed-filesystem-gate`, 정확한 blocked lineage 문서를
`documentation: 2.7.4`로 기록한다. application/web/API/shared/DB/mock/prompt는 유지한다.

- [x] **Step 5: Task 7B scoped verification을 실행한다 — Task 7A root PASS 재사용**

```powershell
apps/api/.venv/Scripts/python.exe -B scripts/validate_data_staging.py validate --draft-dir data/staging/data-001/0.1.0-draft.1
apps/api/.venv/Scripts/python.exe -B scripts/promote_data_seed.py verify-release --release-dir data/official/releases/0.1.0-initial.1
apps/api/.venv/Scripts/python.exe -B scripts/promote_data_seed.py verify-local-seed --release-dir data/official/releases/0.1.0-initial.1
python -B scripts/validate_codex_package.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check_secret_patterns.ps1
git diff --check
```

Actual: DATA-001/release/dispatcher/package/JSON/manifest/link/stale/secret/diff/protected-scope가 모두
PASS했다. Docker/DB/full root는 재실행하지 않았고 Task 7A의 reviewed root PASS와
Task 6 Blocked actual report를 사용했다.

- [x] **Step 6: 구현 note를 완성하고 commit한다**

실제 명령·시간·counts/hashes·보안/데이터/rollback·human/AI 경계를 채우고 INDEX/version을 확인한다.

```powershell
git add -- scripts/verify.ps1 scripts/tests/test_verify_runner.py docs/data-lineage/DATA-SEED-001-0.1.0-initial.1.md docs/test-reports/DATA-SEED-001-LOCAL-VERIFICATION.md data/README.md data/official/README.md database/README.md docs/source-of-truth/TEAM_DECISIONS.md docs/source-of-truth/PROJECT_PLAN.md docs/11_AMBIGUITY_REGISTER.md docs/decisions/DECISION_LOG.md TASKS.md CHANGELOG.md versions/manifest.json docs/implementation-notes/IMP-20260719-008-data-seed-001-불변-공식-release와-local-seed-검증.md docs/implementation-notes/INDEX.md
git commit -m "docs(data): complete DATA-SEED-001 lineage"
```

### Task 8: 독립 리뷰, main 통합, 재검증과 worktree 정리를 수행한다

**Files:** All DATA-SEED diff, plan, reports, notes.

**Interfaces:** Produces reviewed clean main state. No remote push/PR exists.

- [ ] **Step 1: spec compliance review를 별도 agent에 요청한다**

approved spec §1~15와 plan acceptance를 기준으로 Critical/Important/Minor findings를 받는다. 구현 agent가 자기 결과를 승인하지 않는다.

- [ ] **Step 2: code/security/data-quality review를 Sol ultra에 요청한다**

path/reparse, immutable write, duplicate JSON, SQL quoting, role/lock/empty/bidirectional guards, DSN/log secrecy, compensation/concurrency, protected paths와 version gate를 집중 검토한다.

- [ ] **Step 3: finding을 TDD로 보정하고 전체 gate를 재실행한다**

Critical/Important 0이 될 때까지 각 finding을 재현 테스트→minimal fix→focused/full verification 순으로 처리한다. Minor는 수용 여부와 이유를 note에 기록한다.

- [ ] **Step 4: branch diff를 자체 검토한다**

staging 승인 bytes, migrations, API/contracts, `.env`, mock, public deployment가 변경되지 않았는지 확인한다. secret scanner와 `git diff --check`를 마지막으로 실행한다.

- [ ] **Step 5: main에 fast-forward 통합한다**

main/worktree clean과 branch head를 확인하고 `git merge --ff-only codex/data-seed-001-initial-release`를 실행한다. 원격 push/PR은 하지 않는다.

- [ ] **Step 6: main 최종 verification과 안전한 worktree 정리를 수행한다**

main에서 root full gate와 release verify를 재실행한다. worktree가 clean이고 target이 repository `.worktrees` 내부인지 확인한 뒤 `git worktree remove`하고 main worktree 1개, status clean을 증명한다.

## 테스트 계획

- 단위: strict JSON/schema/trust, projection/order/hash, SQL escaping/guards, publication/activation, DSN/query canonicalization.
- 계약: four release schemas, release manifest exact fields/hashes/counts, dispatcher byte equality.
- 통합: existing DATA-001 63 tests, root runner stubs, API DB integration 8/8, pgTAP 282.
- 실제 DB: forced rollback, second seed, exact citizen read, compensation success/failure, semantic hash replay.
- 동시성: capability-before-lock와 lock-before-capability 두 ordering, partial mutation 0.
- 보안/PII: path/reparse attacks, stale/self/rejected/mock input, DSN/secret/content output scan, migration/grant change 0.
- 접근성: UI 변경 0; 기존 Web regression만 실행.
- 성능/비용: generation/import duration 기록, 19/3/10 scale, external API attempt 0, 새 비용 0원.

## 버전 변경 결과

| 축 | Before | Actual after | 근거 |
|---|---|---|---|
| Product spec | 2.2.1 | unchanged | 범위 변경 없음 |
| Application | 0.2.0 | unchanged | runtime behavior 변경 없음 |
| Web | 0.2.0-static-chat-shell | unchanged | UI 변경 없음 |
| API/shared | 2.0.1-draft / 0.2.1 | unchanged | wire 변경 없음 |
| DB schema | 0.3.0-local | unchanged | migration/role/grant 변경 없음 |
| Official data | 0.0.0-not-populated | unchanged | actual DB full cycle 미도달; filesystem release를 DB/ACTIVE 승격으로 간주하지 않음 |
| Mock data | 0.0.0-not-populated | unchanged | mock 미사용 |
| Prompt | 0.0.2-deepseek-v4-flash-selected | unchanged | LLM 미호출 |
| Test suite | 0.8.0-web-browser-gate | 0.8.1-data-seed-filesystem-gate | Task 7A filesystem/no-Docker gate PASS만 반영 |
| Documentation | 2.7.3 | 2.7.4 | Blocked lineage, status, A-030/Q-SEED-002 동기화 |

## 위험과 롤백

| 위험 | 조기 신호 | 처리/롤백 |
|---|---|---|
| approval/staging drift | hash/count/decision code | release write 전 fail; PM 재승인 없이는 진행 금지 |
| partial filesystem publish | temp/release coexistence | existing path 자동 삭제 금지; current-call temp만 검증 후 cleanup |
| dispatcher replace 실패 | byte mismatch | previous bytes atomic restore; release는 prepared 상태 유지 |
| wrong DB/runtime | DSN/session/port assertion | table access 전 fail, secret-free output |
| non-empty DB | any of 8 table counts >0 | write/delete 전 fail; fresh disposable reset만 허용 |
| SQL bug/mid-import | transaction error | rollback 뒤 row/hash unchanged 확인 |
| compensation data loss | operational/extra/altered row | delete 전 bidirectional guard fail |
| concurrency interleaving | lock timeout/preflight mismatch | fixed locks와 scenario reset, partial 0 검증 |
| actual gate 실패 뒤 release 존재 | official version still old | branch를 통합하지 않고 immutable artifact를 그대로 보존해 code remediation; in-place edit 금지 |
| public 오해 | readiness/public docs drift | `/ready=503`, Q-SEC-003, local/private label을 test/docs에서 유지 |

## 인간이 승인해야 하는 사항

- 기존 plan·local disposable DB 실행 승인은 D-039로 완료됐다.
- 현재 필요한 결정은 A-030/Q-SEED-002다. A(추천/default)는 migration/pgTAP
  effective-union 권위를 유지하고 separately approved immutable `.2`를 만든다. B는 새 DB
  migration으로 grantor-specific membership를 하나의 row로 정규화한다.
- 답이 없으면 A를 추천만 유지하고 둘 다 구현하지 않는다. D-040을 확정 결정으로
  작성하지 않으며 DATA-SEED/READY/AI는 Blocked다.
- 이후에도 별도 승인이 필요한 범위: WASTE-03 activation, non-empty/remote data transition,
  migration/API/public deployment, 새 dependency.

## AI 내부 구현 세부

- helper/file split, dataclass 이름, fixture factory, SQL formatting line breaks, test temporary directory naming.
- 계약을 유지하는 internal refactor, lint/format, stable issue code 세분화.
- task별 agent 배정과 review 순서. 제품/data/DB 계약을 바꾸는 finding은 인간에게 다시 올린다.

## 진행 기록

- 2026-07-19T09:20:31+09:00: 사용자가 written specification을 승인했다.
- 2026-07-19: source-of-truth, ADR-0015/0016, schema/migration/tooling과 current Git을 재감사하고 이 실행계획을 작성했다.
- 2026-07-19T09:52:08+09:00: 사용자가 `ㅇㅋ 전체 승인 구현 ㄱㄱ`로 실행계획 전체와 disposable local DB reset/seed/compensation/replay를 승인했다. 고정 release governance timestamp는 변경하지 않는다.
- 2026-07-19T10:09:48+09:00: 승인 기록 commit `eb84690`에서 `codex/data-seed-001-initial-release` worktree를 만들고 root baseline 전체를 PASS했다. official release/dispatcher/DB mutation은 아직 0이다.
- 2026-07-19 Task 5: immutable `.1` release 19/3/10과 byte-identical dispatcher를 게시·검증했고
  독립 review 0/0/0을 받았다. DB/Docker는 실행하지 않았다.
- 2026-07-20 00:21:14~00:51:40 KST Task 6: actual runner 3회, reviewed bounded fix 2개 후에도
  grantor-option union 대 `.1` single-row guard 충돌로 seed write 전 Blocked. cleanup container/54322
  listener 0; volume 2/network 1 보존.
- 2026-07-20 Task 7A: active-release fixture·root stage를 보정하고 no-Docker root gate를 PASS했으며
  독립 review 0/0/0을 받았다.
- 2026-07-20 Task 7B: lineage/source-of-truth/backlog/ADR/decision/note/version을 Blocked actual에
  맞게 동기화하고 A-030/Q-SEED-002를 열었다. 선택지는 구현하지 않았다.

## 자체 검토

- Spec coverage: trust input, 19/3/10 projection, immutable two-phase publish, semantic hash, role/lock/empty guards, compensation, concurrency, version/lineage를 Task 1~8에 모두 매핑했다.
- Completeness review: 구현 함수·파일·명령·expected result를 정의했다. Task 5 timestamp는 명세 승인 시각으로 이미 고정됐다.
- Type consistency: `ReleaseBundle`, projection top-level keys, CLI subcommand와 runner arguments는 전 task에서 동일하다.
- Scope review: migration/API/readiness/LLM/UI/public/remote/new dependency 변경은 없다.

## 결과와 회고

- 실제 결과: immutable filesystem release/dispatcher publication과 offline 회귀 gate는 완료됐다.
  Actual DB import는 seed write 전 membership contract 충돌로 Blocked이며 DB/ACTIVE/READY/AI
  승격 근거는 없다.
- 계획과 달라진 점: Task 7의 success promotion values는 적용하지 않았다. actual은
  official data 유지, tests 0.8.1, docs 2.7.4다.
- 다음 단계: 인간이 A-030/Q-SEED-002를 결정한 뒤 별도로 승인된 선택지만 구현하고
  actual cycle 전체를 처음부터 재실행한다. 그전까지 READY-001·AI-001로 진행하지 않는다.
