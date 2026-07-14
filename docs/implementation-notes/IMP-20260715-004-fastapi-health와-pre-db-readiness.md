# IMP-20260715-004 — FastAPI health와 pre-DB readiness

- Date/Time (KST): 2026-07-15T01:50:03+09:00 ~ 2026-07-15T02:36:55+09:00
- Task ID: DEV-001B
- Type: implementation
- Status: Done
- Author/Agent: `dev001b_implementer`(TDD·코드), Codex `/root`(lock/sync·실제 HTTP·검증·문서), `dev001b_code_reviewer`(독립 검토)
- Branch: `codex/DEV-001-repo-scaffold`
- Base commit: `1efe610`
- Related plan/ADR/RFP: PLAN-20260715-002 Task 2, ADR-0002, ADR-0009, SFR-001~002, SER-001~003

## 1. 사용자 요청과 완료 기준

### 요청

- 승인된 Phase 1을 계속 진행하되 코딩은 에이전트에게 위임하고, 중요한 의존성·명령·계약·검토는 `/root`가 맡는다.

### Acceptance Criteria

- exact 승인 의존성과 Python 3.12.13으로 `apps/api` lock과 새 격리 환경을 재현한다.
- `GET /health`는 외부 I/O 없이 정확히 200 `{"status":"ok"}`를 반환한다.
- DB·필수 승인 seed 전 `GET /ready`는 정확한 503 `SERVICE_UNAVAILABLE` envelope와 `Retry-After: 30`을 반환한다.
- readiness는 typed probe로 주입 가능하되 기본값은 not-ready이고 DB/provider 구현·호출은 0건이다.
- pytest, Ruff format/lint, strict mypy, 구조 테스트, 실제 uvicorn smoke와 독립 검토를 통과한다.
- 공개 OpenAPI·DB·데이터·LLM·chat/admin·환경/로그 경계는 변경하지 않는다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자가 승인했고, 구현 에이전트가 RED→GREEN 코드를 작성했으며 `/root`가 의존성·실행·계약 판단을 통제하고 fresh reviewer가 검토했다. |
| When — 언제 | 2026-07-15 KST, Phase 1 Task 2 |
| Where — 어디서 | 격리 worktree의 `apps/api`, root TASKS/plan/version/changelog, 구현 노트 |
| What — 무엇을 | import-safe FastAPI app factory, process health, pre-DB readiness, 엄격한 공개 모델, 테스트와 exact uv lock을 만들었다. |
| Why — 왜 | 제품 기능 전에 프로세스 생존과 아직 준비되지 않은 DB·승인 seed를 운영/프론트가 안정적으로 구분하게 하기 위해서다. |
| How — 어떻게 | 테스트 선작성, typed dependency injection, Pydantic `extra=forbid`, controller-owned uv lock/frozen sync, 실제 HTTP smoke, 독립 검토로 구현했다. |
| How much — 어느 정도 | API manifest/lock 2, source 6, test 2, API README 1; 직접 의존성 5·dev 4, lock 34 packages, pytest 5+subtest 2; DB/data/LLM 외부 호출 0건, 비용 0원 |

## 3. 시작 전 상태

- 관련 파일: `apps/api/AGENTS.md`·README placeholder, OpenAPI `/health`·`/ready`, ADR-0002/0009, Phase 1 상세 plan.
- 기존 동작: 활성 API manifest/source/test/lock과 실행 가능한 route가 0개였다.
- 발견한 충돌/부채:
  - DB task보다 API scaffold가 앞서므로 이 단계의 정상 readiness는 200이 아니라 503이다.
  - root shell의 Python 3.14에는 Windows IANA tzdata가 없어 note generator가 실패하지만 API venv에는 lock된 `tzdata`가 있다.
  - FastAPI 0.139.0의 TestClient fallback이 Starlette deprecation warning을 내며 `httpx2`를 권고한다.
- Git 상태: branch `codex/DEV-001-repo-scaffold`, base `1efe610`, remote 0, Task 2 시작 시 clean.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| READY-PREDB | Resolved | DB 전 readiness | 기본 probe false, 503; READY-001에서 DB+승인 seed 후 200 | 운영·후속 DB |
| READY-200-BODY | Defaulted | 미래 ready seam body | 최소 `{"status":"ready"}`; tracked OpenAPI 200 content가 미제약이고 task brief가 허용 | 후속 계약 drift |
| FASTAPI-DOC-DRIFT | Deferred | 생성 OpenAPI operationId/503 header metadata 차이 | tracked OpenAPI가 권위; CONTRACT-001B에서 정합화 | generated docs/type gate |
| HTTPX2-WARNING | Deferred human boundary | Starlette가 새 `httpx2` 의존성을 권고 | 승인된 `httpx==0.28.1` 유지, 새 prod dependency 추가 금지 | 향후 dependency update |
| UV-CACHE-ACL | Internal | Codex sandbox가 사용자 uv cache를 읽지 못함 | actual-user frozen sync; sandbox 검증은 ignored workspace `UV_CACHE_DIR` | local verification |

## 5. 설계 결정과 대안

### 선택

- `create_app(readiness_probe=...)` seam과 FastAPI dependency override를 사용한다.
- 기본 `PreDatabaseReadinessProbe`는 항상 false이며 DB/환경/provider를 import하지 않는다.
- public response model은 `Literal`, UUID, 길이 제한과 `extra="forbid"`를 사용한다.
- 503 body는 안정된 단일 code·일반 한국어 message·난수 request UUID·retryable만 공개한다.
- `package=false` src layout과 exact direct dependency, hash가 포함된 `uv.lock`을 사용한다.

### 이유

- future READY-001이 구현체만 교체할 수 있고 지금은 시작 시 외부 I/O가 없다.
- 내부 DB/provider 원인을 공개하지 않으면서 운영 도구가 liveness/readiness를 구분한다.
- lock과 strict test가 승인되지 않은 dependency·응답 필드 drift를 조기에 차단한다.

### 고려했지만 선택하지 않은 대안

- readiness 200 강제: 실제 DB·승인 seed가 없으므로 거짓 신호라 제외.
- route에서 직접 DB 연결: 단계 순서·import safety·장애 격리를 위반해 제외.
- `httpx2` 추가: 새 production dependency 인간 승인 전이므로 제외.
- 생성 FastAPI OpenAPI를 권위 계약으로 덮어쓰기: `contracts/openapi-v1.yaml` 단일 권위를 위반해 제외.
- raw exception/cause 공개: 보안·개인정보 정책을 위반해 제외.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| `apps/api/pyproject.toml` | package 0.1.0, Python range, exact prod/dev deps, pytest/Ruff/mypy config | API 실행·품질 계약 |
| `apps/api/uv.lock` | PyPI 34 packages, hashes, Python 3.12.13 compatible resolution | frozen 재현 |
| `src/sejong_ai_api/main.py` | import-safe app factory와 optional probe injection | startup I/O 0·테스트 seam |
| `api/health.py` | `/health`, `/ready`, protocol/default probe, 503 header/body | liveness/readiness 분리 |
| `contracts/health.py` | strict typed public response models | 공개 shape 제한 |
| `tests/test_health.py` | exact 200/503/header/UUID/금지 문자열/ready seam | wire behavior 회귀 |
| `tests/test_architecture.py` | exact deps/config·금지 import/constructor 검사 | provider/DB scope 차단 |
| `apps/api/README.md` | frozen 실행·범위·후속 경계 | 재현/인수인계 |

### 데이터 흐름/상태 변화

- `/health`: HTTP GET → 고정 typed body. probe/DB/provider/network/env 접근 0.
- 기본 `/ready`: HTTP GET → in-memory false probe → 새 UUID → 공개 503 JSON + retry header. 저장 0.
- 주입 ready test: fake probe true → 200 ready body. 실제 DB/provider 0.

### 오류·빈 상태·롤백

- DB/seed 미구현은 오류 누락이 아니라 의도된 503 empty-readiness 상태다.
- 내부 cause/stack/question/secret은 body에 넣지 않는다.
- task commit revert 시 API app/lock만 제거되며 DB/data migration이 없어 데이터 rollback은 없다.

## 7. 버전 전후

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application | 0.0.0-not-scaffolded | 0.0.1-api-scaffold | 첫 실행 가능한 API 수직 흐름; Web/전체 Phase 1 미완료 |
| Web | 0.0.0-not-scaffolded | 동일 | Web manifest/source 미구현 |
| API public contract | 2.0.0-draft | 동일 | tracked OpenAPI 변경 0 |
| API package | 없음 | 0.1.0 | health/pre-DB readiness 구현 |
| DB schema | 0.2.0-draft | 동일 | migration/연결 0 |
| Official data | 0.0.0-not-populated | 동일 | 데이터 0 |
| Mock data | 0.0.0-not-populated | 동일 | 데이터 0 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 동일 | LLM 코드/호출 0 |
| Test suite | 0.3.1-scaffold-contract | 0.3.2-api-health | API 동작 3 + 구조 2 tests |
| Repo guidance | 1.3.0 | 동일 | 공통 지침 변경 0 |
| Docs | 2.3.3 | 2.3.4 | API README·plan 명령·note/status 동기화 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| architecture tests before source | expected FAIL, exit 1 | 2 tests, 3 failures: pyproject/main/health missing | implementer report |
| behavior pytest before controller sync | expected FAIL, exit 1 | `No module named pytest` | implementer report |
| `.tools/uv/uv.exe lock --project apps/api` | PASS | CPython 3.12.13, 34 packages / 1.13s | `apps/api/uv.lock` |
| `.tools/uv/uv.exe sync --project apps/api --frozen` | PASS | 새 venv, 33 packages installed | controller terminal |
| first full pytest | PASS | 5 + subtest 2 / 4.33s; warning 1 | controller terminal |
| first Ruff/mypy gate | expected FAIL | format 7 files, import I001 1, mypy attr 1 | controller terminal |
| corrected pytest | PASS | 5 + subtest 2 / 2.08s; warning 1 | controller terminal |
| Ruff format/lint | PASS | 8 formatted; findings 0 | controller terminal |
| strict mypy | PASS | 8 files, issues 0 | controller terminal |
| architecture unittest | PASS | 2/2, 0.008s | controller terminal |
| `uv lock --check` | PASS | 34 packages, 3ms | controller terminal |
| lock source/credential scan | PASS | PyPI-only, suspect source/credential 0 | controller terminal |
| actual uvicorn + curl smoke | PASS | `/health=200`; `/ready=503`; retry 30; exact bodies | controller terminal, port 8765 |
| independent code/spec review | APPROVE | P0 0, P1 0, deferred P2 3 | `dev001b_code_reviewer` |
| fresh complete-delta final review | APPROVE | P0 0, P1 0, P2 2; 18/18 allowed paths | `dev001b_final_reviewer` |
| `git diff --check -- apps/api` | PASS | violations 0 | implementer/reviewer terminal |
| note generator with shell Python 3.14 | expected environment FAIL | `ZoneInfoNotFoundError: Asia/Seoul` | controller terminal |
| note generator with locked API Python | PASS | IMP-004 + INDEX | repository |

### 미실행 검증과 이유

- DB-backed `/ready=200`: DB migration·공식 승인 seed 전이므로 READY-001까지 금지.
- chat/admin/provider/PII/log tests: 해당 코드는 이 task에 없고 후속 vertical slice다.
- generated FastAPI OpenAPI와 tracked contract drift gate: CONTRACT-001B에서 operationId·503 header metadata를 포함해 처리.
- 성능 부하·100명 smoke: PERF-001 범위.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: 시민 질문·PII·token·request body 입력/저장/로그/전송 0건.
- Security: app import/startup 외부 I/O·secret/env 요구 0, public model extra 거부, 503 내부 원인 비공개, lock PyPI-only/credential 0.
- Accessibility: UI 변경 0. 프론트의 503 재시도 접근성은 WEB-CHAT-001에서 검증한다.
- Performance/cost: health path는 process-only, readiness는 단일 in-memory probe. 부하 측정 미실행; 외부 API·인프라 비용 0원.

## 10. 데이터와 출처 영향

- 공식 데이터: 변경/승인/ACTIVE 0건.
- mock/AI 생성: 테스트 fake boolean probe만 사용하며 행정 mock/AI 생성 데이터 0건.
- schema/lineage: OpenAPI·JSON Schema·DB schema·data lineage 변경 0.
- verified date: dependency lock·wire behavior 2026-07-15 KST; 공식 행정 데이터 해당 없음.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- 현재 `/ready=503`은 실패가 아니라 DB와 필수 승인 seed가 아직 없음을 정직하게 알리는 정상 상태다.
- API package 직접 의존성은 승인 목록 그대로 exact pin됐고 새 production dependency는 없다.
- TestClient 전이 경고가 `httpx2`를 권고하지만 자동 추가하지 않았다. 향후 dependency 변경은 인간 승인이 필요하다.
- 공개 계약 2.0.0-draft, DB, 데이터, DeepSeek, 배포/CORS/비밀은 변경하지 않았다.
- 생성 FastAPI 문서와 tracked OpenAPI의 operationId/503 header metadata 정합화는 CONTRACT-001B에 남아 있다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- dependency override closure는 app instance별 fake probe만 캡처한다.
- 구조 테스트는 AST로 main/health의 구체 I/O import와 연결 생성 이름을 제한한다.
- Codex sandbox의 user-cache ACL 차이는 ignored `.superpowers/uv-cache`로만 우회하며 제품 runtime에 포함되지 않는다.

## 13. 인수인계·재현·롤백

### 재현

1. root runtime contract test 6개를 통과한다.
2. `.\.tools\uv\uv.exe sync --project apps/api --frozen`을 실행한다.
3. `.\.tools\uv\uv.exe run --directory apps/api --frozen pytest -q`와 README의 Ruff/mypy 명령을 실행한다.
4. uvicorn을 `--app-dir src`로 띄워 `/health` 200과 `/ready` 503·retry header를 확인한다.
5. managed sandbox에서 user cache ACL이 다르면 Git-ignored workspace `UV_CACHE_DIR`만 사용한다.

### 롤백

- task commit을 `git revert`한다. `apps/api/.venv`는 ignored cache라 재생성 가능하고 commit 대상이 아니다.
- DB/data migration·외부 상태가 없어 보상 rollback, 데이터 복구, 비밀 폐기는 필요 없다.

### 다음 개발자 시작점

- DEV-001C Web shell을 구현한다. API readiness 200은 DB-001+DATA-SEED-001 이후 READY-001에서만 바꾼다.
- CONTRACT-001B에 generated OpenAPI operationId와 `Retry-After` metadata drift 항목을 전달한다.

## 14. 남은 위험·미해결 질문·다음 단계

- Starlette TestClient의 httpx fallback은 현재 동작하지만 향후 제거될 수 있다. 승인된 dependency 갱신 시 재평가한다.
- FastAPI generated OpenAPI는 tracked contract의 operationId/header metadata와 아직 다르다.
- raw body/log/env/browser-secret 경계는 DEV-002A 전까지 아직 구현/검증되지 않았다.
- 단일 local PC·원격/CI 부재 위험은 유지된다.

## 15. 자체 리뷰

- [x] 요청/Task 2 범위 충족
- [x] RED→GREEN·실제 HTTP·품질 gate 증거
- [x] 공개 계약/DB/data/provider 무변경
- [x] 개인정보 원문·secret 노출 없음
- [x] 구현 노트 INDEX 생성
- [x] 메타 문서·버전 반영 뒤 fresh final review
