# ADR-0009: 안전 응답 불능 시 HTTP 503 계약

- Status: Accepted
- Date: 2026-07-14

## Decision

근거 부족·개인조회·법적 판단·범위 밖은 정상 정책 결과이므로 HTTP 200 `ChatResponse`의 `FALLBACK`으로 반환한다. HTTP 200의 `answer_status`는 `SUCCESS`, `FOLLOWUP`, `FALLBACK`만 허용한다.

분류·검색·근거 검증·응답 조립의 필수 경로가 불능이고 승인된 ACTIVE KB 또는 검증된 snapshot으로도 안전 응답을 만들 수 없을 때만 HTTP 503을 반환한다. 공개 body는 provider/DB 내부 원인을 노출하지 않는 안정된 `SERVICE_UNAVAILABLE` envelope와 `request_id`, `retryable`만 포함한다. 질문, provider body, stack, 비밀값은 body·로그에 넣지 않는다.

provider timeout·empty output·schema invalid 자체는 503 조건이 아니다. ACTIVE KB와 결정론적 템플릿으로 안전한 SUCCESS/FALLBACK을 만들 수 있으면 200으로 degrade한다. 503 요청의 내부 interaction event에는 `answer_status=SYSTEM_ERROR`, `fallback_reason=NULL`을 기록할 수 있다.

이 변경은 기존 200 `ChatResponse`에서 `SYSTEM_ERROR`를 제거하므로 공개 draft 계약의 호환성 파괴다. `contracts/AGENTS.md`의 major-version 규칙과 사용자의 Q-API-001 승인을 따라 API 계약을 `0.2.0-draft`에서 `1.0.0-draft`로 올린다. 아직 구현 소비자와 배포 데이터는 없다.

## Consequences

프론트·프록시·관측이 정책 폴백과 실제 서비스 불능을 정확히 구분할 수 있다. 프론트는 503·unknown 5xx에서 로딩을 해제하고 키보드 접근 가능한 재시도와 일반 안내를 보여야 한다. 같은 provider 장애 fixture라도 KB 안전 대체 가능성에 따라 200/503이 달라지는 계약 테스트가 필요하다.
