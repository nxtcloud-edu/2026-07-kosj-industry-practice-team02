# API

FastAPI 기반의 세종 민원이음 서버입니다.

## 주요 경로

- `GET /health`: 프로세스 상태 확인
- `GET /ready`: DB·공식 데이터·필수 설정 준비 상태 확인
- `POST /api/v1/chat`: 마스킹 → 분류 → ACTIVE KB 검색 → 근거 판정 → 구조화 답변
- `GET /api/v1/offices`: 선택 지역과 민원 분야에 맞는 공식 기관 조회
- `/api/v1/admin/*`: local/private 관리자 승인 흐름

## 안전 경계

- 질문 원문과 개인정보를 DB·일반 로그에 저장하지 않습니다.
- 외부 모델 호출 전 개인정보를 마스킹합니다.
- 출처명·URL·확인일은 서버가 공식 KB metadata에서 결합합니다.
- 시민 검색 대상은 `ACTIVE` KB로 제한합니다.
- 근거 부족 질문만 관리자 개선 큐에 저장합니다.
- 관리자 API는 local/private 구성에서만 활성화합니다.

DeepSeek 질문 분류와 Upstage 근거 기반 답변은 선택 기능입니다. 설정이 없거나 모델 응답이
계약을 통과하지 못하면 기존 결정론적 분류 또는 공식 템플릿 답변으로 안전하게 폴백합니다.

## 실행

저장소 루트에서:

```powershell
uv sync --project apps/api --frozen
uv run --project apps/api --frozen python scripts/run_local_api.py --port 8000
```

필수 local 설정은 `apps/api/.env.example`을 참고해 ignored
`apps/api/.env`에 작성합니다. 비밀값은 커밋하지 않습니다.

## 검증

```powershell
uv run --directory apps/api --frozen ruff format --check .
uv run --directory apps/api --frozen ruff check .
uv run --directory apps/api --frozen mypy src
uv run --directory apps/api --frozen pytest -q
```
