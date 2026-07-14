# 관측성 정책

## 목표

오류·지연·품질을 진단하되 질문 원문과 개인정보를 관측 시스템에 보내지 않는다.

## 허용 로그/메트릭

- request_id
- route, method, status code
- intent, answer_status, fallback_reason
- source_count와 source ID
- latency, timeout, retry count
- provider name/model identifier
- DeepSeek run attempt count, cap outcome, token usage
- selected region(읍면동)
- candidate/audit state transition IDs
- is_test/mock/source label

## 금지

- raw/masked question을 일반 application log에 출력
- 전체 answer text
- provider request/response body
- API key, Authorization header, cookies
- DB connection string
- chat context token, decoded claim, context signing secret

masked_question은 failed_questions 도메인 저장소에만 보관하고 일반 logger에는 넣지 않는다.

## KPI 출처 라벨

- EVENT: 실제 비식별 이벤트 집계
- EVALUATION: 표본/회귀 테스트
- MOCK: UI 시연용

대시보드는 라벨을 숨기지 않는다.

## 경보 후보

- source-less SUCCESS > 0
- self-approval attempt > 0
- PII test leak > 0
- provider timeout rate
- p95 latency
- retention deletion failures
- DeepSeek outbound attempt cap violation
- context token/storage leak sentinel
