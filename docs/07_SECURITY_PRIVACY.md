# 보안·개인정보 구현 기준

source-of-truth인 `docs/source-of-truth/PRIVACY_POLICY.md`를 요약한 엔지니어링 기준이다.

## 데이터 흐름

```text
raw request in memory
→ validate length/type
→ validate optional signed context; invalid/expired becomes no context
→ detect and redact PII
→ only redacted text reaches LLM/provider
→ answer returned
→ text-free event metadata saved
→ only eligible failure stores masked text
→ masked_question only is set to NULL after 30 days; metadata/candidate link remains
```

## 구현 요구

- raw question을 logger arguments, exception context, analytics, trace attributes에 넣지 않는다.
- request body logging middleware를 사용하지 않는다.
- 개발 환경의 print/debug도 같은 규칙을 따른다.
- 마스킹 로직은 공통 모듈로 두고 테스트한다.
- PII 감지 결과 자체도 과도한 민감정보를 만들지 않는다.
- `OUT_OF_SCOPE`는 masked text조차 저장하지 않는다.
- 실패 질문 텍스트 만료 작업은 행 DELETE가 아닌 멱등 NULL 파기이며 `text_purged_at`을 기록한다.
- 백업 복구 후 외부 요청을 받기 전에 만료 텍스트 파기를 재실행한다.
- admin candidate form에서 PII 감지 시 저장 차단 또는 명시적 정정 요구.
- service role key는 backend only.
- CORS는 명시적 origin allowlist.
- 실제 배포 전 인프라 제공사의 자동 로그와 데이터 보관 정책 확인.
- DeepSeek adapter는 서버 allowlist의 합성 fixture만 허용하고 클라이언트 `is_test`는 신뢰하지 않는다.
- 실제 시민·PII·민감정보·public 요청은 DeepSeek로 보내지 않으며 `user_id`에도 개인정보를 넣지 않는다.
- DeepSeek 기본 디스크 cache를 전제로 ACTIVE KB 최소 청크만 보내고 provider request/response body를 로깅하지 않는다.
- DeepSeek는 `deepseek-v4-flash`, thinking off, max 1024, concurrency 1, retry 최대 1, run당 실제 outbound attempt 총 30을 강제하고 cap/장애 시 template/policy fallback으로 전환한다.
- transcript와 15분 context token은 current-tab memory만 사용한다. token은 HMAC 무결성만 제공하므로 free text·PII·URL·공식 사실을 넣지 않고 DB/log/browser storage에 저장하지 않는다.

## 마스킹 범위

- 주민등록번호, 전화번호, 이메일
- 접수번호, 차량번호
- 계좌/카드, 인증번호
- 이름과 상세 주소: 재현율 우선 보수적 마스킹; 불확실하면 외부 호출 없이 안전 폴백
- 민감 복지·건강 문구: 외부 provider 전송 금지

## 인간 승인 필요

- 마스킹 범위 축소
- 보관기간 변경
- 외부 LLM 실제 시민/공개 사용으로 범위 확대
- DeepSeek model/call cap 변경과 잔액 추가 충전
- context token TTL·claim allowlist·저장 경계 변경
- admin public exposure
- RLS/auth 방식
- 실제 사용자 데이터 테스트
