# 세종 민원이음 (플랫폼명: 민원이음) — 최종 MVP

> **모르면 지어내지 않고, 알면 끝까지 안내한다.**

세종 민원이음은 시민의 일상어 질문을 승인된 공식 행정 지식과 연결하는 local/private MVP입니다. 시민에게는 절차·준비 서류·수수료·담당 기관·공식 출처를 구조화해 안내하고, 근거가 부족한 질문은 운영자의 작성과 별도 승인자의 검수를 거쳐 새로운 ACTIVE KB로 전환합니다.

## 1. 해결하려는 문제

시민은 행정 용어를 정확히 알기 어렵고, 여러 사이트에서 최신 공식 정보를 다시 확인해야 합니다. 담당자는 같은 단순 문의를 반복해서 처리하며, 답하지 못한 질문이 어떤 지식 보강으로 이어져야 하는지 체계적으로 확인하기 어렵습니다.

민원이음은 다음 두 화면을 하나의 개선 흐름으로 연결합니다.

```text
시민용 민원이음
  질문 → 개인정보 마스킹 → 분류 → ACTIVE KB 검색
       → 공식 근거가 있으면 구조화 답변·출처·기관 안내
       → 근거가 부족하면 안전한 폴백

관리자용 이음센터
  실패 질문 → 사유 확인 → KB 후보 작성
            → 작성자와 다른 승인자 검수 → ACTIVE 반영
            → 같은 질문 재질의 시 개선된 공식 답변
```

## 2. 구현 범위

- 시민 화면: `/`, `/chat`
- 관리자 화면: `/admin`
- 지원 분야
  - 전입·주민등록
  - 증명서 발급
  - 대형폐기물
  - 지방세 일반 안내
- 응답 상태
  - 공식 근거 기반 `SUCCESS`
  - 필요한 내용을 다시 묻는 `FOLLOWUP`
  - `INSUFFICIENT_GROUNDING`
  - `PERSONAL_LOOKUP`
  - `LEGAL_JUDGMENT`
  - `OUT_OF_SCOPE`
  - `PRIVACY_UNRESOLVED`
- 공식 데이터 기준선
  - ACTIVE KB 19개
  - 공식 기관 3개
  - 지역·민원 매핑 10개
- 승인 흐름
  - `KB-WASTE-03`을 다른 승인자가 검수해 20번째 ACTIVE로 전환
  - 동일 질문 재질의 시 공식 출처가 포함된 `SUCCESS`

## 3. 핵심 설계 원칙

### 공식 근거 우선

시민 답변 검색 대상은 `ACTIVE+OFFICIAL` KB뿐입니다. 출처명·URL·확인일과 기관 정보는 AI가 만들지 않고 서버가 승인된 KB 메타데이터에서 결합합니다.

### 개인정보 최소화

외부 AI 호출 전에 개인정보를 마스킹합니다. 질문 원문과 실제 개인정보는 애플리케이션 DB·URL·브라우저 저장소·일반 로그에 보관하지 않습니다.

`PERSONAL_LOOKUP`, `LEGAL_JUDGMENT`, `OUT_OF_SCOPE`, `PRIVACY_UNRESOLVED`는 KB 후보로 만들지 않으며 질문 text와 실패 질문 행을 저장하지 않습니다.

### 사람의 승인

지원 범위 안에서 공식 근거가 부족한 `INSUFFICIENT_GROUNDING` 질문만 개선 대상으로 연결합니다. KB 후보 작성자와 승인자는 달라야 하며, 승인되지 않은 후보와 mock 데이터는 시민 답변에 사용되지 않습니다.

### 제한된 AI 사용

- 명백한 지원 질문과 개인정보·정책 질문은 서버의 결정론적 경로가 먼저 처리합니다.
- 마스킹을 통과한 안전한 모호 질문은 DeepSeek `deepseek-v4-flash` 분류기를 선택적으로 사용할 수 있습니다.
- 같은 DeepSeek 모델은 ACTIVE KB와 서버 발급 fact ID 안에서 근거 제한형 답변 표현도 선택적으로 보조합니다.
- 기존 Upstage 경로는 rollback 선택지로 보존하지만 기본 설정과 아래 실행 예시는 DeepSeek로 통일합니다.
- 공급자 장애, timeout, JSON·계약 위반, 근거 불일치가 발생하면 공식 KB 기반 TEMPLATE 응답으로 복구합니다.
- 기본 설정은 외부 공급자 비활성화이며 API key는 저장소에 포함하지 않습니다.

## 4. 기술 구성

| 영역 | 기술 |
| --- | --- |
| Frontend | Next.js 16.2.10, React 19, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python, Pydantic, psycopg |
| Database | PostgreSQL, Docker Desktop, project-pinned patched Supabase CLI |
| 계약 | OpenAPI, JSON Schema, 생성 TypeScript 타입 |
| 테스트 | Pytest, pgTAP, Vitest, Playwright |
| 패키지 관리 | pnpm workspace, uv |

고정 런타임 버전:

| 도구 | 버전 |
| --- | --- |
| Node.js | 24.12.0 |
| pnpm | 11.13.0 |
| Python | 3.12.13 |
| uv | 0.11.28 |

## 5. 저장소 구조

```text
apps/api                 FastAPI, 질문 처리, 관리자 API
apps/web                 시민·관리자 Next.js 화면
contracts                OpenAPI와 JSON Schema
packages/shared-contracts 생성 TypeScript 계약
database                 논리 DB projection과 rollback
supabase/migrations      실행 가능한 DB migration
supabase/tests/database  pgTAP 검증
data                     공식 KB·기관·평가 질문
scripts                  로컬 DB·seed·실행·보안 검사
tools/web-e2e            브라우저 E2E
docs                     핵심 아키텍처·보안·데이터·검증 근거
```

## 6. 실행 방법

### 6.1 준비 사항

- Windows 11
- Windows PowerShell 5.1 이상
- Git
- Docker Desktop
- 위 표의 Node.js, pnpm, Python, uv 버전
- 짧은 영문 경로의 checkout 권장

### 6.2 설치

```powershell
git clone https://github.com/nxtcloud-edu/2026-07-kosj-industry-practice-team02.git
cd 2026-07-kosj-industry-practice-team02

corepack pnpm install --frozen-lockfile --ignore-scripts
uv sync --project apps/api --frozen
```

`.env.example`에는 실제 비밀값이 없습니다. API와 Web을 실행할 때 각각의 예제 파일을 복사하되 API key, DSN, 서명 secret은 커밋하지 않습니다.

### 6.3 화면만 빠르게 확인

DB 없이 화면 구성을 확인하는 fixture 모드입니다. 화면에 `시연용 샘플 — 공식 데이터 아님` 표시가 나타나며 실제 승인과 ACTIVE 전환은 비활성화됩니다.

```powershell
$env:CHAT_UI_MODE = "fixture"
$env:ADMIN_UI_ENABLED = "true"
$env:ADMIN_UI_MODE = "fixture"
corepack pnpm --filter @sejong-ai/web dev
```

- Web: `http://127.0.0.1:3000`
- 시민 화면: `/chat`
- 관리자 화면: `/admin`

### 6.4 실제 local DB 준비

Docker Desktop을 실행한 뒤 저장소 루트에서 진행합니다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/bootstrap_patched_supabase.ps1 -Install

powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/verify_database.ps1
```

`verify_database.ps1`은 disposable local DB를 검증하고 `apps/api/.env`에 local `DATABASE_URL`만 기록합니다. `supabase/config.toml`의 `[db.seed].enabled=false`를 유지하므로 공식 데이터는 별도 단계로 적재합니다.

```powershell
$supabase = ".\.tools\supabase\v2.109.1-sejong-loopback\supabase.exe"
$status = & $supabase status -o env
$dbLine = @($status | Where-Object { $_ -match '^DB_URL=' })
if ($dbLine.Count -ne 1) { throw "LOCAL_DB_STATUS_INVALID" }

$env:SEJONG_ADMIN_DATABASE_URL = (
  $dbLine[0].Substring(7).Trim().Trim('"')
)

uv run --project apps/api --frozen python scripts/verify_data_seed_db.py `
  seed-cycle --release-version 0.1.0-initial.2

uv run --project apps/api --frozen python scripts/verify_data_seed_db.py `
  verify-final --release-version 0.1.0-initial.2

Remove-Item Env:SEJONG_ADMIN_DATABASE_URL
```

이 단계가 완료되면 ACTIVE KB 19개, 공식 기관 3개, 매핑 10개가 기준선입니다.

### 6.5 API 실행

context token secret을 로컬 `.env`에 안전하게 생성한 후 API를 시작합니다. 생성된 값은 출력되지 않습니다.

```powershell
uv run --project apps/api --frozen python scripts/provision_local_context_secret.py
uv run --project apps/api --frozen python scripts/run_local_api.py --port 8000
```

- Health: `http://127.0.0.1:8000/health`
- Ready: `http://127.0.0.1:8000/ready`

정식 19/3/10 기준선과 설정이 준비되면 `/ready`가 200을 반환합니다.

### 6.6 Web 실제 연동

새 PowerShell 터미널에서 실행합니다.

```powershell
$env:API_INTERNAL_BASE_URL = "http://127.0.0.1:8000"
$env:CHAT_UI_MODE = "actual"
$env:ADMIN_UI_ENABLED = "true"
$env:ADMIN_UI_MODE = "actual"
corepack pnpm --filter @sejong-ai/web dev
```

브라우저에서 `http://127.0.0.1:3000`을 엽니다.

## 7. AI 연결

AI 없이도 공식 KB 기반 답변·폴백·관리자 승인 흐름은 작동합니다. AI를 사용할 때는 `apps/api/.env`의 빈 칸에 로컬 key를 입력합니다.

### DeepSeek 질문 분류·근거 제한형 답변 생성

```dotenv
CLASSIFIER_PROVIDER=deepseek
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com
UPSTAGE_SYNTHETIC_EVALUATION_MODE=false
UPSTAGE_CLASSIFIER_MODE=false
UPSTAGE_GROUNDED_CHAT_MODE=false
```

두 역할은 Git 밖의 동일한 `DEEPSEEK_API_KEY`를 사용합니다. 모델은 마스킹된 질문과 서버가 선택한 ACTIVE/OFFICIAL KB의 제한된 fact만 받으며, 사실·출처·기관 정보는 계속 서버가 결합합니다. timeout·JSON·계약·근거 검증에 실패하면 공식 KB TEMPLATE 답변으로 전체 복구합니다. 기본값은 계속 `disabled`이고 실제 key를 설정한 `.env`는 Git에 추가하지 않습니다.

## 8. 동작 확인 시나리오

1. `전입신고는 언제까지 해야 하나요?`
   → 공식 절차·출처·신청 경로
2. `증명서 발급하고 싶어요`
   → 필요한 증명서를 묻는 FOLLOWUP
3. `아름동에서 대형폐기물은 언제 내놓나요?`
   → 선택 지역의 공식 기관 카드
4. `제 자동차세 얼마 나왔나요?`
   → PERSONAL_LOOKUP, 후보 생성 및 질문 저장 없음
5. `침대 2인용 프레임 수수료가 얼마예요?`
   → 승인 전 INSUFFICIENT_GROUNDING
   → 이음센터에서 후보 작성·다른 승인자 승인
   → 20번째 ACTIVE 반영 후 같은 질문 SUCCESS와 공식 출처

19→20 승인 흐름은 DB 상태를 변경하므로 19 기준선에서 한 번 실행합니다. 다시 실행하려면 local DB migration과 정식 seed 절차로 기준선을 복원합니다.

## 9. 검증 명령

```powershell
# API
uv run --project apps/api --frozen ruff format --check apps/api
uv run --project apps/api --frozen ruff check apps/api
uv run --project apps/api --frozen mypy apps/api/src apps/api/tests
uv run --project apps/api --frozen pytest -q apps/api/tests

# 공유 계약
corepack pnpm --filter @sejong-ai/shared-contracts generate:check
corepack pnpm --filter @sejong-ai/shared-contracts test

# Web
corepack pnpm --filter @sejong-ai/web lint
corepack pnpm --filter @sejong-ai/web typecheck
corepack pnpm --filter @sejong-ai/web test
corepack pnpm --filter @sejong-ai/web build

# 비밀값 검사
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/check_secret_patterns.ps1
python -B scripts/check_git_history_secrets.py --repo .
```

### 9.1 이번 스냅샷 검증 결과

2026-07-30에 위 공개 스냅샷에서 새로 실행한 결과입니다.

| 영역 | 결과 |
| --- | --- |
| API Ruff format/check | PASS — 135 files |
| API strict Mypy | PASS — 135 source/test files |
| API Pytest | PASS — 2,612 passed, local DB 전용 8 skipped, 5 subtests passed |
| 공유 계약 | PASS — 96/96 |
| Web lint/typecheck/test/build | PASS — Vitest 77/77, Next production build |
| 현재 파일·공개 Git history 비밀값 검사 | PASS — finding 0 |

Docker DB reset·seed·`/ready=200`·19→20 상태 변경은 이번 공개 export에서 다시 실행하지 않았습니다. 관련 local 실행 절차와 기존 검증 근거는 `docs/test-reports/FINAL-LOCAL-DEMO-REHEARSAL.md`와 `docs/data-lineage/MVP-001-KB-WASTE-03-LOCAL-WORKFLOW.md`에 포함했습니다.

## 10. 팀 역할

| 이름 | 역할 | 담당 |
| --- | --- | --- |
| 김정하 | PM · Frontend · 발표 | 기획, 시민·관리자 화면, 반응형·접근성, 산출물 통합 |
| 곽태성 | Backend | API, DB, 계약, migration, seed와 실행 환경 |
| 이유라 | Data · AI | 증명서·지방세 KB, 검색·AI 품질 |
| 오현송 | Data · AI | 전입·대형폐기물 KB, 테스트셋·QA |

## 11. 현재 한계

- local/private 학습·시연용 MVP입니다.
- 공개 배포와 remote DB는 구성하지 않았습니다.
- 실제 신청·개인별 조회·본인 인증·정부24 내부 연계는 지원하지 않습니다.
- 관리자 화면은 local demo actor를 사용하며 public 인증·SSO/RBAC는 구현 범위 밖입니다.
- GPS·최단거리 기관 계산·지도·다국어·음성은 포함하지 않습니다.
- 외부 AI 공급자의 품질·비용·가용성은 운영 환경에서 별도 검증이 필요합니다.

## 12. 제출 스냅샷

- 스냅샷 작성일: 2026-07-30
- 실제 `.env`, key, token, DSN, local DB 상태, 개인정보, 로그, cache와 build 산출물은 포함하지 않습니다.
- 기존 입찰제안서 PDF와 `notice.md`는 원본 그대로 보존합니다.
