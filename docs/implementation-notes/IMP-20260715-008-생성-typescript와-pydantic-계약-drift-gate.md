# IMP-20260715-008 — 생성 TypeScript와 Pydantic 계약 drift gate

- Date/Time (KST): 2026-07-15T13:41:29+09:00
- Task ID: CONTRACT-001B
- Type: implementation
- Status: Done
- Author/Agent: Codex `/root/contract001b_implement`; root 설치·검증; read-only reviewer 검토
- Branch: codex/DEV-001-repo-scaffold
- Base commit: 68740b9
- Related plan/ADR/RFP: PLAN-20260715-002 Task 6, ADR-0009, ADR-0010, SFR-001, SFR-003, SER-003, COR-001

## 1. 사용자 요청과 완료 기준

### 요청

승인된 OpenAPI 2.0.0-draft에서 결정적 TypeScript 타입을 생성하고, API Pydantic 모델이 CONTRACT-001A의 동일한 16개 합성 fixture를 strict raw JSON으로 소비하도록 만들어 프론트·백엔드 drift를 실행 시점 전에 차단한다.

### Acceptance Criteria

- `openapi-typescript@7.13.0`만 exact dev dependency로 추가하고 기존 TypeScript 5.9.3 peer를 재사용한다.
- 생성물 banner에는 상대 source, OpenAPI version, generator version만 두며 시간·절대 경로를 넣지 않는다.
- generate/check가 결정적 byte equality를 검증하고 생성 TypeScript 자체가 compile된다.
- request context optional nullable, response context required nullable, FALLBACK null, SUCCESS source 1개 이상을 strict Pydantic discriminated union으로 검증한다.
- 기존 503 모델을 재사용하고 같은 16개 raw JSON fixture의 valid/invalid 결과를 소비한다.
- scalar coercion, OpenAPI default optionality, FastAPI operationId/Retry-After metadata drift를 회귀 테스트로 차단한다.
- 공개 계약·fixture·DB·데이터·프롬프트·production dependency는 변경하지 않는다.

## 2. 육하원칙(6W1H)

| 항목 | 기록 |
|---|---|
| Who — 누가 | 사용자가 Phase 1 계획을 승인했고 구현 에이전트가 작성, root가 dependency install·gate, read-only reviewer가 spec/quality 검토 |
| When — 언제 | 2026-07-15 KST, Phase 1 Task 6 |
| Where — 어디서 | `packages/shared-contracts`, `apps/api`, root scripts/lock, 계획·버전·노트 |
| What — 무엇을 | generated TS, 결정적 generator/check, strict Pydantic chat models, raw fixture consumer와 FastAPI OpenAPI metadata gate |
| Why — 왜 | 공개 계약을 프론트/백엔드가 서로 다르게 해석하거나 permissive coercion으로 잘못 승인하는 것을 구현 전에 차단하기 위해 |
| How — 어떻게 | Node API+AST stringify, byte compare, Pydantic v2 discriminated union, TDD와 fresh review |
| How much — 어느 정도 | dev dependency 1개, shared tests 34, API tests 42+subtests 4, production dependency·DB migration·data/provider 호출 0 |

## 3. 시작 전 상태

- 관련 파일: OpenAPI 2.0.0-draft, 합성 fixture 16개, shared validator 30 tests, health/readiness strict response model.
- 기존 동작: generated source/helper와 chat Pydantic model/consumer가 없었고 FastAPI가 자동 operationId를 생성했다.
- 발견한 충돌/부채: OpenAPI default가 generated TS optional field를 required로 만들 수 있었고, Pydantic 기본 coercion은 JSON 숫자/문자열/boolean을 다른 scalar로 허용했다. IMP-004가 FastAPI operationId와 503 header metadata 정합을 이 Task로 명시 이월했다.
- Git 상태: base `68740b9`, branch `codex/DEV-001-repo-scaffold`, remote 없음, 시작 시 clean.

## 4. 미지의 영역·가정·인터뷰

| ID | 구분 | 내용 | 결정/기본값 | 영향 |
|---|---|---|---|---|
| TS-PEER | resolved | generator가 별도 TypeScript copy를 추가할 위험 | lock에서 기존 exact 5.9.3 한 copy 재사용 확인 | lock·재현성 |
| OFFICE-OPEN | accepted tradeoff | 두 계약 모두 Office nested extra를 허용하고 `source_url`은 optional non-null | `extra=allow`; omission 허용, explicit null field validator로 거부 | 향후 office 확장 호환성 |
| STRICT-JSON | resolved by review | Python dict validation은 UUID/date/URL JSON 표현과 scalar coercion을 혼동 | raw JSON API와 strict model/adapter 사용 | 계약 정확성 |
| FASTAPI-META | resolved from IMP-004 | 실제 wire는 맞지만 generated operationId/header metadata drift | route decorator metadata만 tracked contract와 정합 | generated OpenAPI |
| TSC-PATH | environment workaround | filtered `pnpm exec tsc`가 Windows PATH에서 local bin을 찾지 못함 | lock-resolved installed local `tsc.cmd` 직접 호출로 TypeScript 5.9.3 compile | 검증 명령 |

A/Blocker는 없었으며 이미 승인된 dev-only dependency와 공개 계약 안에서 처리했다.

## 5. 설계 결정과 대안

### 선택

- `openapi-typescript@7.13.0` Node API와 `astToString`을 사용하고 `alphabetize`, `arrayLength`, `silent`, `defaultNonNullable:false`를 고정했다.
- generator는 source/API/generator version을 읽어 상대 경로 banner를 만들고 tracked file과 fresh render를 byte 단위로 비교한다.
- Pydantic은 `Literal` answer status의 discriminated union과 UUID/date/AnyUrl을 쓰며 public intersection은 `extra=forbid, strict=True`다.
- `Office`만 계약 그대로 `extra=allow`이고, `source_url`은 field-level validator로 누락과 explicit null을 구분한다.
- 503은 기존 `ServiceUnavailableEnvelope`를 재사용하고 boolean singleton `true`를 명시적으로 검증한다.
- FastAPI health decorators의 operationId와 실제 존재하는 Retry-After wire header metadata를 tracked OpenAPI와 정합화했다.

### 이유

한 원본 OpenAPI에서 생성물을 재현하고 동일 JSON fixture를 runtime consumer까지 통과시켜, 수동 중복 타입과 permissive 언어 기본값이 계약 drift를 숨기지 못하게 하기 위해서다.

### 고려했지만 선택하지 않은 대안

- 수동 TypeScript interface: 원본 변경을 자동 추적하지 못해 제외했다.
- generated Pydantic model 추가 dependency: 기존 승인 runtime dependency와 명시적 모델이 충분해 제외했다.
- Office 전체 extra forbid 또는 `source_url` required화: 현재 OpenAPI/standalone 허용 범위를 깨므로 제외했다.
- generated TS만으로 `if/then` 불변조건 보장: generator가 해당 조건을 `unknown & unknown`으로 표현하므로 AJV/Pydantic runtime gate를 유지했다.
- durable 별도 generated-file tsc package script: 실제 FE 소비가 아직 없어 이번에는 direct compile 증거만 남기고 Task 7/FE 소비 단계에서 재평가한다.

## 6. 구현 상세

| 파일/영역 | 변경 내용 | 이유 |
|---|---|---|
| root/shared `package.json`, `pnpm-lock.yaml` | shared package 0.2.0, exact dev-only generator와 generate/check scripts | 재현 가능한 dependency/gate |
| `scripts/generate-api.mjs` | deterministic AST render, write/check와 상대 banner | 생성 drift 차단 |
| `src/generated/api.ts` | OpenAPI 2.0.0-draft generated TypeScript | FE 소비 기준 |
| shared generated test | helper/source/byte equality/banner/optional default/root command 회귀 | 생성 경계 고정 |
| API `contracts/chat.py` | strict request, Source/Office/Fallback, SUCCESS/FOLLOWUP/FALLBACK union | runtime 계약 소비 |
| API `contracts/health.py` | strict public base와 exact boolean true guard | 503 coercion 차단·model 재사용 |
| API fixture/health/architecture tests | raw 16 fixture, scalar coercion, generated OpenAPI metadata, no-I/O boundary | BE drift와 이월 부채 해소 |
| API/shared README, TASKS, CHANGELOG, plan, manifest, note/index | 명령·상태·버전·한계 동기화 | 인수인계 |

### 데이터 흐름/상태 변화

`contracts/openapi-v1.yaml → openapi-typescript AST → deterministic api.ts ↔ byte-check`와 `동일 합성 fixture JSON → AJV 계약 gate + strict Pydantic runtime model`의 두 경로다. FastAPI `app.openapi()`는 health operationId와 503 header metadata를 추가 검증한다. DB·provider·실제 시민 데이터 흐름은 없다.

### 오류·빈 상태·롤백

- generator/helper/source 누락, stale bytes, optional default drift는 shared test/check가 non-zero로 중단한다.
- missing/extra field, 잘못된 status/context/source, scalar coercion은 Pydantic ValidationError다.
- Office `source_url` omission은 허용하지만 explicit null은 거부한다.
- rollback은 Task 6 commit을 revert한다. API 2.0.0-draft/fixture/DB/data는 변경하지 않아 migration·데이터 복구가 없다.

## 7. 버전 전후

### 생성 시 매니페스트
- product_spec: 2.2.0
- repo_guidance: 1.3.0
- application: 0.0.3-security-boundaries
- web: 0.1.0
- api: 2.0.0-draft
- database_schema: 0.2.0-draft
- official_data: 0.0.0-not-populated
- mock_data: 0.0.0-not-populated
- prompt_set: 0.0.2-deepseek-v4-flash-selected
- test_suite: 0.3.5-contract-fixtures
- documentation: 2.3.7

| 축 | Before | After | 변경 이유 |
|---|---|---|---|
| Application | 0.0.3-security-boundaries | 0.0.4-contract-drift-gates | 생성/runtime drift gate 추가 |
| Web | 0.1.0 | 동일 | Web 제품 코드 변경 없음 |
| API | 2.0.0-draft | 동일 | tracked public contract/wire 변경 없음 |
| Shared contracts | 0.1.0 | 0.2.0 | 생성 타입과 check 추가 |
| DB schema | 0.2.0-draft | 동일 | migration 없음 |
| Official data | 0.0.0-not-populated | 동일 | 공식 데이터 없음 |
| Mock data | 0.0.0-not-populated | 동일 | 제품 mock seed 없음; contract fixture만 합성 |
| Prompt set | 0.0.2-deepseek-v4-flash-selected | 동일 | LLM 호출/프롬프트 변경 없음 |
| Test suite | 0.3.5-contract-fixtures | 0.4.0-contract-drift-gates | generated/Pydantic/FastAPI drift 회귀 추가 |
| Docs | 2.3.7 | 2.3.8 | Task 6 문서·노트 동기화 |

## 8. 명령과 테스트 증거

| 명령/검증 | 결과 | 시간/개수 | 증거 경로 |
|---|---|---|---|
| `node --test test/generated-api.test.mjs` (구현 전) | expected RED, exit 1 | 0 pass, helper/source 누락 2 fail, 1 skip | terminal output |
| API fixture consumer pytest (구현 전) | expected RED, exit 1 | collection error: `contracts.chat` 없음 | terminal output |
| architecture focused (chat source 추가 전) | expected RED, exit 1 | 2 pass+3 subtests, missing chat subfail | terminal output |
| shared generator focused 최초 GREEN | exit 0 | 3/3 pass, fresh render 2회 byte equality | terminal output |
| raw JSON strict review regression | expected RED, exit 1 | 18 pass/3 fail: bool·retryable coercion 미거부, Office pre-validator의 strict date 손실; confidence string은 이미 거부 | terminal output |
| chat+health strict focused | exit 0 | 24/24 pass, warning 1 | terminal output |
| root `contracts:check` nested pnpm | expected operational RED, exit 1 | 요구 11.13.0, PATH 11.7.0 | terminal output |
| root direct-helper regression | RED 3 pass/1 fail → GREEN 4/4 | unpinned nested pnpm 제거 | generated-api test |
| optional-default regression | expected RED 3 pass/1 fail → GREEN 4/4 | `simple_language: boolean`을 `?: boolean`로 재생성 | generated-api test |
| FastAPI generated metadata focused | expected RED 3 pass/2 fail → GREEN 5/5 | operationId 2개와 Retry-After schema | `test_health.py` |
| warm-store `corepack.cmd pnpm install --frozen-lockfile --offline` | exit 0 | 3 workspace, pnpm 11.13.0, already up to date | terminal output |
| shared package full test | exit 0 | 34/34 pass | terminal output |
| `corepack.cmd pnpm contracts:check` | exit 0 | fresh render byte equality | terminal output |
| generator `node --check` | exit 0 | syntax error 0 | terminal output |
| API ruff format/check | exit 0 | 13 files formatted; lint error 0 | terminal output |
| API strict mypy | exit 0 | 13 source files, issue 0 | terminal output |
| API full pytest | exit 0 | 42 pass+4 subtests, 기존 Starlette/httpx2 warning 1 | terminal output |
| generated TS direct TypeScript 5.9.3 compile | exit 0 | error/output 0 | local `apps/web/node_modules/.bin/tsc.cmd` |
| note generator system Python | expected operational failure 후 대체 성공 | Windows system Python tzdata 없음; API venv로 IMP-008 생성 | terminal output |
| `python -B scripts/validate_codex_package.py` | exit 0 | required files 12, manifest valid | terminal output |
| `scripts/check_secret_patterns.ps1` | exit 0 | finding/output 0 | terminal output |
| explicit manifest JSON parse | exit 0 | `MANIFEST JSON PASS` | terminal output |
| `git diff --check 68740b9` | exit 0 | tracked delta whitespace error 0; INDEX CRLF future-normalization warning만 | terminal output |
| stage 후 `git diff --cached --check` | exit 0 | 신규 파일을 포함한 whitespace error 0 | root completion gate |

### 미실행 검증과 이유

- 실제 chat route/E2E는 아직 구현되지 않아 실행하지 않았다. 이 단계는 contract consumer model까지만 범위다.
- filtered `pnpm exec tsc`는 Windows PATH가 존재하는 local tsc shim을 찾지 못해 실패했다. lock-resolved installed local TypeScript 5.9.3의 `tsc.cmd` 직접 호출은 exit 0이었고 durable script는 실제 FE 소비 또는 Task 7에서 재평가한다.
- tracked delta 검사 뒤 root가 신규 파일을 stage하고 `git diff --cached --check`까지 exit 0으로 확인했다.

## 9. 보안·개인정보·접근성·성능 영향

- Privacy: fixture는 `시연용 샘플`, 합성 UUID, `example.invalid`뿐이며 질문 원문·PII·token을 저장/전송하지 않는다.
- Security: strict raw JSON/extra forbid/scalar coercion 거부로 public boundary confusion을 줄였다. Office extra allow는 공개 계약상 의도된 예외다.
- Accessibility: UI 변경 없음.
- Performance/cost: 외부 API/DB 호출과 인프라 비용 0원. generator/test는 local dev-only이며 production bundle/runtime dependency가 아니다.

## 10. 데이터와 출처 영향

- 공식 데이터: 추가·수정·승인 0건.
- mock/AI 생성: 제품 mock seed 0건; 기존 contract fixture 16개만 소비하며 모두 `시연용 샘플`이다.
- schema/lineage: OpenAPI 2.0.0-draft와 standalone/fixture 내용은 불변, DB migration 0. generated TS lineage는 banner의 상대 source/API/generator version이다.
- verified date: 2026-07-15 KST.

## 11. 인간이 반드시 알아야 하거나 승인할 내용

- API public revision은 `2.0.0-draft` 그대로이며 OpenAPI/standalone/fixture의 wire 계약은 바꾸지 않았다.
- 새 의존성은 승인된 exact dev-only `openapi-typescript@7.13.0` 하나이며 기존 TypeScript 5.9.3 peer를 재사용한다. production dependency·외부 비용은 0이다.
- generated TypeScript는 OpenAPI `if/then`의 SUCCESS sources≥1/FALLBACK context-null을 정적 타입으로 완전 표현하지 못한다. 따라서 AJV/Pydantic fixture gate를 대체하지 않는다.
- Office가 알 수 없는 nested field를 허용하는 것은 현재 공개 계약을 그대로 따른 tradeoff다. 더 엄격하게 만들거나 `source_url`을 required로 바꾸려면 공개 계약 승인과 version 판단이 필요하다.
- DB migration, 데이터 삭제, 공식 데이터 ACTIVE, 배포/CORS/DeepSeek/public route는 실행하지 않았다.

## 12. AI 내부 구현 세부 — 필요할 때만 보면 되는 내용

- generator의 AST option 순서, LF normalization, banner 조립과 byte comparison helper 분리는 계약 내 구현 세부다.
- scalar strictness는 공통 `StrictPublicModel`과 field-level 예외로 구현했고, helper/fixture 명명·test parameterization은 행동 불변 내부 세부다.
- root script는 nested package manager dispatch 대신 deterministic Node helper를 직접 호출해 PATH의 다른 pnpm을 피한다.

## 13. 인수인계·재현·롤백

### 재현

저장소 루트에서 다음 순서로 실행한다.

```powershell
corepack.cmd pnpm install --frozen-lockfile
.\.tools\uv\uv.exe sync --project apps/api --frozen
corepack.cmd pnpm contracts:check
corepack.cmd pnpm --filter @sejong-ai/shared-contracts test
.\apps\web\node_modules\.bin\tsc.cmd --noEmit --strict --skipLibCheck --target ES2022 packages\shared-contracts\src\generated\api.ts
.\apps\api\.venv\Scripts\python.exe -B -m pytest apps\api\tests -q
.\apps\api\.venv\Scripts\python.exe -B -m ruff format --check apps\api\src apps\api\tests
.\apps\api\.venv\Scripts\python.exe -B -m ruff check apps\api\src apps\api\tests
.\apps\api\.venv\Scripts\python.exe -B -m mypy --strict apps\api\src apps\api\tests
```

OpenAPI를 승인 변경한 경우 `corepack.cmd pnpm contracts:generate` 후 generated diff와 runtime fixture 결과를 함께 검토한다.
첫 설치는 network/cache를 사용할 수 있는 기본 frozen 명령을 사용한다. store가 준비된 환경에서만 `corepack.cmd pnpm install --frozen-lockfile --offline`을 선택적 warm-cache 재현성 검사로 추가한다.

### 롤백

Task 6 commit을 `git revert <task-6-sha>`로 되돌린다. lock/package/source/test/docs를 같은 단위로 되돌리며 history를 삭제하지 않는다. DB/data/provider 복구는 없다.

### 다음 개발자 시작점

`packages/shared-contracts/scripts/generate-api.mjs`, `apps/api/src/sejong_ai_api/contracts/chat.py`, 두 generated/fixture test를 먼저 읽고 Task 7 단일 local verify runner에 현재 명령을 연결한다.

## 14. 남은 위험·미해결 질문·다음 단계

- generated TS의 `unknown & unknown`은 JSON Schema conditional을 정적으로 보장하지 못하므로 runtime AJV/Pydantic gate를 계속 필수로 실행한다.
- durable generated-file tsc script는 아직 없다. 실제 FE import를 추가할 때 app typecheck 포함 여부를 정하고 Task 7에서도 재평가한다.
- FastAPI generated OpenAPI 전체와 tracked OpenAPI 전체의 일반 목적 diff는 아직 없다. 이 Task는 명시적으로 이월된 health/readiness metadata만 닫았다.
- 기존 Starlette TestClient/httpx2 deprecation warning 1은 승인 dependency 밖 변경이므로 남겼다.
- 다음 단계는 DEV-001D 단일 clean local verify, actual health smoke와 fresh final review다.

## 15. 자체 리뷰

- [x] 요청 충족
- [x] 테스트/검증
- [x] source-of-truth/계약/버전 동기화
- [x] 개인정보 원문 노출 없음
- [x] 구현 노트 INDEX 갱신
