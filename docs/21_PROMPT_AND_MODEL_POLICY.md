# 프롬프트·모델 정책

## 원칙

- 공급자 모델은 정확히 `deepseek-v4-flash`이며 thinking off, max output 1024, concurrency 1, retry 최대 1회, process run당 outbound attempt 총 30으로 고정하고 도메인 코드와 분리한다.
- 프롬프트는 파일/모듈로 버전 관리하고 코드에 장문 문자열로 흩뜨리지 않는다.
- 구조화 출력은 JSON Schema/Pydantic validation을 통과해야 한다.
- 모델이 source title/url/verified date를 만들지 않는다.
- 모델의 confidence는 근거 충족 판정의 유일한 기준이 아니다.
- 낮은 temperature/생성 자유도와 명확한 context boundary를 사용한다.
- local/private의 서버 검증 합성 fixture만 외부 provider에 허용하고 자유 입력·실제 시민 질문은 disabled/template 경로로 처리한다.

## 입력 허용

- 마스킹된 질문
- 지원 intent/policy
- ACTIVE KB의 필요한 필드/청크
- 출력 schema
- 개인정보 없는 비식별 난수 `user_id`

## 입력 금지

- raw PII
- 비밀키/내부 지침 전문
- 승인되지 않은 candidate를 공식 근거처럼 전달
- 무관한 전체 DB dump
- 클라이언트 `is_test`만 근거로 허용한 자유 입력
- 실제 시민·실제 PII·민감정보·비밀이 든 `user_id`

## 출력 검증 실패

1. schema repair/retry 최대 1회
2. KB가 충분하면 서버 템플릿 응답
3. 근거가 없으면 안전 폴백
4. 질문 원문 없이 provider/error metric 기록

## DeepSeek adapter 기준

- 정확한 모델은 `deepseek-v4-flash`로 pin한다. `deepseek-chat`·`deepseek-reasoner` alias와 다른 model ID는 설정 검증에서 거부한다.
- JSON Output에 `response_format={"type":"json_object"}`를 사용하고 prompt에 `json`과 기대 예시를 포함한다.
- 간헐적 empty content, truncation, 429, schema invalid를 별도 계측하며 raw payload는 기록하지 않는다.
- context caching은 기본 활성화되고 cache off가 확인되지 않았으므로 ACTIVE KB 최소 청크만 전달한다.
- 모든 호출에 thinking disabled와 `max_tokens=1024`를 강제한다. client/route 값으로 덮어쓸 수 없다.
- app 외부 호출 concurrency는 1, 논리 요청당 최초 1회+재시도 최대 1회다. HTTP client/SDK hidden retry는 0이다.
- 한 명시적 process run에서 timeout·연결 실패·429·empty·truncated·schema-invalid와 재시도를 포함한 실제 outbound attempt 총 30을 네트워크 전 원자적으로 예약한다. cap 30이면 새 전송·재시도는 0이다.
- health/readiness/startup preflight는 provider를 호출하지 않는다. 결제·잔액 조회·자동 충전·counter reset endpoint를 구현하지 않는다.
- cap/429/잔액 부족은 그 자체로 503이 아니며 ACTIVE KB template SUCCESS 또는 정책 FALLBACK으로 전환한다.
- 출처명·URL·확인일은 provider 결과를 버리고 서버가 KB metadata로 결합한다.

## 버전

prompt set의 모든 변경은 다음을 기록한다.

- prompt version
- model/provider
- evaluation set version
- before/after KPI
- known regression
- rollback template

공식 모델·가격·cache·약관 기준일은 2026-07-14이며 구현 시작과 데모 전에 재확인한다.
