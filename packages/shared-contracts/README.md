# shared-contracts

OpenAPI/JSON Schema로부터 동기화한 프론트·백엔드 공용 계약 검증 package다. 현재는 runtime business logic이나 생성 타입을 포함하지 않는다.

## 검증 범위

- 요청 fixture 3개는 OpenAPI `ChatRequest`로 검증한다.
- 응답 fixture 9개는 OpenAPI `ChatResponse`와 standalone `chat-response.schema.json` 양쪽에서 검증한다.
- 오류 fixture 4개는 OpenAPI `ServiceUnavailableEnvelope`로 검증한다.
- 총 25 fixture validations와 5 structure tests가 SUCCESS source 1개 이상, context nullability, `session_id` 거부, FALLBACK office, 503 envelope/reference를 고정한다.

Fixture는 합성 UUID, `example.invalid`, `시연용 샘플`만 사용하며 공식 행정 데이터가 아니다.

## 실행

```powershell
corepack.cmd pnpm install --frozen-lockfile
corepack.cmd pnpm --filter @sejong-ai/shared-contracts test
```

검증 helper는 OpenAPI의 모든 component schema를 `$defs`로 복제하고 내부 component reference만 rewrite한다. 알 수 없는 component와 외부 reference는 실패시켜 부분 검증을 방지한다. TypeScript 생성물과 Pydantic 소비 모델은 `CONTRACT-001B`에서 추가한다.
