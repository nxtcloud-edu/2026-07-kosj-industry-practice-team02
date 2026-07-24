# Contributing

## 기본 흐름

1. 최신 `main`에서 작업 브랜치를 만듭니다.
2. 한 PR에는 하나의 목적만 담습니다.
3. 공개 계약, migration, 공식 데이터, 개인정보 정책 변경은 reviewer 승인을 먼저 받습니다.
4. 변경 영역의 lint, typecheck, test, build와 비밀 검사를 실행합니다.
5. PR에서 변경 이유, 검증 결과, 데이터·보안 영향과 롤백 방법을 기록합니다.
6. CI가 통과한 뒤 reviewer가 병합합니다. `main` 직접 push와 자동 병합은 사용하지 않습니다.

브랜치 예:

```text
feat/web-chat-source-cards
fix/api-personal-lookup-storage
docs/week3-evaluation
```

## 필수 검증

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

# 계약·보안
corepack pnpm --filter @sejong-ai/shared-contracts test
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/check_secret_patterns.ps1 -RepositoryRoot .
```

## 금지 사항

- 실제 `.env`, key, token, DSN, 시민 질문 원문, 실제 개인정보 커밋
- 승인되지 않은 KB 또는 mock 데이터를 공식 근거로 사용
- LLM이 생성한 출처명·URL·확인일을 시민에게 노출
- production dependency, 공개 API, DB migration, 보관 정책의 무승인 변경
- public/remote 환경에서 local demo actor 또는 개발 DB credential 사용

버그·보안 수정은 재현 테스트와 함께 제출하고, 호환성 파괴 변경에는 migration/rollback과
계약 버전 변경을 포함합니다.
