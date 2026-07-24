# 세종 민원 AI 길잡이 — 3주차 MVP

> 모르면 지어내지 않고, 알면 끝까지 안내한다.

세종 민원 AI 길잡이는 시민의 일상어 질문을 승인된 공식 행정 지식과 연결하고, 근거가 부족한 질문을 사람의 작성·별도 승인 절차를 거쳐 새 ACTIVE KB로 개선하는 local/private MVP입니다.

이 저장소는 3주차 평가를 위한 실행 가능한 공개 snapshot입니다. 검증된 API·Web·공유 계약·DB
migration·공식 데이터와 재현 문서를 포함하며, 비밀값·local DB 상태·실제 개인정보·로그/trace·
dependency/build 산출물은 포함하지 않습니다. 정확한 provenance와 검증 결과는
[WEEK3_EVALUATION.md](WEEK3_EVALUATION.md)에 기록했습니다.

## 구현 범위

- 시민 화면: `/`, `/chat`
- local/private 관리자 화면: `/admin`
- 분야: 전입·주민등록, 증명서 발급, 대형폐기물, 지방세 일반 안내
- FastAPI `/api/v1/chat`: 개인정보 마스킹 → 정책 분류 → ACTIVE KB 검색 → 근거 gate → 구조화 답변 또는 안전한 폴백
- `INSUFFICIENT_GROUNDING` 실패 → KB 후보 → 작성자와 다른 승인자 → 20번째 ACTIVE → 동일 질문 재질의 SUCCESS
- `PERSONAL_LOOKUP`: `intent=UNKNOWN`, `candidate_eligible=false`, 질문 text/event/failed row 미저장
- 서버가 승인 KB에서 출처명·URL·확인일을 결합하며 LLM이 출처를 만들지 않음

## 역할 분담

- Owner / Backend·AI/Data·Security·Docs: API, DB, 공식 데이터, 개인정보·근거 정책, 통합 검증
- Frontend collaborator: `/`, `/chat`, `/admin`, typed API client, 반응형·접근성, Web unit/E2E
- PM reviewer: 공식 데이터와 KB 후보의 별도 검수·승인

## 저장소 구조

```text
apps/api/                 FastAPI API, 개인정보·검색·승인 흐름
apps/web/                 Next.js 시민·관리자 UI
packages/shared-contracts/ OpenAPI/JSON Schema/TypeScript 공유 계약
contracts/                공개 API 계약
supabase/migrations/      실행 가능한 DB migration 권위
database/                 local DB 논리 projection·rollback
data/official/            승인된 immutable 공식 데이터 release
data/evaluation/          표본 질문
tools/web-e2e/            Playwright 브라우저 검증
scripts/                  검증·seed·local 실행 도구
```

## 요구 버전

| 도구 | 버전 |
|---|---:|
| Node.js | 24.12.0 |
| pnpm | 11.13.0 |
| Python | 3.12.13 |
| uv | 0.11.28 |

## 설치

```powershell
corepack pnpm install --frozen-lockfile --ignore-scripts
uv sync --project apps/api --frozen
```

`.env.example`, `apps/api/.env.example`, `apps/web/.env.example`은 값이 비어 있는 템플릿입니다. 실제 `.env`, API key, DSN은 커밋하지 않습니다. Upstage 호출은 합성 평가 전용이며 시민 질문 경로에서는 기본 비활성입니다.

## 로컬 실행

local DB와 승인 seed가 준비되지 않은 import-safe 기본 API는 의도적으로 `/ready=503`입니다.
아래 정식 seed 절차와 local login 준비가 성공한 뒤에만 local API가 `/ready=200`을 반환합니다.
Docker Desktop을 켠 뒤 먼저 다음 절차를 수행합니다.

```powershell
# 짧은 영문 경로의 checkout에서 실행
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/bootstrap_patched_supabase.ps1 -Install
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/verify_database.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/verify_data_seed.ps1 -ReleaseVersion 0.1.0-initial.2
```

첫 명령이 프로젝트 전용 patched Supabase CLI를 `.tools/`에 생성합니다. `.tools/`는 재생성 가능한
로컬 도구이므로 저장소에는 포함하지 않습니다.

```powershell
# API — process-only DATABASE_URL과 32-byte 이상 CONTEXT_TOKEN_SECRET 필요
uv run --project apps/api --frozen python scripts/run_local_api.py --port 8000

# Web — 별도 터미널
$env:API_INTERNAL_BASE_URL = "http://127.0.0.1:8000"
corepack pnpm --filter @sejong-ai/web dev
```

- Web: `http://127.0.0.1:3000`
- API health: `http://127.0.0.1:8000/health`
- API readiness: `http://127.0.0.1:8000/ready`

## 정식 seed와 19→20 승인 흐름

`supabase/config.toml`은 `[db.seed].enabled=false`를 유지합니다. 따라서 `db reset --local`은 migration만 재현하며 seed를 자동 실행하지 않습니다. local admin DSN은 출력하지 않고 process-only `SEJONG_ADMIN_DATABASE_URL`로 전달합니다.

정식 `.2` seed의 시작 상태는 ACTIVE KB 19개, 공식 기관 3개, 승인 매핑 10개입니다. 별도 local rehearsal은 `/ready=200`을 확인한 뒤 근거 부족 질문을 저장하고, `KB-WASTE-03` 후보를 작성자와 다른 승인자가 승인해 20번째 ACTIVE로 만들고, 동일 질문의 SUCCESS와 공식 출처를 확인합니다.

## 검증

```powershell
# API
uv run --directory apps/api --frozen ruff format --check .
uv run --directory apps/api --frozen ruff check .
uv run --directory apps/api --frozen mypy src tests
uv run --directory apps/api --frozen pytest -q

# Web
corepack pnpm --filter @sejong-ai/web lint
corepack pnpm --filter @sejong-ai/web typecheck
corepack pnpm --filter @sejong-ai/web test
corepack pnpm --filter @sejong-ai/web build

# 공유 계약과 공개 snapshot 보안
corepack pnpm --filter @sejong-ai/shared-contracts test
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/check_secret_patterns.ps1 -RepositoryRoot .
```

평가 snapshot의 출처, 제외 범위, 정책과 실제 검증 결과는
[WEEK3_EVALUATION.md](WEEK3_EVALUATION.md)에 정리돼 있습니다. 결정론적 표본 20개 결과는
[MVP-001-SAMPLE-20-RESULT.md](docs/test-reports/MVP-001-SAMPLE-20-RESULT.md)에서 바로 확인할 수
있습니다.

## 안전 경계

- 질문 원문, 실제 개인정보, IP·기기 ID를 애플리케이션 DB에 저장하지 않습니다.
- `PERSONAL_LOOKUP`, `LEGAL_JUDGMENT`, `OUT_OF_SCOPE`, `PRIVACY_UNRESOLVED`는 후보로 만들지 않습니다.
- 시민 검색은 ACTIVE+OFFICIAL KB만 사용합니다.
- 작성자는 자기 후보를 승인할 수 없습니다.
- 이 snapshot은 local/private MVP 증거이며 public 배포·remote DB·실사용 운영 승인이 아닙니다.

기존 평가 저장소의 입찰제안서 PDF와 `notice.md`는 원본 그대로 보존했습니다.
