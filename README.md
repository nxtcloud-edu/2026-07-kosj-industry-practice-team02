# 세종 민원이음 (플랫폼명: 민원이음) — 3주차 MVP

> **모르면 지어내지 않고, 알면 끝까지 안내한다.**

2026년 7월 고려대 세종 산업체 실습 프로젝트 2팀이 만든 local/private MVP입니다.
시민과 공식 행정 지식을 잇고, 답하지 못한 질문을 사람의 검수·승인을 거쳐 다음 답변 개선으로
잇습니다.

이 저장소는 실행 가능한 공개 평가 snapshot입니다. API·Web·공유 계약·DB migration·승인된
공식 데이터와 재현 문서를 포함하며, 비밀값·local DB 상태·실제 개인정보·로그·빌드 산출물은
포함하지 않습니다. 출처와 검증 범위는 [WEEK3_EVALUATION.md](WEEK3_EVALUATION.md)에
기록했습니다.

## 1. 프로젝트 소개

민원이음은 시민의 일상어 질문을 승인된 공식 KB와 연결해 절차, 준비 서류, 비용, 처리 기간,
담당 기관과 공식 출처를 안내합니다. 근거가 부족하면 답을 만들지 않고 안전하게 폴백합니다.
지원 범위 안의 `INSUFFICIENT_GROUNDING` 질문만 이음센터에서 사유 확정 → KB 후보 작성 →
작성자와 다른 승인자의 검수 → ACTIVE 반영으로 이어집니다.

```text
세종 민원이음
├─ 시민용 민원이음 — apps/web
│  ├─ /, /chat
│  ├─ 전입·주민등록, 증명서 발급, 대형폐기물, 지방세 일반 안내
│  ├─ 구조화 답변, 공식 출처, 후속질문, 안전한 폴백
│  └─ 모바일 우선, 키보드 접근성, 본문 대비 4.5:1 이상
├─ 관리자용 이음센터 — apps/web/src/app/admin
│  └─ 실패 질문 → 사유 확정 → KB 후보 → 별도 승인자 → ACTIVE
└─ Backend — apps/api + contracts + database + supabase + data
   └─ 마스킹 → 분류 → ACTIVE 검색 → 근거 gate → 답변/폴백
```

## 2. 해결하려는 문제

| 문제 | 기존 어려움 | 민원이음의 해결 방향 |
|---|---|---|
| 시민 접근성 | 야간·주말에는 즉시 안내받기 어려움 | 승인 KB 기반 상시 안내 |
| 정보 정확성 | 창구와 문서마다 안내를 다시 찾아야 함 | 공식 출처·확인일이 결합된 구조화 답변 |
| 행정 효율 | 반복 문의가 담당자 업무를 점유함 | 반복 질문은 자동 안내하고 개인 조회는 공식 채널로 연결 |
| 지식 공백 | 무엇을 보강해야 하는지 체계적으로 남지 않음 | 근거 부족 질문만 사람 승인형 KB 개선 루프로 전환 |

## 3. 핵심 설계 원칙

- **근거가 없으면 생성하지 않습니다.** 시민 검색 대상은 `ACTIVE+OFFICIAL` KB뿐이며,
  출처명·URL·확인일은 LLM이 아니라 서버가 KB 메타데이터에서 결합합니다.
- **시민 응답 경로의 외부 LLM 호출은 0회입니다.** 승인 KB 기반 결정론적 template 경로를
  사용해 호출 비용과 환각 가능성을 구조적으로 차단합니다.
- **Upstage는 합성 평가 전용입니다.** `solar-pro3` adapter는 승인된 local/private 합성
  allowlist에서만 사용하며 기본값은 `LLM_PROVIDER=disabled`입니다.
- **개인정보를 먼저 줄입니다.** 외부 처리 전에 마스킹하고 질문 원문은 DB·URL·브라우저
  저장소·액세스 로그에 저장하지 않습니다.
- **개인 조회와 법적 판단은 질문·상호작용·실패 행을 만들지 않습니다.** `PERSONAL_LOOKUP`과
  `LEGAL_JUDGMENT`는 `candidate_eligible=false`이며 질문 text, interaction event,
  failed-question row를 만들지 않습니다.
- **AI는 제안하고 사람은 판정합니다.** KB 후보 작성자와 승인자를 분리하고,
  MOCK 후보의 ACTIVE 승격을 차단합니다.

## 4. 현재 구현 범위와 데이터

- 시민 화면: `/`, `/chat`
- local/private 관리자 화면: `/admin`
- FastAPI: `/health`, `/ready`, `/api/v1/chat`, local/private admin API
- 모호 질문: `FOLLOWUP`
- 폴백: `INSUFFICIENT_GROUNDING`, `PERSONAL_LOOKUP`, `LEGAL_JUDGMENT`,
  `OUT_OF_SCOPE`, `PRIVACY_UNRESOLVED`
- immutable 공식 release: `0.1.0-initial.2`
- 정식 seed 기준선: ACTIVE KB 19개, 공식 기관 3개, 기관 매핑 10개
- 승인 데모 결과: 별도 승인으로 `KB-WASTE-03`을 20번째 ACTIVE로 만든 뒤 동일 질문 SUCCESS
- 결정론적 평가 질문: 20개, skip 0

`supabase/config.toml`은 `[db.seed].enabled=false`입니다. 따라서 `db reset`은 migration만
적용하며 공식 데이터를 자동 적재하지 않습니다. `.2` release는 반드시 별도 `seed-cycle`과
`verify-final`을 거칩니다.

## 5. 기술 스택과 고정 버전

| 영역 | 기술 |
|---|---|
| Frontend | Next.js 16, React, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python, uv |
| Database | PostgreSQL, Docker Desktop, project-pinned patched Supabase CLI |
| 계약 | OpenAPI v1, JSON Schema, 생성 TypeScript 타입 |
| 테스트 | Pytest, pgTAP, Vitest, Playwright |
| 패키지 관리 | pnpm workspace |

| 도구 | 정확한 버전 |
|---|---:|
| Node.js | 24.12.0 |
| pnpm | 11.13.0 |
| Python | 3.12.13 |
| uv | 0.11.28 |

## 6. 평가자 빠른 실행

### 6.1 설치

```powershell
git clone https://github.com/nxtcloud-edu/2026-07-kosj-industry-practice-team02.git
cd 2026-07-kosj-industry-practice-team02
corepack pnpm install --frozen-lockfile --ignore-scripts
uv sync --project apps/api --frozen
```

`.env.example` 파일에는 비민감 local 기본값과 빈 secret 칸만 있습니다. 실제 `.env`, key,
token, DSN은 커밋하지 않습니다.

### 6.2 DB 없이 화면 먼저 확인

UI와 접근성을 먼저 볼 때 사용하는 명시적 fixture 모드입니다. 모든 화면에
`시연용 샘플 — 공식 데이터 아님`이 표시되며 관리자 승인·ACTIVE 전환은 비활성입니다.

```powershell
$env:CHAT_UI_MODE = "fixture"
$env:ADMIN_UI_ENABLED = "true"
$env:ADMIN_UI_MODE = "fixture"
corepack pnpm --filter @sejong-ai/web dev
```

`http://127.0.0.1:3000`에서 `/`, `/chat`, `/admin`을 확인합니다.

### 6.3 실제 API·DB·19→20 승인 흐름

이 경로는 **Windows amd64, Windows PowerShell 5.1+, Git, Docker Desktop
(Docker server 28+), 짧은 영문 checkout 경로**가 필요합니다. remote project에는 연결하지
않으며 `127.0.0.1`의 disposable DB만 사용합니다.

먼저 Docker Desktop을 켜고, 저장소 루트에서 pinned CLI와 DB 기준선을 준비합니다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/bootstrap_patched_supabase.ps1 -Install
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/verify_database.ps1
```

`verify_database.ps1`은 migration·rollback·pgTAP·local login을 검증하고
`apps/api/.env`에 local `DATABASE_URL`만 기록합니다. 이어서 같은 DB에 immutable `.2`를
별도 적재하고 19/3/10을 확인합니다. 아래 명령은 admin DSN을 화면에 출력하지 않습니다.

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

API 터미널에서 32-byte 이상 context secret을 process-only로 만들고 API를 시작합니다.
할당 결과는 출력하지 않으며 터미널 종료 시 사라집니다.

```powershell
$contextTokenSecret = uv run --project apps/api --frozen python -c `
  "import secrets; print(secrets.token_urlsafe(32))"
Set-Item -LiteralPath Env:CONTEXT_TOKEN_SECRET -Value $contextTokenSecret
Remove-Variable contextTokenSecret
uv run --project apps/api --frozen python scripts/run_local_api.py --port 8000
```

별도 Web 터미널:

```powershell
$env:API_INTERNAL_BASE_URL = "http://127.0.0.1:8000"
$env:CHAT_UI_MODE = "actual"
$env:ADMIN_UI_ENABLED = "true"
$env:ADMIN_UI_MODE = "actual"
corepack pnpm --filter @sejong-ai/web dev
```

- Web: `http://127.0.0.1:3000`
- Health: `http://127.0.0.1:8000/health` → 200
- Ready: `http://127.0.0.1:8000/ready` → approved 19/3/10이면 200

실제 브라우저 승인 루프는 19 ACTIVE 기준선에서 한 번만 실행합니다. DB 상태를 20으로
변경하므로 재실행 전에는 위 migration·seed 절차로 19 기준선을 복원합니다.

```powershell
corepack pnpm --filter @sejong-ai/web build
corepack pnpm --dir tools/web-e2e install --frozen-lockfile --ignore-scripts
corepack pnpm --dir tools/web-e2e exec playwright install chromium
$env:E2E_ACTUAL = "1"
corepack pnpm --dir tools/web-e2e test
Remove-Item Env:E2E_ACTUAL
```

전체 seed의 실패·동시성·보상·재실행 방지까지 검사하는 별도 gate는 다음과 같습니다.
이 스크립트는 검증 뒤 자신이 소유한 DB runtime을 안전하게 종료하므로 API 실행 직전에
사용하지 않습니다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/verify_data_seed.ps1 -ReleaseVersion 0.1.0-initial.2
```

## 7. 팀 역할

| 이름 | 역할 | 담당 영역 | 핵심 책임 |
|---|---|---|---|
| 김정하 | PM/Frontend/발표 | 기획·제안서, 시민 화면·이음센터 UI, 디자인 시스템 | 방향성 유지, 요구사항 대응, 프론트엔드 구현(화면·반응형·접근성), 산출물 통합, 발표 |
| 곽태성 | Backend | API·DB·contracts, 데이터 릴리스, CI·협업 정책 | 서버 구현, 계약 정의와 검증, DB·seed 파이프라인, 저장소 거버넌스 |
| 이유라 | AI/Data | KB(증명서 발급, 지방세), 검색 | 지식베이스 구축·검증, 검색 파이프라인 |
| 오현송 | AI/Data | KB(전입·주민등록, 대형폐기물), QA | 지식베이스 구축·검증, 테스트셋, 품질 평가 |

## 8. 프로젝트 일정

| 주차 | 기간 | 핵심 목표 | 상태 |
|---|---|---|---|
| 1주차 | 7/6~7/10 | RFP 분석, 문제 정의, 기본 설계 | 완료 |
| 2주차 | 7/13~7/17 | 입찰 제안서, KB·계약 기준선 | 완료 |
| 3주차 | 7/20~7/24 | 시민·이음센터 P0, API·DB·Web 통합, 평가 snapshot | 완료 |
| 4주차 | 7/27~7/31 | 기능 동결, 회귀·데모 리허설, 발표자료·영상 | 예정 |

## 9. 5문항 데모 시나리오

1. **정상:** “전입신고는 언제까지 해야 하나요?” → 14일, 공식 출처·확인일·신청 경로
2. **정상+기관:** “아름동에서 대형폐기물은 언제 내놓나요?” → 선택 지역의 담당 기관
3. **후속질문:** “이사했는데 뭐 해야 하나요?” → 단정하지 않고 선택지 제시
4. **개인 조회 폴백:** “제 자동차세 얼마 나왔나요?” → `PERSONAL_LOOKUP`,
   `candidate_eligible=false`, 질문 text/event/failed row 저장 0
5. **개선 루프:** “침대 2인용 프레임 배출 수수료” → `INSUFFICIENT_GROUNDING` →
   실패 질문 → 사유 확정 → 후보 → 다른 승인자 → `KB-WASTE-03` ACTIVE(19→20) →
   동일 질문 SUCCESS와 공식 출처

## 10. 검증 결과

| Gate | 실제 결과 |
|---|---|
| API format/lint/typecheck | PASS — Ruff, strict Mypy 87 files |
| API test | PASS — 1,782 passed / local DB 전용 8 skipped |
| Web lint/typecheck/test/build | PASS — Vitest 49/49, Next production build |
| Web fixture E2E | PASS — 390px·430px·desktop 18/18 |
| Web actual 승인 루프 | PASS — local/private 1/1 |
| Shared contracts | PASS — 89/89 |
| 결정론적 표본 | PASS — 20/20, skip 0 |
| 데이터·문서 focused gate | PASS — 120 passed, 1 skipped, 85 subtests |
| 공개 tree·Git history secret scan | PASS — finding 0 |

재현 명령과 provenance는 [WEEK3_EVALUATION.md](WEEK3_EVALUATION.md), 표본 결과는
[MVP-001-SAMPLE-20-RESULT.md](docs/test-reports/MVP-001-SAMPLE-20-RESULT.md)에 있습니다.

## 11. 안전 경계와 Pending

- 질문 원문, 실제 개인정보, IP·기기 ID를 애플리케이션 DB에 저장하지 않습니다.
- `OUT_OF_SCOPE`, `PERSONAL_LOOKUP`, `LEGAL_JUDGMENT`, `PRIVACY_UNRESOLVED`는
  개선 후보로 만들지 않습니다.
- 공개 배포, remote DB, public admin 인증·SSO/RBAC, 자동 backup은 아직 완료하지 않았습니다.
- 실제 시민 질문의 외부 provider 전송, 100명 부하 목표와 production 운영 승인을 주장하지 않습니다.
- 이 snapshot은 local/private 학습·평가용이며 공고문의 기관·예산은 실제 사업 정보가 아닙니다.

기존 평가 저장소의 `[2026-세종-0001] 입찰제안서_세종 민원이음_2팀.pdf`와
`notice.md`는 원본 그대로 보존했습니다.
