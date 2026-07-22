# shared-contracts

OpenAPI/JSON Schema로부터 동기화한 프론트·백엔드 공용 계약 검증 package다. runtime business logic은 포함하지 않으며, OpenAPI 3.0.0-draft에서 결정적으로 생성한 TypeScript 타입을 추적한다.

package 버전은 `0.3.0`이며 `PRIVACY_UNRESOLVED`의 닫힌 응답과 local/private 관리자 목록·상세·상태변경 envelope를 포함한다.

## 검증 범위

- 요청 fixture 3개는 OpenAPI `ChatRequest`로 검증한다.
- 응답 fixture 20개는 OpenAPI `ChatResponse`와 standalone `chat-response.schema.json` 양쪽에서 검증한다.
- 오류 fixture 4개는 OpenAPI `ServiceUnavailableEnvelope`로 검증한다.
- 관리자 fixture 20개는 성공·오류 envelope와 보관·승인 상태 불변조건을 검증한다.
- 총 67 fixture validations와 structure/type tests가 SUCCESS source·기관 카드, context nullability, `session_id` 거부, 닫힌 FALLBACK, health/readiness 200 body와 503 envelope/reference를 고정한다.
- `src/generated/api.ts`는 `openapi-typescript@7.13.0` Node API로 생성하며 source/API/generator 버전만 banner에 기록한다. 시간·절대 경로는 기록하지 않는다.
- API Pydantic 모델은 같은 합성 JSON fixture를 소비하고 scalar coercion, 상태 불변조건과 응답 추가 필드를 거부한다.

Fixture는 합성 UUID, `example.invalid`, `시연용 샘플`만 사용하며 공식 행정 데이터가 아니다.

## 실행

```powershell
corepack.cmd pnpm install --frozen-lockfile
corepack.cmd pnpm --filter @sejong-ai/shared-contracts test
corepack.cmd pnpm contracts:generate
corepack.cmd pnpm contracts:check
```

검증 helper는 OpenAPI의 모든 component schema를 `$defs`로 복제하고 내부 component reference만 rewrite한다. 알 수 없는 component와 외부 reference는 실패시켜 부분 검증을 방지한다.
`contracts:check`는 생성 결과를 byte 단위로 비교한다. 원본 계약을 바꾼 경우 `contracts:generate` 후 생성물 diff를 함께 검토하고 커밋한다. `defaultNonNullable:false`로 OpenAPI default가 optional 필드를 임의로 required로 바꾸지 않게 고정한다.

생성 TypeScript의 `ChatResponse`는 명시적 `oneOf`와 literal 상태를 사용한 discriminated union이다. 기존 Web workspace의 TypeScript compiler로 유효 SUCCESS/PRIVACY 형태를 허용하고, SUCCESS+privacy 및 FALLBACK의 non-empty source/non-null context를 컴파일 단계에서 거부한다. AJV와 Pydantic fixture gate도 별도로 유지한다.
