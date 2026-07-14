# Initial Discovery Report

- Date/Time: 2026-07-14 01:26~02:15 KST
- Agent: Codex `/root` (read-only audit subagents: runtime/code, security/data, operations/docs)
- Workspace: `C:\Users\ss020\바탕 화면\sejong_ai\sejong_ai_codex_ready_project`
- Branch/commit: 이 폴더는 유효한 Git 저장소가 아니므로 정의할 수 없음
- Task: `DISC-001`
- Scope: 제품 코드 변경 없이 저장소 발견 감사, 첫 인터뷰 질문, 발견 보고서와 구현 노트 작성

## 0. 읽은 권위 문서와 활성 지침

다음 순서와 범위를 실제 파일에서 확인했다.

1. 루트 및 하위 지침
   - `AGENTS.md`
   - `apps/web/AGENTS.md`
   - `apps/api/AGENTS.md`
   - `data/AGENTS.md`
   - `contracts/AGENTS.md`
2. 권위 순서 핵심
   - `docs/00_SOURCE_OF_TRUTH.md`
   - `docs/source-of-truth/TEAM_DECISIONS.md`
   - `docs/source-of-truth/PROJECT_PLAN.md`
   - `docs/source-of-truth/RFP_MATRIX.md`
3. 나머지 source-of-truth 전체
   - `RFP.md`, `BID_PROPOSAL.md`, `PRIVACY_POLICY.md`, `APPROVAL_POLICY.md`, `KB_GUIDE.md`, `REGRESSION_TEST.md`
   - `assets/`의 와이어프레임·로드맵 이미지와 아키텍처·대표 흐름 DOT 원본
4. ADR 전체
   - `docs/adr/0001`~`0006`, README와 템플릿
5. 활성 계약·DB 초안 전체
   - `contracts/openapi-v1.yaml`
   - JSON Schema 3개
   - `database/schema-v1.draft.sql`, `database/README.md`
6. 현재 감사·운영 문서
   - `docs/01_PROJECT_CONTEXT.md`~`docs/24_UI_STATE_MATRIX.md`
   - `docs/decisions/DECISION_LOG.md`, `PLANS.md`, `TASKS.md`
   - 구현 노트·발견·계획·인수인계 템플릿과 INDEX
   - `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `.env.example`, `.gitignore`, `CHANGELOG.md`, `CODEX_FILE_INDEX.md`, `FIRST_RUN_CHECKLIST.md`, `OVERLAY_INSTALL.md`
   - `scripts/`의 저장소 관리 스크립트 4개와 README
7. 실제 코드·데이터·legacy
   - 활성 `apps/`, `packages/`, `data/` 전체
   - `legacy/`의 상태 문서, FastAPI mock, 오래된 OpenAPI/SQL/requirements, CSV 6개, 정적 HTML 프로토타입

적용한 작업 스킬은 `using-superpowers`, `ambiguity-audit`, `implementation-note`, `dispatching-parallel-agents`이며, 구현 노트 생성 실패 진단에는 `systematic-debugging`을 적용했다. 제품 코드를 만드는 스킬이나 구현 절차는 사용하지 않았다.

## 1. Executive summary

현재 저장소는 **제품 구현 저장소가 아니라, 최종 기준과 legacy를 정리한 Codex-ready 준비 패키지**다. 문서·계약 초안·DB 논리 초안은 상당히 정리되어 있으나 실행 가능한 활성 Web/API 코드는 0개다. 따라서 지금 상태에서 빌드·앱 테스트·배포를 수행할 수 없다.

가장 중요한 결론은 다음과 같다.

1. **Git 경계가 잘못되어 있다.** 작업 폴더에는 유효한 `.git`이 없고, Git은 상위 사용자 홈의 커밋 없는 `master` 저장소를 찾는다. 이 프로젝트의 branch, dirty state, recent commit, 안전한 diff/rollback을 정의할 수 없다.
2. **활성 앱은 스캐폴딩 전이다.** `apps/web`와 `apps/api`에는 README/AGENTS만 있으며 package manifest, 소스, 테스트, 실행 명령이 없다.
3. **공식 답변 데이터는 아직 없다.** 20행 출처대장은 있지만 작성자·검수자가 모두 비어 있고 ACTIVE KB 0건, 공식 기관 0건, 지역 매핑 0건이다.
4. **관리자 보안 경계가 미정이다.** OpenAPI에 인증 scheme이 없고 일부 쓰기 API는 위조 가능한 `X-Demo-*` 헤더만 신뢰한다. DB 초안에도 RLS/GRANT 정책이 없다.
5. **30일 보관 정책과 DB FK가 충돌한다.** 후보가 생성되면 `kb_candidates.failed_question_id`의 NOT NULL FK 때문에 연결된 실패 질문 행을 그대로 삭제할 수 없다.
6. **권위 정책과 계약 초안 사이에 정합성 결함이 있다.** 출처 없는 SUCCESS, 잘못된 후보 적격성, OUT_OF_SCOPE 실패 행, 기관 공식성, ACTIVE 승인 불변조건이 계약/DB 모든 층에서 동일하게 강제되지 않는다.
7. **legacy 격리는 대체로 성공했다.** 오래된 FastAPI/CSV/HTML은 `legacy/`에만 있으며 활성 앱 참조는 없다. 다만 범위 드리프트 검사기가 `PACKAGE_MANIFEST.json`에 기록된 legacy 파일명을 실제 활성 드리프트로 오탐한다.
8. **고신뢰 비밀값이나 실제 개인정보 증거는 발견하지 못했다.** `.env.example`만 있고 키 값은 비어 있다. 활성 PII 형태 문자열은 정책 예시와 의도된 합성 평가 데이터뿐이다. 이는 제한된 정적 검사 결과이며 완전 무결성 보증은 아니다.

결론적으로 `DISC-001` 문서 감사는 완료할 수 있지만, **제품 구현은 Git·개발환경·공식 데이터·배포·관리자 보호·보관 종료 방식에 대한 인간 결정 전까지 시작하면 안 된다.**

## 2. Repository inventory

| Area | Active/Legacy/Missing | Evidence | Risk |
|---|---|---|---|
| 루트 지침·문서 | Active | 권위 문서, ADR, 운영 기준, 템플릿 존재 | 문서가 실제 구현보다 앞서 있음 |
| `apps/web` | Missing implementation | README/AGENTS 2개, 구현 파일 0개 | `/`, `/chat`, `/admin` 없음 |
| `apps/api` | Missing implementation | README/AGENTS 2개, 구현 파일 0개 | health/chat/admin API 없음 |
| `packages/shared-contracts` | Placeholder | README만 존재 | FE/BE 공유 타입 없음 |
| `contracts/` | Active draft | OpenAPI 0.1.0-draft + JSON Schema 3개 | 상호 드리프트와 조건부 불변조건 누락 |
| `database/` | Active logical draft | SQL 1개, 실행 금지 안내 | migration/rollback/RLS/retention job 없음 |
| `data/official` | Staging registry | 출처대장 20행 | ACTIVE KB·기관 데이터로 오인 위험 |
| `data/evaluation` | Active spec data | 표본 20행, SUCCESS/FOLLOWUP/FALLBACK=10/2/8 | enum/기계 판정 필드 일부 불일치 |
| `data/mock` | Empty | README만 존재 | 관리자 데모 데이터 미준비 |
| 테스트 | Missing | 앱 테스트 파일·runner config 0개 | 품질·보안·접근성·성능 미검증 |
| CI | Missing | workflow/CODEOWNERS/PR template 0개 | 계약·비밀·테스트 gate 없음 |
| 배포 | Missing | Vercel/Render/Supabase config 0개 | 계정·리전·CORS·로그·비용 미정 |
| Git | Invalid boundary | workspace Git metadata 없음; 상위 홈 repo가 탐지됨 | diff/rollback/최근 커밋 증거 없음 |
| `legacy/` | Legacy, quarantined | 36개 파일: FastAPI mock 1, HTML 2, CSV 6, SQL 1, 문서 등 | 복사 시 10개 분야/P2/가짜 데이터 재도입 위험 |

초기 패키지 파일은 `PACKAGE_MANIFEST.json`이 나열한 144개이며, 문서 작성 전 SHA-256 재검증에서 missing 0, mismatch 0이었다. `PACKAGE_MANIFEST.json` 자체는 의도적으로 목록에서 제외된다. 이 보고서와 구현 노트는 승인된 후속 문서 산출물이므로 그 초기 패키지 스냅샷에는 포함되지 않는다.

## 3. Source-of-truth vs implementation gaps

| Requirement/decision | Expected | Actual | Severity | Recommended action |
|---|---|---|---|---|
| 실제 페이지 | `/`, `/chat`, `/admin` | 활성 UI 코드 0 | A/Blocker | Git·도구 결정 후 스캐폴딩 계획 승인 |
| Web stack | Next.js + TypeScript + Tailwind | package.json/lockfile/소스 없음 | A/Blocker | 런타임·패키지 관리자 확정 |
| API stack | FastAPI + Python | 활성 pyproject/requirements/소스 없음 | A/Blocker | Python 기준과 환경 도구 확정 |
| 공식 KB 20건 | 사람 작성·별도 승인·ACTIVE | 출처대장 20행만 존재; 작성자/검수자 20/20 공란 | A/Blocker | 담당자·승인자·완료일 확정 후 seed 작성 |
| 공식 기관 3건 | 아름동·도담동·조치원읍 공식 카드 | 레코드 0, 매핑 0 | A/Blocker | 공식 출처 검수·승인 흐름 정의 |
| ACTIVE 전용 검색 | DRAFT/PENDING 제외 | 정책·SQL index 초안만, 검색 코드 없음 | B/High | 계약/DB/통합 테스트로 강제 |
| SUCCESS 근거 | source 1개 이상, 서버 결합 | OpenAPI/JSON Schema는 빈 sources 허용 | B/High | 상태별 조건부 schema와 DB check 추가 |
| 네 가지 폴백/FOLLOWUP | enum과 저장 정책 고정 | 평가/계약 초안만, 구현 없음 | B/High | 계약 정합화 후 정책 단위 테스트 |
| OUT_OF_SCOPE | event만 저장, 텍스트/실패 목록 없음 | SQL은 텍스트 NULL인 failed row 허용, API는 masked text 필수 | B/High | 권위 정책대로 DB/API를 일치시킴 |
| PII 마스킹 | 외부 LLM 호출 전, 원문 미저장 | 활성 코드 없음; legacy regex는 범위 부족 | A/Blocker | 공통 redaction 경계와 payload spy test 계획 |
| 30일 보관 | 만료 삭제와 테스트 | expires_at만 있고 job/default/check 없음; 후보 FK가 삭제 차단 | A/Blocker | Q-PRIV-001 결정 후 schema/job 설계 |
| 관리자 역할 분리 | 운영자/승인자, 자기 승인 차단 | SQL check 초안만; 인증·RLS·transaction 없음 | A/Blocker | Q-SEC-001 결정 후 API/DB 보안 설계 |
| 기관 공식성 | 공식 데이터만 시민 노출 | `offices.is_official DEFAULT true`, 승인/provenance 필드 부족 | B/High | 기본값 제거, 출처·작성·승인 명시 |
| KPI 출처 | EVENT/EVALUATION/MOCK 라벨 | DB는 `is_test` boolean, quality 응답 schema 없음 | B/High | source_kind enum과 계약/화면 배지 강제 |
| LLM adapter | 공급자 독립 + disabled/template fallback | ADR/문서만, provider 없음 | A/Blocker | Q-LLM-001 결정 |
| 검색 | keyword/metadata 기본, embedding 보조 | 코드·인덱스·threshold 없음 | B/High | embedding off 기본, 근거 기준 테스트 |
| 오류 모델 | stable code/request_id | OpenAPI 오류 body schema 없음; SYSTEM_ERROR 200/503 미정 | B/High | 후속 인터뷰에서 HTTP 정책 확정 |
| 접근성 | 390/430, 200%, 4.5:1, 키보드 | 와이어프레임만; 자동/수동 결과 없음 | B/High | UI 수직 흐름 때 인수 기준과 도구 고정 |
| 성능 | 평균/p95/오류율, 100명 1분 | 테스트 도구·환경·부하 모델 없음 | B/High | 실행 조건과 합격 기준 문서화 |
| API 경로 | versioned contract | BID 부록은 `/api/chat`, 활성 계약/TASKS는 `/api/v1/chat` | C/Defaultable | `/api/v1`을 기준으로 참조 문서 동기화 |
| 회귀 흐름 | REG-01 승인 전후 완주 | 문서 시나리오만 존재 | B/High | 관리자 수직 흐름 후 상태 변화 E2E |

### 이미 인간이 결정했으므로 다시 묻지 않을 항목

- 페이지 3개와 지원 분야 4개
- 공식 KB 20건·표본 20개·회귀 1개
- 실제 GPS/지도/상태조회/다국어/고급 분석의 P2 제외
- ACTIVE KB만 검색
- 작성자 자기 승인 금지
- 원문 질문 DB·로그 미저장
- OUT_OF_SCOPE 텍스트 미저장·후보 불가
- FOLLOWUP은 실패 질문이 아님
- 출처 메타데이터는 서버가 KB에서 결합
- provider adapter, keyword/metadata 우선, embedding 보조 기본 방향
- Vercel+Render+Supabase는 확정 배포가 아니라 권장안

## 4. Runtime and tooling

- OS/shell: Windows, PowerShell 5.1
- Git: 2.44.0.windows.1
- Node: v24.12.0
- npm: 11.6.2 (`npm.ps1`은 실행정책으로 차단되며 `npm.cmd`는 동작)
- Python:
  - 기본 `python`: 3.14.0
  - `py -3.11`: 3.11.2
  - Anaconda Python: 3.13.5
- pnpm/yarn/uv/psql/Supabase CLI: 없음
- Docker CLI: 29.2.1, Compose v5.0.2; daemon·프로젝트 설정은 확인하지 못함
- DB tooling: migration 파일·Alembic·Supabase CLI·실행 Postgres 없음
- Existing build/test/lint/typecheck/dev commands: 없음
- Repository utility commands: package validator, scope drift checker, state capture, implementation-note generator

### Git 상세

감사 시작 시 workspace에 `.git`이 없었다. 샌드박스 밖 읽기 전용 `git status --short --branch`는 상위 `C:\Users\ss020`의 커밋 없는 `master` 저장소를 탐지했고, 이 프로젝트 전체를 그 상위 저장소의 untracked 하위 폴더로 취급했다. 사용자 홈의 다른 untracked 경로는 개인정보 최소화 차원에서 이 보고서에 복사하지 않는다.

감사 중 `.git` 읽기 전용 mount 지점으로 보이는 빈 디렉터리가 workspace에 나타났으나 내부 파일은 0개이고 `HEAD`/`config`도 없다. 어떤 감사 에이전트도 `git init`, `mkdir`, `New-Item`, worktree/clone 명령을 실행하지 않았다. 원인이 확정되지 않아 삭제하거나 초기화하지 않았다. 따라서 여전히 유효한 Git 저장소가 아니다.

### 실제로 존재하는 명령 검증

| 명령/검증 | 실제 결과 |
|---|---|
| `python scripts/validate_codex_package.py` | 통과: 필수 파일 12개, version manifest 유효 |
| `python scripts/check_scope_drift.py` | exit 1: `PACKAGE_MANIFEST.json`이 나열한 legacy 100문항 파일 경로 1건을 활성 드리프트로 오탐; 활성 구현 드리프트는 0 |
| 활성 JSON `ConvertFrom-Json` | 5/5 파싱 성공 |
| 활성 CSV `Import-Csv` | 출처대장 20행, 평가 20행 파싱 성공 |
| package manifest SHA-256 재계산 | 144개, missing 0, mismatch 0 (문서 변경 전) |
| 고신뢰 secret/private-key 파일명·패턴 검색 | 발견 0 |
| 활성 package/lock/test/CI/deploy config 검색 | 모두 0 |
| PyYAML/OpenAPI 의미 검증 | 미실행: PyYAML 미설치, 새 의존성 설치 승인 없음 |
| SQL 실행 검증 | 미실행: psql/DB/migration 환경 없음 |
| app build/test/lint/typecheck/E2E | 미실행: 활성 앱과 명령 없음 |

`scripts/capture_repo_state.py`는 Git root가 workspace와 같은지 검증하지 않고 Git 오류도 문자열로 출력해 종료 성공으로 오인될 수 있어 실행 증거 도구로 신뢰할 수 없다.

`scripts/new_implementation_note.py`는 기본 Python 3.14/설치된 3.11에서 `tzdata`가 없어 `ZoneInfo("Asia/Seoul")` 단계에서 재현 가능하게 실패했다. 기존 Anaconda Python 3.13에는 `tzdata`가 있어 스크립트 수정·의존성 설치 없이 동일 생성 명령을 성공시켰다. 표준 개발환경 결정 후 스크립트의 Windows 호환성을 별도로 보완해야 한다.

## 5. Security and data findings

### 5.1 비밀값·개인정보

- 실제 `.env`, 개인키, 인증서, 로그, sqlite 파일은 활성 트리에 없다.
- `.env.example`의 Supabase/LLM 키 값은 비어 있고 DB URL은 localhost 예시다.
- 고신뢰 OpenAI/AWS/GitHub/개인키 패턴 검색 결과는 0개 파일이다.
- 활성 개인정보 형태 문자열은 정책 문서의 가상 예시와 평가셋의 합성 접수번호뿐이며 실제 개인 데이터라는 증거는 없다.
- `.gitignore`에는 `.pfx`, `.jks`, `.keystore`, `.npmrc`, `.pypirc`, 서비스계정 JSON 같은 흔한 비밀 파일 패턴이 빠져 있다. Git 초기화 후 보강할 수 있는 C/Defaultable 항목이다.

### 5.2 관리자 인증·인가

- OpenAPI에 `security`와 `securitySchemes`가 없다.
- 실패 질문 목록·상세·사유 수정·후보 목록·품질 조회는 actor 매개변수조차 없다.
- 후보 쓰기는 클라이언트가 임의 지정할 수 있는 `X-Demo-Actor-Id`, `X-Demo-Role` 헤더를 사용한다.
- DB 초안에는 RLS, policy, GRANT/REVOKE가 없다.
- `/admin`을 공개 배포하면 현재 초안만으로는 마스킹 질문과 승인 기능을 보호할 수 없다.

### 5.3 보관·삭제

- `failed_questions.expires_at`은 필수지만 30일 default/check가 없다.
- 만료 삭제 함수·job·실패 경보·백업 파기 규칙이 없다.
- 후보가 생긴 경우 NOT NULL FK 때문에 실패 질문 행 hard delete가 막힌다.
- 정책이 요구하는 것은 적어도 `masked_question`의 30일 후 파기이며, 행/메타데이터/후보 링크를 어떻게 처리할지 Q-PRIV-001로 결정해야 한다.

### 5.4 공식 데이터 품질

- 출처대장은 정확히 4분야×5건이고 URL·확인일 공란은 0이다.
- 작성자와 검수자는 각각 20/20 공란이다.
- 상태는 `작성 예정` 19건, `회귀 테스트 후 승인 예정` 1건이다.
- 실제 ACTIVE KB, 기관, 지역×민원 매핑은 0건이다.
- `offices.is_official DEFAULT true`는 미검수 레코드가 공식으로 승격될 위험이 있다.
- 2026-07-14의 제한적 URL spot check에서 일부 정부24 링크는 유지보수 화면으로 이동해 본문 검증이 불가능했고, 대형폐기물 `siteId=null` URL은 정규 URL 재확인이 필요했다. [공식 품목 페이지](https://www.sjwaste.kr/wasteApp/appCategoryPopup.do?menuId=MENU00305)의 침대/매트리스 금액은 대장과 일치했으나, `KB-TAX-02`의 [위택스 로그인 페이지](https://www.wetax.go.kr/login.do)는 자동차세 세부 내용의 직접 근거로 부족하다. 이 spot check는 사람의 20건 전수 검수를 대체하지 않는다.

### 5.5 비협상 정책을 환경변수로 우회할 위험

`.env.example`에는 `STORE_SUCCESS_TEXT`와 `STORE_OUT_OF_SCOPE_TEXT`가 feature/config처럼 존재한다. 기본값은 안전하지만 이 두 금지사항은 인간 승인 없는 운영 설정으로 켤 수 없어야 한다. 구현 시 정책 위반 값이면 시작을 거부하거나 비프로덕션 테스트 전용으로 제한해야 한다.

## 6. Contract and model consistency findings

다음은 인간이 이미 정한 안전 원칙을 초안이 완전히 표현하지 못한 결함이다. 방향을 다시 질문하지 않고, 승인된 실행계획에서 정합화해야 한다.

1. `SUCCESS ⇒ sources.length >= 1`이 OpenAPI/JSON Schema/DB에 조건부로 강제되지 않는다.
2. `FALLBACK ⇒ fallback object 필수`, `FOLLOWUP ⇒ fallback_reason 없음`도 schema 조건이 없다.
3. `candidate_eligible=true`를 INSUFFICIENT_GROUNDING에만 제한하는 조건이 chat response에는 없다.
4. `KBCandidateCreate.category`가 전체 Intent를 재사용해 OUT_OF_SCOPE/UNKNOWN도 허용하지만 DB는 거부한다.
5. 정책은 OUT_OF_SCOPE를 event-only로 정했지만 SQL은 텍스트 NULL인 failed row를 허용하고 OpenAPI는 masked text를 필수로 요구한다.
6. OpenAPI fallback에는 `office`가 있으나 별도 `chat-response.schema.json`은 `additionalProperties:false`로 이를 거부한다.
7. Office의 `source_url`은 DB에서는 NOT NULL이나 OpenAPI required에서 빠져 있다.
8. `KBRecord.status=ACTIVE`인데 승인자/승인시각이 없는 객체도 JSON Schema를 통과한다.
9. InteractionEvent JSON Schema의 intent/fallback/region이 DB/OpenAPI enum보다 느슨하다.
10. 실패 질문 목록에는 P1이 요구한 민원 유형 필터가 없다.
11. admin list/review/quality 주요 응답 schema와 공통 오류 body가 없다.
12. `session_id`는 목적·생성 주체·보관·로그 금지·TTL 정책 없이 ChatRequest에 들어 있다.
13. KPI 출처는 EVENT/EVALUATION/MOCK 3종이어야 하나 DB는 `is_test` boolean만 갖는다.
14. source-of-truth BID 부록의 `/api/chat`과 활성 계약/TASKS의 `/api/v1/chat`이 다르다. versioned 경로를 기준으로 동기화하는 것이 기본값이다.

## 7. Unknowns classification

| Q-ID | A/B/C/D | Decision | Why it matters | Default |
|---|---|---|---|---|
| Q-REPO-001 | A | 독립 Git root/기존 원격/브랜치 정책 | diff, rollback, CI, 최근 커밋 증거 | 구현 중지, 기존 원격 확인 |
| Q-DEV-001 | A | Node/Python/package manager 기준 | 설치·lockfile·CI·재현성 | 문서 권장안을 plan에만 기록 |
| Q-DATA-001 | A | 공식 KB/기관 작성·승인 책임과 마감 | 시민 답변 가능 여부 | 미승인 데이터는 근거 사용 금지 |
| Q-LLM-001 | A | 공급자 지금 선택 vs disabled/template | 보관·비용·품질·장애 경로 | disabled/template |
| Q-DEP-001 | A | 로컬/데모 배포, 계정·리전·예산·로그 | CORS·비밀·비용·데이터 위치 | local-first |
| Q-SEC-001 | A | `/admin`과 admin API 보호 수준 | 실패 질문·승인 무단 접근 | local/private only |
| Q-PRIV-001 | A | 30일 후 텍스트/행/FK 처리 | 개인정보 파기·감사·migration | 텍스트 파기+최소 메타 유지 |
| Q-PRIV-002 | B | 한국어 이름·상세주소 탐지와 오탐 | 마스킹 누락/질문 맥락 | 보수적 탐지+테스트 |
| Q-CHAT-001 | B | 완전 무상태 vs 익명 단기 session | 최소수집·후속 대화·API | 무상태 |
| Q-ERR-001 | B | SYSTEM_ERROR HTTP 200 vs 503 | FE/모니터링/재시도 계약 | 기술 장애는 503, 사용자 body 구조화 |
| Q-SEARCH-001 | B | embedding feature flag 활성화 | 비용·DB 확장·재현성 | off |
| Q-CI-001 | B | GitHub/GitLab/필수 검사 | merge gate·비밀 스캔 | GitHub Actions 제안만 유지 |
| Q-DEMO-001 | B | 배포·로컬·녹화 3중 백업과 발표망 | 데모 안정성 | 3중 백업 |
| Q-BACKUP-001 | B | DB backup 주기·RPO/RTO·복원 시험 | 데이터 손실·인수인계 | seed 재현+일일 demo backup 제안 |
| C-CONTRACT-001 | C | 위 14개 계약 정합화 방식 | 이미 결정된 정책의 기계적 강제 | 단일 OpenAPI/Schema 기준 |
| C-DATA-001 | C | 평가 CSV enum/expected source 정규화 | 자동 판정 가능성 | 계약 enum 사용 |
| C-TOOL-001 | C | drift checker/tzdata/state capture 호환성 | 자동화 신뢰도 | 표준 환경에서 수정·테스트 |
| C-VERSION-001 | C | 루트 `VERSION=0.0.0` 의미 | 릴리스 혼동 | application 축으로 문서화 |
| D-STRUCTURE-001 | D | 내부 모듈·fixture·generated type 배치 | 공개 동작 없음 | framework convention |

이번 첫 인터뷰는 영향도가 가장 큰 A 7개만 묻는다. B 항목은 답변에 따라 사라지지 않으면 다음 배치에서 최대 7개로 묻는다.

## 8. Interview batch 1

### Q-REPO-001. 이 폴더를 어떤 Git 저장소로 확정할까요?

- 왜 지금 필요한가: 현재 폴더는 독립 Git 저장소가 아니며 상위 사용자 홈의 커밋 없는 저장소가 잘못 탐지됩니다. 이 상태에서는 안전한 diff·branch·rollback·CI·최근 커밋 증거가 없습니다.
- 선택지 A / 장점 / 단점: **이 폴더에서 새 독립 저장소를 시작**하고 `main`을 기본 브랜치로 사용합니다. 즉시 격리되고 이후 변경을 정확히 추적할 수 있지만, 원래 원격 이력은 복구되지 않습니다.
- 선택지 B / 장점 / 단점: **원래 Git 원격 또는 올바른 clone 경로를 제공**하고 그 저장소에서 계속합니다. 기존 이력·브랜치·리뷰 정책을 보존하지만 원본 확인 전 구현이 지연됩니다.
- 당신의 추천안: 원본 원격이나 이력이 있으면 B, 없다면 A. 새로 시작할 경우 Codex 작업 브랜치는 `codex/<task-id>-<slug>`로 통일하고 프로젝트 문서의 `feature/` 예시를 동기화합니다.
- 답을 받지 못할 때 사용할 기본값: Git 초기화·삭제를 하지 않고 제품 구현을 보류합니다.
- 영향을 받는 파일·계약·데이터·배포: `.git`, CONTRIBUTING, CI, branch protection, 구현 노트의 branch/commit, diff/rollback, 배포 연결.

### Q-DEV-001. 개발 런타임과 패키지 관리 기준을 어느 조합으로 고정할까요?

- 왜 지금 필요한가: 실제 환경은 Node 24.12/npm 11.6, Python 3.14·3.11이고 pnpm/uv가 없습니다. 문서는 Node LTS+pnpm, Python 3.12+uv를 권장하므로 스캐폴딩·lockfile·CI 전에 하나로 고정해야 합니다.
- 선택지 A / 장점 / 단점: **문서 권장 기준으로 통일** — 승인 시 Node major를 고정하고 pnpm, Python 3.12, uv를 설치합니다. 재현성과 문서 일치성이 높지만 초기 설치가 필요합니다.
- 선택지 B / 장점 / 단점: **현재 설치 도구를 최대 활용** — Node 24+`npm.cmd`, Python 3.11+venv/pip를 사용합니다. 시작은 빠르지만 기존 문서와 달라지고 PowerShell npm 실행정책 우회가 필요합니다.
- 당신의 추천안: A. `pyproject.toml`·lockfile·CI에 exact range를 기록하고 전원이 같은 기준을 사용합니다.
- 답을 받지 못할 때 사용할 기본값: 새 도구를 설치하지 않고 A를 실행계획의 제안값으로만 기록합니다.
- 영향을 받는 파일·계약·데이터·배포: package manifests/lockfiles, Docker, Alembic 또는 migration tool, CI, README, 개발 명령, 모든 앱 코드.

### Q-DATA-001. 공식 KB 20건과 기관 3건의 작성자·승인자·완료일을 어떻게 정할까요?

- 왜 지금 필요한가: 현재 출처대장은 20행이지만 작성자·검수자 20건 모두 공란이고 실제 ACTIVE KB와 기관 데이터가 0건입니다. 공식 데이터가 없으면 정상 답변 P0를 구현·검증할 수 없습니다.
- 선택지 A / 장점 / 단점: **팀 역할로 분담해 사람 전수 작성·별도 승인** — 예: AI/Data·Backend 작성, PM/지정 승인자 검수, 완료일 확정. P0를 충족하지만 실제 사람 시간이 필요합니다.
- 선택지 B / 장점 / 단점: **이번 단계는 구조와 mock 데모만 유지**하고 공식 답변 기능을 미완료로 표시합니다. 빠르지만 핵심 제품 원칙과 P0 인수 기준을 충족하지 못합니다.
- 당신의 추천안: A. 각 행에 작성자·승인자·확인일·상태를 채우고 기관 데이터도 같은 승인 gate를 사용합니다.
- 답을 받지 못할 때 사용할 기본값: 모든 현행 행을 미승인 staging으로 유지하고 시민 답변 근거로 사용하지 않습니다.
- 영향을 받는 파일·계약·데이터·배포: `data/official`, source registry, DB seed, data lineage/version, ACTIVE search, 표본/회귀 테스트, 시민 출처 카드.

### Q-LLM-001. 첫 구현부터 실제 외부 LLM을 선택할까요, 안전한 비활성 공급자로 시작할까요?

- 왜 지금 필요한가: 공급자·모델·입력 보관·학습 미사용·ZDR·예산·쿼터가 미정입니다. 실제 공급자를 바로 넣으면 개인정보·비용·장애 경계가 달라집니다.
- 선택지 A / 장점 / 단점: **초기에는 disabled/template provider**로 구현하고 실제 외부 호출을 하지 않습니다. 구조·검색·폴백·출처·승인 흐름을 안전하게 완성할 수 있지만 모델 품질·실제 latency는 아직 측정하지 못합니다.
- 선택지 B / 장점 / 단점: **지금 실제 provider/model을 선택**하고 월 예산·키 소유자·보관정책·쿼터를 함께 승인합니다. 실제 품질 평가가 가능하지만 비용과 데이터 처리 검토가 선행됩니다.
- 당신의 추천안: A. 시민 수직 흐름과 개인정보 테스트를 먼저 고정한 뒤 별도 결정으로 B를 도입합니다.
- 답을 받지 못할 때 사용할 기본값: `LLM_PROVIDER=disabled`, 외부 전송 0건.
- 영향을 받는 파일·계약·데이터·배포: provider adapter, env, prompt version, evaluation, observability, timeout/retry, 비용, 개인정보 문서.

### Q-DEP-001. 이번 프로젝트의 실제 실행·배포 목표와 계정 책임을 어디까지 둘까요?

- 왜 지금 필요한가: Vercel+Render+Supabase는 권장안일 뿐 실제 계정·소유자·리전·플랜·예산·도메인·인프라 로그 보관·CORS가 없습니다.
- 선택지 A / 장점 / 단점: **local-first + 승인 후 단일 demo/staging**. 로컬 재현을 먼저 끝내고 계정·리전·로그·예산을 확인한 뒤 배포합니다. 안전하고 롤백하기 쉽지만 공개 URL이 늦어집니다.
- 선택지 B / 장점 / 단점: **처음부터 제공된 관리형 계정에 공개 demo 배포**. 팀 공유와 발표 접근은 빠르지만 admin 보호·비밀·cold start·비용·데이터 위치 위험을 즉시 해결해야 합니다.
- 당신의 추천안: A. 계정 소유자, 허용 월 예산, 데이터 리전, 자동 로그 보관기간, CORS origin을 배포 승인 체크리스트로 둡니다.
- 답을 받지 못할 때 사용할 기본값: 로컬 전용, 외부 DB/LLM/배포 연결 금지.
- 영향을 받는 파일·계약·데이터·배포: env, CORS, secrets, health/readiness, deployment config, DB migration/backup, domain, 비용/쿼터.

### Q-SEC-001. `/admin`과 `/api/v1/admin/*`를 어떤 방식으로 보호할까요?

- 왜 지금 필요한가: 현재 OpenAPI에는 인증 scheme이 없고 데모 역할 헤더는 클라이언트가 위조할 수 있습니다. 공개 상태에서는 마스킹 질문·후보·승인 기능이 무단 노출됩니다.
- 선택지 A / 장점 / 단점: **공개 demo 전에 서버측 gate를 추가**합니다. 플랫폼 접근제어 또는 최소 로그인/세션 뒤에서만 데모 역할 전환을 허용하고, DB는 backend-only/RLS deny-by-default로 둡니다. 원격 시연이 가능하지만 인증·세션 구현과 테스트가 추가됩니다.
- 선택지 B / 장점 / 단점: **admin은 local/private 환경에서만 실행**하고 데모 헤더는 loopback/test에서만 허용합니다. 가장 단순하고 안전하지만 공개 원격 admin 시연은 할 수 없습니다.
- 당신의 추천안: 초기 구현은 B, 공개 demo가 필요하다고 확정되면 A를 배포 전 필수 gate로 적용합니다. SSO/RBAC는 P2로 유지합니다.
- 답을 받지 못할 때 사용할 기본값: B. 공개 배포에서 admin API 비활성.
- 영향을 받는 파일·계약·데이터·배포: OpenAPI security, actor 전달, cookies/session, CORS/CSRF, Supabase RLS/roles, audit log, E2E, demo 운영.

### Q-PRIV-001. 30일이 지난 실패 질문이 KB 후보와 연결되어 있을 때 무엇을 파기할까요?

- 왜 지금 필요한가: 정책은 masked question 30일 보관을 요구하지만 후보 FK가 실패 질문 행 삭제를 막습니다. 처리 방식을 정하지 않으면 retention job이나 migration을 확정할 수 없습니다.
- 선택지 A / 장점 / 단점: **만료 시 `masked_question`을 NULL로 파기하고 비텍스트 메타데이터·후보 링크는 유지**합니다. 감사·회귀 연결을 보존하면서 텍스트를 지울 수 있지만 행 자체는 남습니다. 후보의 대표 질문은 사람이 별도로 정제하고 PII 검사를 통과해야 합니다.
- 선택지 B / 장점 / 단점: **후보 링크를 분리한 뒤 failed question 행을 hard delete**합니다. 데이터 최소화는 강하지만 참조·감사·복구 설계와 migration이 복잡해집니다.
- 당신의 추천안: A. 정책 문구를 “마스킹 텍스트 30일 후 파기”로 명확히 하고 만료·백업·관리자 빈 상태를 테스트합니다.
- 답을 받지 못할 때 사용할 기본값: A를 설계 제안으로만 기록하고 실제 migration/job은 만들지 않습니다.
- 영향을 받는 파일·계약·데이터·배포: privacy policy, OpenAPI FailedQuestion, DB nullability/FK/check, retention job, backups, admin UI, audit/회귀 테스트.

### 답변 예시

```text
Q-REPO-001: A — 원본 원격 저장소 없음
Q-DEV-001: A
Q-DATA-001: A — 작성 AI/Data·Backend, 승인 PM, 완료 목표 2026-07-20
Q-LLM-001: A
Q-DEP-001: A — 계정 소유자는 PM, 초기 예산 0원, 공개 URL은 추후 승인
Q-SEC-001: B
Q-PRIV-001: A
```

비밀키·비밀번호·실제 접속 문자열은 답변에 적지 않는다.

## 9. Safe actions that can proceed without answers

이번 요청 범위에서는 다음만 안전하게 완료했다.

- 발견 보고서와 구현 노트 작성
- source-of-truth/실제 파일/legacy 차이 기록
- 계약·DB 정합성 결함 목록화
- A/B/C/D 분류와 첫 A 질문 7개 작성
- 기존 파일 형식·패키지 hash·비밀 패턴의 읽기 전용 검증

향후 승인된 계획에서는 다음 C/D 작업을 인간의 추가 설계 질문 없이 포함할 수 있다.

- 이미 확정된 안전 불변조건을 OpenAPI/JSON Schema/DB에 동일하게 표현
- scope drift false positive와 note generator Windows 호환성 수정
- 평가 enum 정규화·기계 판정 필드 추가
- 내부 모듈/fixture/generated type 배치

단, 공개 계약·DB migration·새 의존성에 실제 변경을 적용하기 전에는 계획과 영향도를 제시하고 사용자 승인을 받아야 한다.

## 10. Blocked actions

- Git init/remote 연결/브랜치 생성
- Next.js/FastAPI 스캐폴딩과 새 의존성 설치
- DB migration tool 선택·schema 실행·RLS 구성
- 공식 KB/기관 seed를 시민 근거로 활성화
- 실제 LLM 호출
- 공개 `/admin` 배포
- Vercel/Render/Supabase 연결
- retention hard delete/nulling job
- 공개 API·DB 초안 변경
- P0/P1 제품 코드 구현

## 11. Proposed next documents/plan

사용자 답변을 받은 뒤에만 다음을 수행한다.

1. `docs/discovery/INTERVIEW_ANSWERS.md`에 질문 원문과 답변 보존
2. `docs/decisions/DECISION_LOG.md`에 새 행 추가
3. 장기 결정에 필요한 ADR 작성/갱신
4. `docs/11_AMBIGUITY_REGISTER.md` 상태를 Resolved/Deferred로 갱신
5. 필요 시 계약/DB 초안/버전 매니페스트의 계획상 변경점 명시
6. `docs/plans/PLAN-...` 실행계획 작성
7. `TASKS.md`의 DISC/DOC/PLAN 상태와 의존성 갱신
8. A/Blocker가 남으면 다음 인터뷰 배치, 없으면 최종 계획 검토 요청

사용자가 `진행`, `구현 시작` 또는 동등한 명시적 승인을 하기 전에는 제품 코드를 변경하지 않는다.

## 12. Interview batch 1 outcome — 2026-07-14

답변 원문과 해석은 `docs/discovery/INTERVIEW_ANSWERS.md`에 보존했다.

| 질문 | 판정 | 반영 결과 |
|---|---|---|
| Q-REPO-001 | Resolved | 새 독립 repo·`main`; 실제 init은 최종 계획 승인 후 |
| Q-DEV-001 | Resolved | Node 24.x+pnpm, Python 3.12+uv |
| Q-DATA-001 | Resolved | AI/Data·Backend 작성, PM 전수 승인, 2026-07-20 |
| Q-LLM-001 | Partially resolved / A blocker | 실제 LLM 목표는 확정; 공급자·모델·데이터 처리·0원 예산 양립 미정 |
| Q-DEP-001 | Local resolved / public deferred | local-first·외부 인프라 0원; 공개 계정·리전·CORS·로그는 추후 승인 |
| Q-SEC-001 | Resolved | local/private admin, public server gate 없이는 관리자 route off |
| Q-PRIV-001 | Resolved | 30일 후 masked text만 NULL 파기, 메타·후보 FK 유지 |

결정 로그 D-009~D-015, ADR-0002/0004/0005/0007, source-of-truth, OpenAPI/DB draft 0.2.0, `TASKS.md`와 Interviewing 계획을 동기화했다. 제품 코드, Git init, 도구 설치, 외부 API/DB 호출은 수행하지 않았다.

남은 A 블로커는 Q-LLM-002, 호스팅 선택 시 Q-LLM-003, Q-DB-001, Q-PRIV-002, Q-CHAT-001, Q-API-001과 최종 계획 승인이다. Q-CI-001은 B/High다.

Q-LLM-002 선택지 검증을 위한 읽기 전용 하드웨어 조회에서 RAM 15.6GiB와 Intel Arc 표시 메모리 2GiB를 확인했다. 따라서 20B급 local model을 안정적 데모 기본값으로 추천하지 않으며, 0원 local 경로는 4B급 모델의 별도 한국어/구조화 출력/latency benchmark를 조건으로 한다.
