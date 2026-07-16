# IMP-20260717-003 — DB-001 Task 8 lazy typed database boundary

- Date/Time (KST): 2026-07-17T02:49:33+09:00
- Task ID: DB-001-T8
- Type: implementation
- Status: Done
- Author/Agent: Codex Task 8 implementation agent, independent reviewer, `/root` coordinator, documentation closeout agent
- Branch: `codex/db-001-layered-enforcement`
- Base commit: `ab86c09`
- Implementation commit: `3cae552`
- Related plan/ADR/RFP: [DB-001 plan Task 8](../superpowers/plans/2026-07-16-db-001-layered-enforcement.md#task-8-add-the-lazy-typed-fastapi-database-boundary), [ADR-0011](../adr/0011-layered-database-and-backend-enforcement.md), D-026/D-027, RFP F-11/F-12/F-13, [Task 7 note](IMP-20260717-002-db-001-task-7-official-citizen-reads.md)

## 1. 사용자 요청과 완료 기준

### 요청

사용자가 승인한 DB-001 계획을 계속 실행하여, 이미 검증된 PostgreSQL capability를 FastAPI에서 지연 로딩되는 타입 안전 repository로 사용할 수 있게 한다. 코딩은 독립 agent가 담당하고 root가 중요 경계·명령·검증을 통제하며, 독립 review 후에만 닫는다.

### Acceptance Criteria

- DB 규칙 오류는 SQLSTATE로만 안전한 domain error에 mapping하고 DB message, parameter, question/answer text를 반사하거나 log하지 않는다.
- PostgreSQL enum·상태 matrix·기본 구조 규칙을 frozen/slotted typed model로 중복 검증한다.
- repository는 고정된 `app_api` SQL 9개와 위치 parameter만 사용하고, read는 immutable tuple, write는 connection transaction 경계를 사용한다.
- pool은 명시적 factory 호출 전에 환경변수를 읽거나 열리지 않는다. `sejong_ai_api.main` import는 DB driver·repository·pool을 import/생성하지 않는다.
- public route·OpenAPI·migration·seed·dependency·version manifest를 바꾸지 않고 `/health`를 유지하며 `/ready=503`을 바꾸지 않는다.
- TDD RED→GREEN, Ruff, strict Mypy, API pytest, secret/package/diff/exact scope, independent review를 모두 통과한다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자 승인자, Codex `/root` coordinator, Task 8 구현 agent, 독립 reviewer, 문서 마감 agent |
| When — 언제 | 2026-07-17 KST; base `ab86c09`에서 구현·review·root 검증 후 마감 |
| Where — 어디서 | `.worktrees/db-001-layered-enforcement`, `apps/api/src/sejong_ai_api/db`, `apps/api/tests/db`, API architecture test |
| What — 무엇을 | typed model/error, lazy pool factory, repository protocol/psycopg adapter, unit/architecture regression 10파일 |
| Why — 왜 | DB의 privacy·role·workflow·citizen-read 규칙을 backend 연결 경계에서 유지하고 native DB diagnostic 누출을 차단하기 위해 |
| How — 어떻게 | 두 단계 TDD RED→GREEN, 고정 SQL/위치 parameter, sqlstate-only mapping, import-isolation subprocess, 독립 review |
| How much — 어느 정도 | 정확히 10파일·2,053 insertions, SQL constant 9개, DB model/error focused 81 pass, repository/architecture 31 pass+4 subtests, 전체 API 156 pass+4 subtests, 외부 비용 0원 |

## 3. 시작 전 상태

- 관련 파일: 승인 DB-001 plan/spec, ADR-0011, `20260716000300~00500` 인터페이스, `apps/api/tests/test_architecture.py`, frozen `uv.lock`.
- 기존 동작: migration 5/5·pgTAP 274/274·DB concurrency 4개는 통과했지만 FastAPI에 DB model, diagnostic sanitizer, pool, repository 경계가 없었다. public route는 DB에 연결되지 않았다.
- 발견한 충돌/부채: PostgreSQL native error `DETAIL`이 실패 row를 포함할 수 있어 backend이 exception 문자열을 전파하면 정책을 우회할 수 있었다. DB가 허용하는 ACTIVE KB는 question example 적어도 1개를 갖지만 초기 Python model 안에 같은 불변조건이 빠져 있었다.
- Git 상태: clean base `ab86c09`, branch `codex/db-001-layered-enforcement`, remote 없음.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| Q-SEC-002 | Resolved — Human | DB role fail-closed 모델 | A / D-026 유지 | repository는 backend capability만 호출 |
| Q-WF-001 | Resolved — Human | 실패 사유 확인 경계 | A / D-027 유지 | 별도 typed confirmation method |
| DB driver lifetime | Internal | import 시 pool/env 접근 여부 | explicit `create_pool`, `open=False`, module env read 0 | startup·test isolation |
| DB diagnostic | Internal security | native exception message/detail 처리 | sqlstate-only safe mapping, 원본은 chain만 하고 stringify/log 0 | 개인정보 누출 차단 |
| route wiring | Deferred | public route와 repository 연결 | Task 8 범위 외; Task 9는 local integration 증명만 소유 | OpenAPI/사용자 동작 무변경 |

## 5. 설계 결정과 대안

### 선택

- PostgreSQL enum과 1:1 대응하는 `str, Enum`과 frozen/slotted dataclass로 입출력을 고정했다.
- DB와 같은 단순 구조 규칙은 model 생성 시 검증하고, 교차 row·동시성 규칙은 transaction과 DB에 남겼다.
- `DatabaseRuleError`는 SQLSTATE 허용 목록의 고정 code/message만 노출하고, 알 수 없는 DB 오류는 `DATABASE_OPERATION_FAILED`로 축약했다.
- `PsycopgSejongRepository`는 고정된 `app_api` SQL 9개만 위치 parameter로 실행하고 write만 transaction을 사용한다. `create_pool`은 입력 URL을 직접 받고 `open=False`, min 1/max 4, autocommit false를 사용한다.

### 이유

이 경계는 raw SQL·raw question/answer·HTTP role header·DB diagnostic을 repository public method에서 배제한다. import만으로 connection이 열리지 않아 `/health`·`/ready`의 기존 동작과 local test isolation도 유지한다.

### 고려했지만 선택하지 않은 대안

- 자유 SQL repository: 검토 된 capability를 우회하고 SQL injection/사유화 규칙 drift를 만들어 제외.
- module import에서 env를 읽고 pool 자동 open: health/import 부작용과 test 비결정성 때문에 제외.
- DB exception message parsing/전달: private row·parameter 누출 위험으로 제외.
- 이 Task에 public route나 dependency를 추가: 승인 계약과 프로덕션 의존성 경계를 넘어 제외.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `apps/api/src/sejong_ai_api/db/__init__.py` | safe value/error type만 package root에 export | root import가 psycopg/pool/repository를 당기지 않게 제약 |
| `apps/api/src/sejong_ai_api/db/errors.py` | SQLSTATE→stable domain error mapping | native message/detail/parameter 비노출 |
| `apps/api/src/sejong_ai_api/db/models.py` | exact enum, frozen/slotted input/output dataclass, structural validator | DB 계약의 backend typed mirror |
| `apps/api/src/sejong_ai_api/db/pool.py` | explicit unopened `AsyncConnectionPool` factory | env/import side effect 0 |
| `apps/api/src/sejong_ai_api/db/repository.py` | `SejongRepository` protocol, fixed-SQL psycopg adapter, typed row mapping | backend-only capability 호출과 transaction 경계 고정 |
| `apps/api/tests/db/__init__.py` | DB test package marker | 분리된 focused test 구조 |
| `apps/api/tests/db/test_errors.py` | SQLSTATE-only mapping·비누출 regression | 안전한 error surface 고정 |
| `apps/api/tests/db/test_models.py` | enum/matrix/trim/array/ACTIVE question invariant test | 잘못된 model을 pool 접근 전 거부 |
| `apps/api/tests/db/test_repository.py` | 9 SQL/parameter, read/write context, mapping/failure test | raw SQL·partial transaction·diagnostic drift 차단 |
| `apps/api/tests/test_architecture.py` | isolated main import probe | driver/concrete DB/env/pool eager access 차단 |

### 데이터 흐름/상태 변화

Task 8은 DB row·schema·migration·seed를 바꾸지 않는 adapter 계층이다. 호출자가 생성한 typed input이 단순 구조 검증을 통과하면 repository가 fixed SQL과 분리 parameter로 `app_api` capability를 호출한다. read는 typed immutable tuple로 돌려주고, write는 connection transaction 안에서 commit/rollback된다. 실패는 SQLSTATE 허용 목록으로만 domain code가 되며 원본 message는 response/log surface에 나가지 않는다.

### 오류·빈 상태·롤백

read result 0건은 정상적인 빈 tuple이다. 지원 SQLSTATE `P1001~P1005`, `P1010`은 고정 domain error로 매핑되고, 미지 DB 오류·비정상 result shape는 고정 `DATABASE_OPERATION_FAILED`로 닫힌다. write 실패는 transaction context가 rollback하며 exception text를 log/string 처리하지 않는다. 코드 rollback은 `3cae552`를 revert하며 DB compensation이나 data 복구는 필요 없다.

## 7. 버전 전후

### 생성 시 매니페스트

- product_spec: 2.2.0
- repo_guidance: 1.4.0
- application: 0.1.0
- web: 0.1.0
- api: 2.0.1-draft
- shared_contracts: 0.2.1
- database_schema: 0.2.0-draft
- official_data: 0.0.0-not-populated
- mock_data: 0.0.0-not-populated
- prompt_set: 0.0.2-deepseek-v4-flash-selected
- test_suite: 0.4.2-readiness-contract
- documentation: 2.3.14

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Product spec | 2.2.0 | 2.2.0 | 범위 변경 없음 |
| Repo guidance | 1.4.0 | 1.4.0 | Task 10 전 유지 |
| Application | 0.1.0 | 0.1.0 | public application 동작 변경 없음 |
| Web | 0.1.0 | 0.1.0 | frontend 변경 없음 |
| API | 2.0.1-draft | 2.0.1-draft | route/OpenAPI 무변경 |
| Shared contracts | 0.2.1 | 0.2.1 | 공개 계약 무변경 |
| DB schema | 0.2.0-draft | 0.2.0-draft | migration/schema 무변경; Task 10에서 승격 |
| Official data | 0.0.0-not-populated | 0.0.0-not-populated | 실제/승인 seed 0 |
| Mock data | 0.0.0-not-populated | 0.0.0-not-populated | tracked/persistent mock 0 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 0.0.2-deepseek-v4-flash-selected | LLM 미사용 |
| Test suite | 0.4.2-readiness-contract | 0.4.2-readiness-contract | Task 10 전 manifest 유지 |
| Docs | 2.3.14 | 2.3.14 | 중간 Task closeout; Task 10 최종 동기화 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| `uv run --directory apps/api --frozen pytest -q -p no:cacheprovider tests/db/test_errors.py tests/db/test_models.py` — production DB module 전 | 의도한 RED: DB import 2개 `ModuleNotFoundError`, exit 1 | collection 2 errors | `.superpowers/sdd/task-8-report.md` |
| 같은 error/model focused command — 구현 후 | GREEN | 81 passed | Task 8 report/agent terminal |
| `uv run --directory apps/api --frozen pytest -q -p no:cacheprovider tests/db/test_repository.py tests/test_architecture.py` — pool 전 | 의도한 RED: `sejong_ai_api.db.pool` 부재, exit 1 | collection 1 error | Task 8 report |
| 같은 repository/architecture focused command — 구현 후 | GREEN | 31 passed + 4 unittest subtests | Task 8 report/agent terminal |
| ACTIVE read question-example 중간 regression | 의도한 RED 2 후 minimal validator GREEN 2 | model+adapter 2 tests | Task 8 report |
| `ruff format --check src tests` | PASS | 22 files already formatted | Task 8 report/root+agent terminal |
| `ruff check src tests` | PASS | lint finding 0 | Task 8 report/root+agent terminal |
| `mypy src tests` | PASS | strict, 22 source files, issue 0 | Task 8 report/root+agent terminal |
| `pytest -q -p no:cacheprovider` | PASS | 156 passed + 4 subtests; agent 2.65s | Task 8 report/root+agent terminal |
| independent review of `ab86c09..3cae552` | clean | Critical 0, Important 0, Minor 0 | coordinator/reviewer result |
| secret/package/diff/exact owned-file checks | PASS | secret 0, package 12/12, whitespace 0, exact 10 files | Task 8 report/root terminal |
| global `scripts/check_scope_drift.py` | baseline RED only | 기존 `PACKAGE_MANIFEST.json`, ignored `.tools/isolated-repo`; Task 8 file 0 | Task 8 report |

### 미실행 검증과 이유

- real DB integration·concurrency·rollback/replay runner: Task 9가 소유하므로 Task 8에서 실행/추가하지 않았다. repository는 async fake pool/connection/cursor로 transaction·parameter·mapping을 검증했다.
- DeepSeek/LLM/API 호출: DB-001 Task 8 범위 밖이며 key/env를 읽거나 전송하지 않았다.
- public route/end-to-end UI: route 연결은 승인된 Task 8 범위가 아니며 architecture test로 미연결을 보장했다.
- 경고 제거: pinned Starlette TestClient가 현재 httpx integration deprecation warning 1건을 발생시킨다. 수정은 신규 dependency 변경이므로 승인 범위 밖이고 test failure는 아니다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: repository method에 raw question, answer, context token, HTTP role header, arbitrary SQL을 받지 않는다. `InteractionWrite` 보존 텍스트는 masked question만 허용하고 OUT_OF_SCOPE 저장을 구조 검증에서 거부한다. 실제 env/key/개인정보를 읽지 않았다.
- Security: SQLSTATE만 매핑하고 native message/detail/parameter를 response/log에 반사하지 않는다. SQL은 고정된 schema-qualified constant와 positional parameter로만 실행된다. actor/filter/comment validation은 pool 접근 전 실행된다.
- Accessibility: UI·콘텐츠·포커스·반응형 변경 없음.
- Performance/cost: pool 상한 4이지만 import/open되지 않고, read는 불필요한 transaction을 열지 않는다. 실제 DB/provider 호출·외부 비용은 0원이다.

## 10. 데이터와 출처 영향

- 공식 데이터: 추가·수정·조회 실행 0. persistent official row 0 유지.
- mock/AI 생성: 테스트 내 synthetic typed value/fake pool만 사용했고 tracked/persistent mock row 0. AI/DeepSeek 생성물 0.
- schema/lineage: migration 5/5와 logical schema는 무변경. Task 8은 이미 승인된 function 시그니처를 Python model/repository로 반영했으며 manifest DB version은 Task 10 전까지 `0.2.0-draft`다.
- verified date: 2026-07-17 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- FastAPI의 내부 typed DB 경계는 구현됐지만 public route에 연결되지 않았고 실제 공식 데이터는 0건이다. 따라서 `/ready=503`이 정상이다.
- remote Supabase·public deploy·official seed·새 production dependency·OpenAPI/route 변경은 승인되지 않았고 실행하지 않았다.
- 오류 code는 DB의 `P1001~P1005`, `P1010`을 stable internal domain code로 바꾼다. 사용자에게 보이는 HTTP error 계약으로 연결하는 작업은 별도 수직 흐름에서 검토해야 한다.
- Task 9에서 실제 local PostgreSQL로 concurrency·idempotency·retention·전체 compensation/replay를 영구 게이트에 연결해야 DB-001 기술 인수기준이 완성된다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- `Sequence`는 `collections.abc`에서 import하고 concrete adapter는 tuple만 반환한다.
- psycopg JSON list parameter는 fresh list를 `Jsonb`로 감싸며 UUID/date/bool/nullable 타입을 native parameter로 유지한다.
- read는 connection context만, 모든 write는 connection+transaction context를 사용하고 success commit/failure rollback을 fake로 관찰했다.
- main import isolation은 별도 interpreter에서 DB driver/concrete module/pool/env read 부재를 검사한다.

## 13. 인수인계·재현·롤백

### 재현

1. branch `codex/db-001-layered-enforcement`에 commit `3cae552`가 있고 `git show --name-status 3cae552`가 정확히 위 10파일만 표시하는지 확인한다.
2. worktree root에서 `.\.tools\uv\uv.exe run --directory apps/api --frozen ruff format --check src tests`와 `ruff check src tests`를 실행한다.
3. 같은 frozen 환경에서 `mypy src tests`를 실행해 strict 22 files issue 0을 확인한다.
4. `pytest -q -p no:cacheprovider`를 실행해 156 pass+4 unittest subtests를 확인한다. pinned Starlette/httpx deprecation warning 1건은 알려진 non-failing warning이다.
5. `scripts/check_secret_patterns.ps1`, `scripts/validate_codex_package.py`, `git diff --check` 및 exact 10-file scope를 확인한다. global scope drift의 기존 package/ignored-tool 경고와 Task 8 file 0을 구분한다.

### 롤백

Task 8 production/test 변경은 DB 데이터와 schema를 변경하지 않으므로 `git revert 3cae552`로 되돌린다. 이후 기존 API 게이트와 Task 7 `274/274+4` DB 게이트를 재확인한다. DB compensation, seed 복구, 비밀 회전은 필요 없다.

### 다음 개발자 시작점

[DB-001 실행계획의 Task 9](../superpowers/plans/2026-07-16-db-001-layered-enforcement.md#task-9-prove-concurrency-idempotency-retention-boundaries-and-rollbackreplay)와 `.superpowers/sdd/task-8-report.md`를 읽고, real local DB integration 테스트 8개의 RED부터 시작한다. `00100~00500` migration과 Task 8 공개 Python 타입/SQL 시그니처는 baseline으로 유지한다.

## 14. 남은 위험·미해결 질문·다음 단계

- Task 9의 real DB integration, 동시 approval/reason confirmation, idempotency, retention boundary, backend private SELECT 거부, 모든 migration compensation/replay 영구 게이트가 남아 있다.
- `scripts/verify_database.ps1`의 rollback 목록은 없는 `20260716000400_indexes_and_read_interfaces.rollback.sql`을 가리키고 Task 6 candidate workflow compensation을 빠뜨린 stale 상태다. Task 9가 runner test RED를 먼저 추가한 뒤 actual `00500 → 00400 → 00300 → 00200 → 00100` 순서로 보정한다.
- pinned Starlette/httpx deprecation warning 1건은 test failure가 아니며 승인 없이 production dependency를 바꾸지 않았다. 의존성 승격 시 재검토한다.
- global `check_scope_drift.py`는 불변 package snapshot의 `PACKAGE_MANIFEST.json`과 ignored `.tools/isolated-repo`를 기존 경고로 보고한다. Task 8 변경 파일은 포함하지 않는다.
- 실제 공식 seed가 0이므로 `/ready=503`을 유지한다. DATA-001/DATA-SEED-001 승인 전에 임의로 바꾸지 않는다.
- 다음 단계: Task 9 concurrency·idempotency·retention·rollback/replay 영구 게이트.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증
- [x] source-of-truth/계약/버전 동기화 — 변경 필요 없음, manifest 전 축 유지
- [x] 개인정보 원문·native DB diagnostic·secret 노출 없음
- [x] 구현 노트 INDEX 갱신
- [x] 정확히 10파일 범위·독립 review C/I/M 0 기록
- [x] 재현·롤백·인수인계·인간/AI 경계 기록
