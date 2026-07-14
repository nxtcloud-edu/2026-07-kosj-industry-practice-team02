# PLAN-20260715-002 — Phase 1 스캐폴딩·health·환경 경계·계약 gate

## 상태

In Progress — 상위 `PLAN-20260714-001`을 2026-07-15 사용자가 `진행`으로 승인했으며, 이 문서는 승인된 첫 수직 흐름을 독립 리뷰 가능한 단위로 세분화한다.

## 목표와 비목표

- 목표:
  - Node 24/pnpm, Python 3.12/uv를 exact pin한 재현 가능한 local-first 모노레포를 만든다.
  - 최소 Next.js 앱과 FastAPI 앱을 만들고 `/health=200`, DB·승인 seed 전 `/ready=503`을 계약과 테스트로 고정한다.
  - 브라우저/서버 환경변수 경계와 raw request body 비기록을 자동 검증한다.
  - OpenAPI 2.0.0-draft, JSON Schema, 생성 TypeScript 타입, FastAPI/Pydantic 소비 모델의 핵심 불변조건 drift를 0으로 만든다.
  - clean install, lint, format, typecheck, unit/contract test, build, health smoke를 단일 local gate로 재현한다.
- 비목표:
  - DB migration·Supabase local stack·공식/모의 seed
  - `/api/v1/chat` 검색/LLM/PII/응답 구현과 `/chat`, `/admin` 제품 UI
  - DeepSeek 실제 호출, 공개 배포, 원격 Git/CI, 실제 시민 데이터
  - 승인 목록 밖의 프로덕션 의존성

## 사용자 가치와 인수 기준

- 사용자 가치:
  - 새 개발자는 문서와 lockfile만으로 같은 환경을 재현하고, 제품 기능 전에도 프로세스 생존과 아직 준비되지 않은 의존성을 구분할 수 있다.
  - 비밀과 질문 원문이 프론트 번들·로그로 새지 않는 경계가 기능 구현 전에 자동으로 고정된다.
- Acceptance Criteria:
  - root `packageManager`, `.node-version`, `.python-version`, pnpm/uv lock이 exact하며 clean install이 통과한다.
  - web lint/typecheck/unit/build와 API ruff format/lint, mypy, pytest가 통과한다.
  - `GET /health`는 비밀·내부 상세 없이 200 `{"status":"ok"}`를 반환한다.
  - DB·필수 승인 seed 전 `GET /ready`는 503 `SERVICE_UNAVAILABLE` envelope와 `Retry-After`를 반환하며 provider를 호출하지 않는다.
  - root `.env.example`은 서비스 파일을 가리키는 안내만 포함하고, `apps/web/.env.example`에는 `NEXT_PUBLIC_` allowlist 외 서버 비밀 이름이 0개다.
  - sentinel 질문을 포함한 요청 후 app/access/error log에 sentinel과 request body가 0건이다.
  - `.next` client/static 산출물에 `SUPABASE_SERVICE_ROLE_KEY`, `LLM_API_KEY`, `CONTEXT_TOKEN_SECRET`, `DATABASE_URL` 이름·sentinel 값이 0건이다.
  - SUCCESS fixture는 source 1개 이상일 때만 두 계약에서 통과하고, 빈 source SUCCESS는 둘 다 실패한다.
  - `Fallback.office`와 request optional nullable/response required nullable `context_token`, FALLBACK-null, `session_id` 거부가 OpenAPI/JSON Schema 공통 fixture로 고정된다.
  - 생성 타입을 재생성한 뒤 tracked diff가 0이며, 503 exact envelope fixture가 통과한다.
  - 제품 코드는 web/API scaffold·health·계약 gate로 제한하고, DB migration·공식/모의 데이터·외부 LLM 호출은 0건이다.

## 권위 근거

- RFP ID: SFR-001, SFR-002, SER-001~003, COR-001~002, QUR-001~002
- source-of-truth: `docs/source-of-truth/TEAM_DECISIONS.md`, `PROJECT_PLAN.md`, `PRIVACY_POLICY.md`, `RFP_MATRIX.md`
- ADR: ADR-0002, ADR-0004, ADR-0007, ADR-0009, ADR-0010
- 계약/운영: `contracts/openapi-v1.yaml`, `contracts/chat-response.schema.json`, `docs/05_API_AND_CONTRACTS.md`, `docs/15_DEPLOYMENT_AND_OPERATIONS.md`
- 관련 구현 노트: `IMP-20260715-001`, `IMP-20260715-002`

## 현재 상태와 조사 결과

- 활성 코드: `apps/web`, `apps/api`, `packages/shared-contracts`에 README/AGENTS만 있고 실행 manifest·source·test·lock이 없다.
- Git: 독립 `main` 기준선 `5682804`; 격리 branch/worktree `codex/DEV-001-repo-scaffold`.
- 도구: Node 24.12.0, npm 11.6.2, Corepack 0.34.5, Docker CLI 29.2.1/Compose 5.0.2. pnpm·uv·Python 3.12·Supabase CLI는 아직 없다.
- legacy 참고: 정적 레이아웃 아이디어만 참고 가능하며 legacy Python/HTML/API/seed는 활성 코드로 복사하지 않는다.
- 확인한 명령: package validator, secret pattern scan, Git 상태/remote/worktree, Node/Python/Docker 인벤토리, npm/PyPI 공식 registry version/peer metadata 조회.
- 발견한 충돌:
  - DEV-001은 DB보다 앞서므로 `/ready=200`을 요구할 수 없다. 이 단계의 정상값은 503이며 DB·승인 seed 후 200으로 전환한다.
  - OpenAPI와 JSON Schema 모두 SUCCESS의 빈 `sources`를 허용한다.
  - OpenAPI `Fallback`은 `office`를 허용하지만 JSON Schema는 `additionalProperties:false`로 거부한다.
  - root `.env.example`에 프론트와 backend-only 변수가 섞여 있다.
  - `check_scope_drift.py`는 `PACKAGE_MANIFEST.json` 속 legacy 경로 문자열을 활성 범위로 오탐한다.

## 미지의 영역과 인터뷰

| ID | 영향 | 질문 | 상태 | 결정 |
|---|---|---|---|---|
| READY-PREDB | 운영·테스트 | DB 전 readiness | Defaulted, 기록 완료 | `/health=200`, `/ready=503`; DB/승인 seed 후 별도 작업에서 200 |
| DEP-EXACT | 재현·보안 | exact dependency 조합 | Resolved by official registry metadata + clean build gate | 아래 표 exact pin, lock이 최종 권위 |
| PY312-PATCH | 런타임 | uv managed Python 3.12 exact patch | Task 1에서 resolver가 제공하는 최신 3.12 patch를 설치한 뒤 `.python-version` exact 기록 | 그 전 앱 dependency lock 금지 |
| CONTRACT-STATUS | 공개 계약 | 이미 승인된 불변조건 표현 | Resolved | 새 동작 추가 없이 SUCCESS source≥1, FALLBACK-null, office drift만 정합화 |
| PUBLIC/REAL | 개인정보·비용·배포 | public/실제 시민 provider | Deferred human decision | 이 계획에서 금지 유지 |

## 엔지니어링 제안 exact dependency 후보

패키지 이름과 production dependency 경계는 사용자가 승인했고, 아래 exact patch는 2026-07-15 KST 공식 npm/PyPI registry metadata를 근거로 AI가 제안했다. peer/engine과 clean install/build가 통과해야 lock에 확정한다. 후보를 바꿀 때는 같은 승인 패키지 안에서 최소 변경하고 metadata·실패 원인·대안을 기록한다.

| 영역 | 구분 | Exact candidate |
|---|---|---|
| Tooling | Node / pnpm / uv | `24.12.0` / `11.13.0` / `0.11.28` |
| Web runtime | next / react / react-dom | `16.2.10` / `19.2.7` / `19.2.7` |
| Web build/dev | TypeScript / @types/node / @types/react / @types/react-dom | `5.9.3` / `24.13.3` / `19.2.17` / `19.2.3` |
| Web style/dev | tailwindcss / @tailwindcss/postcss | `4.3.2` / `4.3.2` |
| Web quality/dev | eslint / eslint-config-next / vitest / jsdom | `10.7.0` / `16.2.10` / `4.1.10` / `29.1.1` |
| Web test/dev | @testing-library/react / @testing-library/dom / @testing-library/jest-dom | `16.3.2` / `10.4.1` / `6.9.1` |
| API runtime | fastapi / uvicorn / pydantic / httpx | `0.139.0` / `0.51.0` / `2.13.4` / `0.28.1` |
| API DB runtime | psycopg / psycopg-binary / psycopg-pool | `3.3.4` / `3.3.4` / `3.3.1` |
| API quality/dev | pytest / pytest-asyncio / ruff / mypy | `9.1.1` / `1.4.0` / `0.15.21` / `2.3.0` |
| Contract/dev | openapi-typescript / ajv / ajv-formats / yaml | `7.13.0` / `8.20.0` / `3.0.1` / `2.9.0` |

Tailwind와 모든 test/lint/type generator는 build/dev dependency다. 새 브라우저 또는 서버 runtime dependency가 필요하면 구현을 멈추고 사용자 승인을 받는다.

## 제안 설계

- 데이터 흐름:
  - `/health`: process-only, 외부 I/O 0 → 고정 최소 body.
  - `/ready`: injectable readiness probe → DB/필수 승인 seed가 아직 없으므로 기본 probe는 not-ready → 공개 503 envelope. provider/LLM은 검사하지 않는다.
  - web은 이 단계에서 정적 shell만 빌드하며 API 질문을 보내지 않는다.
- 컴포넌트 경계:
  - root: workspace, runtime pin, 공통 명령과 검증.
  - `apps/web`: Next App Router, TypeScript strict, Tailwind build-time styling, browser-safe env만.
  - `apps/api`: FastAPI app factory/router, typed health/error models, metadata-only logging, server env만.
  - `packages/shared-contracts`: OpenAPI 생성 타입, schema fixtures와 drift test만; runtime business logic 없음.
- API/DB 변경:
  - `/health`와 pre-DB `/ready`만 실제 구현한다. Chat/admin route와 DB schema/migration은 구현하지 않는다.
  - OpenAPI 2.0.0-draft는 기존 승인 동작을 더 엄격히 표현하되 route/version은 유지한다.
- 보안/개인정보:
  - raw body를 읽거나 기록하는 middleware를 만들지 않는다. log allowlist는 method/path/status/request_id만이다.
  - web env와 client bundle은 explicit deny markers로 검사한다. secret scan은 값 내용을 출력하지 않고 경로/개수만 보고한다.
- 실패/장애 처리:
  - readiness 503은 오류가 아니라 의존성 준비 전 정상 상태다.
  - 도구 설치/registry가 실패하면 임의 버전으로 진행하지 않고 원인·명령을 기록한다.
  - contract generator 결과가 바뀌면 자동 반영하지 않고 원본 계약 diff부터 검토한다.

## 단계별 구현

### Task 1 — DEV-001A exact runtime과 root workspace contract

**Files**

- Create: `package.json`, `pnpm-workspace.yaml`, `.npmrc`, `.node-version`, `.python-version`
- Create: `scripts/tests/__init__.py`, `scripts/tests/test_repository_scaffold.py`
- Modify: `.gitignore`, `README.md`, `TASKS.md`
- Create/update: `docs/implementation-notes/IMP-20260715-003-*.md`, `docs/implementation-notes/INDEX.md`, `versions/manifest.json`

**TDD/steps**

1. 표준 라이브러리 unittest로 root manifest, exact package manager, engine range, workspace, runtime pins가 없어서 실패하는 RED를 작성하고 실행한다.
2. root workspace 파일만 최소 구현한다. root에는 production dependency를 두지 않는다.
3. `corepack.cmd`으로 pnpm 11.13.0을 준비하고 version을 확인한다.
4. `/root`가 `py -3.11 -m pip install --user uv==0.11.28`로 uv를 설치하고 이후 모든 명령은 `py -3.11 -m uv`로 호출한다.
5. managed Python 3.12 최신 patch를 설치하고 실제 `python --version`을 확인한 뒤 `.python-version`에 exact pin한다.
6. RED 테스트가 GREEN인지 확인하고 note/versions를 동기화한다.

**Commands/evidence**

- `python -B -m unittest scripts.tests.test_repository_scaffold -v` — RED 후 GREEN
- `node --version`; `corepack.cmd pnpm --version`
- `py -3.11 -m pip install --user uv==0.11.28`; `py -3.11 -m uv --version`
- `py -3.11 -m uv python install 3.12`; `py -3.11 -m uv run --python 3.12 python --version`; `py -3.11 -m uv python find 3.12`
- `git diff --check`; scoped secret scan; self-review

**Commit**: `chore: pin repository runtimes and workspace`

### Task 2 — DEV-001B FastAPI health와 pre-DB readiness

**Files**

- Create: `apps/api/pyproject.toml`, `apps/api/uv.lock`
- Create: `apps/api/src/sejong_ai_api/__init__.py`, `main.py`, `api/__init__.py`, `api/health.py`, `contracts/health.py`
- Create: `apps/api/tests/test_health.py`, `apps/api/tests/test_architecture.py`
- Modify: `apps/api/README.md`, `contracts/openapi-v1.yaml` only if implementation-shape correction is required
- Create/update: `IMP-20260715-004-*.md`, INDEX, manifest, changelog

**TDD/steps**

1. TestClient로 `/health` 200 최소 body, `/ready` 503 exact envelope/header, provider I/O 0을 먼저 실패시킨다.
2. `package=false` src-layout, pytest `pythonpath=["src"]`, mypy `mypy_path="src"`와 exact API deps/dev deps를 선언하고 uv lock/sync한다.
3. app factory, typed models, health router와 injectable `ReadinessProbe`를 만들고 pre-DB 기본 구현만 not-ready로 둔다.
4. ruff format/lint, mypy, pytest를 통과시킨다.

**Commands/evidence**

- `py -3.11 -m uv lock --project apps/api`; `py -3.11 -m uv sync --project apps/api --frozen`
- `py -3.11 -m uv run --project apps/api pytest -q`
- `py -3.11 -m uv run --project apps/api ruff format --check .`; `py -3.11 -m uv run --project apps/api ruff check .`; `py -3.11 -m uv run --project apps/api mypy src tests`
- local uvicorn smoke에서 `/health=200`, `/ready=503` 확인
- `py -3.11 -m uv run --project apps/api uvicorn sejong_ai_api.main:app --app-dir apps/api/src --host 127.0.0.1 --port 8000`

**Commit**: `feat(api): add health and pre-db readiness`

### Task 3 — DEV-001C 최소 Next.js web scaffold

**Files**

- Create: `apps/web/package.json`, `tsconfig.json`, `next.config.ts`, `postcss.config.mjs`, `eslint.config.mjs`, `vitest.config.ts`
- Create: `apps/web/src/app/layout.tsx`, `page.tsx`, `globals.css`, `apps/web/src/test/setup.ts`
- Create: `apps/web/src/app/page.test.tsx`
- Create/update: root `pnpm-lock.yaml`, `apps/web/README.md`, `IMP-20260715-005-*.md`, INDEX, manifest, changelog

**TDD/steps**

1. 서비스명·핵심 원칙·지원 범위 안내 shell의 접근 가능한 heading/link test를 RED로 작성한다.
2. 승인된 exact runtime 및 build/dev dependency를 선언한다. 새 runtime dependency는 추가하지 않는다.
3. 의미론적 최소 App Router shell과 visible focus/base contrast token을 구현한다. `/chat` 제품 동작은 아직 구현하지 않는다.
4. install, lint, typecheck, unit, build를 통과시킨다.

**Commands/evidence**

- `corepack.cmd pnpm install --frozen-lockfile` (lock 생성 전 최초 1회는 `--lockfile-only` 후 검토)
- `corepack.cmd pnpm --filter @sejong-ai/web lint`
- `corepack.cmd pnpm --filter @sejong-ai/web typecheck`; `corepack.cmd pnpm --filter @sejong-ai/web test`; `corepack.cmd pnpm --filter @sejong-ai/web build`

**Commit**: `feat(web): add accessible Next.js application shell`

### Task 4 — DEV-002A 환경변수·로그·secret/browser boundary

**Files**

- Modify: root `.env.example` to service-pointer only
- Create: `apps/web/.env.example`, `apps/api/.env.example`
- Create: `apps/api/src/sejong_ai_api/core/logging.py`, `apps/api/tests/test_safe_logging.py`
- Create: `scripts/check_secret_patterns.ps1`, `scripts/check_web_bundle_secrets.mjs`, related standard-library tests
- Modify: `SECURITY.md`, `docs/07_SECURITY_PRIVACY.md`, `docs/22_OBSERVABILITY_POLICY.md`, TASKS
- Create/update: `IMP-20260715-006-*.md`, INDEX, manifest, changelog

**TDD/steps**

1. web env deny-name test, log sentinel test, missing-build/clean-build scanner test를 먼저 실패시킨다.
2. server-only/browser-safe env 파일을 분리하고 allowlist 문서를 적는다.
3. method/path/status/request_id만 기록하는 metadata middleware를 구현한다. body/header/query content는 기록하지 않는다.
4. secret scan은 실제 값 내용을 출력하지 않고 non-zero exit와 파일 경로만 반환하도록 구현한다.
5. web build 뒤 server-only marker name/value 0건을 확인한다.

**Commands/evidence**

- API pytest safe logging tests
- `powershell -File scripts/check_secret_patterns.ps1`
- `node scripts/check_web_bundle_secrets.mjs apps/web/.next`
- web build, API quality gate 재실행

**Commit**: `feat(security): enforce env and logging boundaries`

### Task 5 — CONTRACT-001A 승인 불변조건과 공통 fixtures

**Files**

- Modify: `contracts/openapi-v1.yaml`, `contracts/chat-response.schema.json`
- Create: `contracts/fixtures/chat-request/*.json`, `contracts/fixtures/chat-response/*.json`, `contracts/fixtures/errors/*.json`
- Create: `packages/shared-contracts/package.json`, contract test source/config
- Create/update: `IMP-20260715-007-*.md`, INDEX, manifest, changelog

**TDD/steps**

1. 기존 두 계약에서 빈-source SUCCESS가 잘못 통과하고 `Fallback.office`가 drift하는 것을 실패 테스트로 재현한다.
2. SUCCESS일 때 `sources.minItems=1`, FALLBACK일 때 `context_token=null`을 양쪽 계약에 동일하게 표현한다.
3. JSON Schema의 `Fallback.office`를 OpenAPI `Office`와 동기화한다.
4. artifact matrix를 고정한다: response fixture는 OpenAPI에서 추출한 `ChatResponse`와 standalone JSON Schema 양쪽에서 검사하고, request/503 fixture는 각각 OpenAPI `ChatRequest`/`ServiceUnavailableEnvelope`에서 검사한다.
5. request `context_token` optional nullable, response required nullable, `session_id` 거부, 503 exact envelope fixtures를 고정한다.
6. 새 공개 동작이나 enum은 추가하지 않고 API version `2.0.0-draft`를 유지한다.

**Commands/evidence**

- shared-contracts unit/fixture test RED→GREEN
- JSON/YAML parse, fixture matrix pass/fail count
- `python -B scripts/validate_codex_package.py`

**Commit**: `fix(contracts): enforce grounded response invariants`

### Task 6 — CONTRACT-001B 생성 TypeScript와 API model drift gate

**Files**

- Create: `packages/shared-contracts/src/generated/api.ts`, generator/check scripts
- Create: `apps/api/src/sejong_ai_api/contracts/chat.py`, API fixture-consumer tests
- Modify: root/package scripts and lock as needed with dev-only contract deps
- Create/update: `IMP-20260715-008-*.md`, INDEX, manifest, changelog

**TDD/steps**

1. 생성 파일 부재와 Pydantic fixture validation 부재를 RED로 만든다.
2. OpenAPI→TypeScript를 결정적 명령으로 생성하고 banner에 source/version을 기록한다.
3. Pydantic discriminated response/error models로 동일 fixtures를 검증한다.
4. 재생성 뒤 `git diff --exit-code`가 0인지 검사한다.

**Commands/evidence**

- `corepack.cmd pnpm --filter @sejong-ai/shared-contracts generate`
- shared contract tests and `git diff --exit-code -- packages/shared-contracts/src/generated/api.ts`
- API ruff/mypy/pytest

**Commit**: `feat(contracts): add generated and runtime drift gates`

### Task 7 — DEV-001D/DEV-002B clean local verification과 문서 마감

**Files**

- Create: `scripts/verify.ps1`
- Modify: `README.md`, `FIRST_RUN_CHECKLIST.md`, `scripts/README.md`, `TASKS.md`, plan progress/result, `versions/manifest.json`, `CHANGELOG.md`
- Create/update: `IMP-20260715-009-*.md`, INDEX

**TDD/steps**

1. verify runner가 필요한 단계/종료코드를 검사하는 standard-library test를 RED로 작성한다.
2. clean/frozen install→web→API→contract→secret/bundle→package validation 순서와 fail-fast를 구현한다.
3. local server smoke를 별도로 실행해 실제 HTTP status/body/header를 기록한다.
4. 전체 diff를 스스로 검토하고 별도 에이전트의 spec/quality 리뷰를 모두 통과시킨다.

**Commands/evidence**

- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify.ps1`
- clean/frozen install, all tests/lint/typecheck/build, generator diff, secret scans
- `git diff --check`, `git status`, scoped secret scan

**Commit**: `chore: complete phase one local verification`

## 에이전트 실행 규칙

- 한 번에 하나의 구현 에이전트만 shared worktree에 쓴다.
- 각 Task는 fresh 구현자 → fresh spec/quality 검토자 → 필요 시 같은 구현자 수정 → 재검토 순서다.
- 각 구현자는 RED 출력, GREEN 출력, 변경 파일, 보안 영향, commit SHA를 report에 남긴다.
- `/root`는 dependency/설치/Git 명령, 계약·보안 판단, 최종 diff와 완료 판정을 직접 수행한다.
- `.superpowers/sdd/`의 brief/report/review package/progress는 ignored transient evidence이며 핵심 결과는 implementation note로 승격한다.

## 테스트 계획

- 단위: root config contract, web render, API health/readiness, safe logging, scanners.
- 계약: OpenAPI/JSON Schema fixture matrix, Pydantic fixture consumer, generated TS diff.
- 통합: TestClient middleware/route, frozen package/uv sync, actual uvicorn HTTP smoke.
- E2E: 제품 E2E는 후속 단계. 이 계획에서는 web static shell start/build smoke만 수행한다.
- 보안/PII: synthetic sentinel, raw body log 0, server-only env/browser artifact 0, secret pattern scan.
- 접근성: semantic heading/link, visible focus/base contrast; 390/430과 본 제품 상태는 WEB-HOME/WEB-CHAT에서 확대 검증한다.
- 성능: build/start sanity만. 100-user smoke와 p95는 PERF-001에서 수행한다.

## 버전 변경 계획

- app: `0.0.0-not-scaffolded → 0.1.0`
- web: `0.0.0-not-scaffolded → 0.1.0`
- api: 공개 계약은 `2.0.0-draft` 유지, 구현 패키지는 `0.1.0`
- schema: `0.2.0-draft` 유지, migration 0건
- data: official/mock 모두 not-populated 유지
- prompts: `0.0.2-deepseek-v4-flash-selected` 유지, 호출 0건
- tests: `0.3.0-spec → 0.4.0-scaffold-gates`
- docs: 계획/각 note마다 patch 증가, Phase 1 완료 시 실제 값 기록

## 위험과 롤백

- 위험: 최신 stable dependency 간 Windows/Node24/Python3.12 호환성, Corepack/uv user install 경로, Docker config 권한 경고, 계약 조건부 schema generator 차이.
- 조기 신호: clean install 실패, peer warning, Next build/TS failure, uv lock Python mismatch, fixture가 양 계약에서 다르게 판정, client bundle deny marker 검출.
- 롤백:
  - task commit 단위로 `git revert <sha>`하며 history를 삭제하지 않는다.
  - user-level pnpm/uv/Python cache/tool은 앱 rollback과 분리하고 exact 설치 경로를 note에 기록한다.
  - readiness 200을 임시로 강제하지 않는다. DB 단계가 실패하면 503을 유지한다.
  - contract 생성물이 문제면 생성물과 원본 contract를 같은 commit으로 revert한다.

## 인간이 승인해야 하는 사항

- 이미 승인됨: 위 초기 production dependency, local Git/도구 설치, local/private 구현.
- 여전히 별도 승인 필요: 새 production dependency, 공개/실사용 DeepSeek, 공개 배포·CORS·도메인, 원격 Git/CI, DB migration/삭제, 실제 공식 데이터 ACTIVE 승인.
- 이번 계획에서 추가 질문이 필요한 A/Blocker는 없다.

## 진행 기록

- 2026-07-15: 사용자 `진행` 승인, 기준선 commit `5682804`, 격리 branch/worktree 생성.
- 2026-07-15: read-only Phase 1 감사에서 pre-DB readiness, contract drift, env 경계, exact pin 필요를 확인.
- 2026-07-15: npm/PyPI 공식 registry latest/peer metadata 확인 후 상세 계획 작성.

## 결과와 회고

- 실제 결과: 진행 중.
- 계획과 달라진 점: 완료 시 기록.
- 다음 단계: Task 1 DEV-001A exact runtime/root workspace를 TDD로 구현한다.
