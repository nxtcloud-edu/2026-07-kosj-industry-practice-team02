# 오류·상태 코드 카탈로그

## 사용자 응답 상태

| Code | HTTP | 의미 | 사용자 행동 |
|---|---:|---|---|
| SUCCESS | 200 | 공식 근거 답변 | 출처/기관 확인 |
| FOLLOWUP | 200 | 질문 모호 | 선택지 응답 |
| FALLBACK | 200 | 정책상 직접 답변 금지 | 공식 경로/기관 |
| SYSTEM_ERROR | 503 | 승인된 근거로도 안전 응답 생성 불가 | 재시도/기관 안내 |

## 내부 오류 코드 초안

| Code | HTTP | 설명 | 로그 정책 |
|---|---:|---|---|
| REQUEST_VALIDATION_FAILED | 422 | 길이/형식 오류 | question 없음 |
| KB_EVIDENCE_INSUFFICIENT | 200 fallback | 근거 기준 미달 | source IDs만 |
| KB_SOURCE_INVALID | 200 fallback | 출처 metadata 누락/invalid | KB ID만 |
| PROVIDER_TIMEOUT | 200 safe degradation 또는 503 | LLM timeout; 안전한 KB 대체 가능성으로 결정 | provider/latency만 |
| PROVIDER_SCHEMA_INVALID | 200 safe degradation 또는 503 | 구조화 출력 invalid; 안전한 KB 대체 가능성으로 결정 | body 저장 금지 |
| INVALID_STATE_TRANSITION | 409 | 후보 상태 오류 | target/status만 |
| SELF_APPROVAL_FORBIDDEN | 403/409 | 작성자 승인 시도 | actor/target만 |
| APPROVER_ROLE_REQUIRED | 403 | 권한 부족 | role/target만 |
| PII_IN_CANDIDATE | 422 | 후보 입력 PII | 탐지 유형만 |
| DATABASE_UNAVAILABLE | 200 safe snapshot 또는 503 | 검증된 ACTIVE snapshot이 없으면 503 | 연결 비밀 없음 |
| SERVICE_UNAVAILABLE | 503 | 안전 대체 경로가 없는 공개 오류 code | request_id·retryable만 |

정책 FALLBACK은 오류 envelope가 아니라 정상 200 `ChatResponse`다. provider 장애 자체가 아니라 승인된 ACTIVE KB로 안전 응답을 완성할 수 있는지가 200/503을 결정한다.
