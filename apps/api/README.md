# apps/api

세종 민원 AI 길잡이의 FastAPI 서비스다. 현재 수직 흐름은 프로세스 상태와 DB 이전
readiness만 구현한다.

## 현재 동작

- `GET /health`: 외부 의존성을 확인하지 않고 `200 {"status":"ok"}` 반환
- `GET /ready`: DB와 승인 seed가 아직 없으므로 기본적으로 `503 SERVICE_UNAVAILABLE` 반환
- readiness는 typed probe로 주입할 수 있지만, 이 단계에는 DB/provider 구현이나 연결이 없다.

채팅·관리자 API, DB migration, 외부 LLM 호출, 환경변수/로그 middleware는 후속 수직
흐름이며 현재 구현에 포함되지 않는다.

## 로컬 명령

저장소 루트에서 실행한다.

```powershell
.\.tools\uv\uv.exe sync --project apps/api --frozen
.\.tools\uv\uv.exe run --directory apps/api --frozen pytest -q
.\.tools\uv\uv.exe run --directory apps/api --frozen ruff format --check .
.\.tools\uv\uv.exe run --directory apps/api --frozen ruff check .
.\.tools\uv\uv.exe run --directory apps/api --frozen mypy src tests
.\.tools\uv\uv.exe run --directory apps/api --frozen uvicorn sejong_ai_api.main:app `
  --app-dir src --host 127.0.0.1 --port 8000
```

`uv.lock`은 저장소에 포함하며, 의존성 변경이 승인된 경우에만 다시 생성한다.

Codex managed sandbox가 사용자 uv cache를 읽지 못하는 경우에만 Git-ignored
`.superpowers/uv-cache`를 `UV_CACHE_DIR`로 지정한다. 일반 개발자 환경의 필수 설정은
아니다.
