# apps/api

세종 민원 AI 길잡이의 FastAPI 서비스다. 현재 수직 흐름은 프로세스 상태와 DB 이전
readiness만 구현한다.

## 현재 동작

- `GET /health`: 외부 의존성을 확인하지 않고 `200 {"status":"ok"}` 반환
- `GET /ready`: DB와 승인 seed가 아직 없으므로 기본적으로 `503 SERVICE_UNAVAILABLE` 반환
- readiness는 typed probe로 주입할 수 있지만, 이 단계에는 DB/provider 구현이나 연결이 없다.
- API 2.0.1-draft는 `/health`와 향후 ready 상태의 `/ready` 200 body를 required·closed schema로 고정한다. pre-DB 기본값은 계속 503이다.
- 승인된 chat request/response와 공통 503은 strict Pydantic v2 경계 모델로 같은 17개 합성 JSON fixture를 소비한다. 숫자·문자열·boolean 간 암묵적 coercion과 FALLBACK 추가 필드를 거부한다.
- 정상 완료와 일반 `Exception` 경로의 HTTP 요청 로그는 서버가 만든 UUID, method, 라우트
  템플릿, status만 JSON 한 줄로 남긴다.
- Uvicorn request-line access log, raw ASGI trace logger, INFO 미만 protocol record와 고정
  WebSocket INFO protocol record는 query·경로·client 정보 노출을 막기 위해 차단한다.
  INFO startup과 일반 error record는 유지하며, 현재 범위 밖인 WebSocket은 실행 명령에서도
  비활성화한다.

채팅 route·관리자 API, DB migration, 외부 LLM 호출은 후속 수직 흐름이며 현재 구현에
포함되지 않는다. 요청 body·query·header·cookie·client IP·응답 본문은 일반 로그에 기록하지
않는다.

## 로컬 환경변수

`apps/api/.env.example`을 `apps/api/.env`로 복사한다. 비밀 칸은 의도적으로 비어 있으며,
현재 health/readiness 앱은 시작 시 환경변수·DB·provider를 읽거나 연결하지 않는다. DeepSeek는
기본 비활성이고 승인된 local/private 합성 평가 단계 전에는 호출하지 않는다.

## 로컬 명령

저장소 루트에서 실행한다.

```powershell
.\.tools\uv\uv.exe sync --project apps/api --frozen
.\.tools\uv\uv.exe run --directory apps/api --frozen pytest -q
.\.tools\uv\uv.exe run --directory apps/api --frozen ruff format --check .
.\.tools\uv\uv.exe run --directory apps/api --frozen ruff check .
.\.tools\uv\uv.exe run --directory apps/api --frozen mypy src tests
.\.tools\uv\uv.exe run --directory apps/api --frozen uvicorn sejong_ai_api.main:app `
  --app-dir src --host 127.0.0.1 --port 8000 --no-access-log --ws none
```

`uv.lock`은 저장소에 포함하며, 의존성 변경이 승인된 경우에만 다시 생성한다.

Codex managed sandbox가 사용자 uv cache를 읽지 못하는 경우에만 Git-ignored
`.superpowers/uv-cache`를 `UV_CACHE_DIR`로 지정한다. 일반 개발자 환경의 필수 설정은
아니다.
