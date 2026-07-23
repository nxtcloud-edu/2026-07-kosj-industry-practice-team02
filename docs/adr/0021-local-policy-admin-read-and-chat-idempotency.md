# ADR-0021: local policy fallback, admin read와 durable chat idempotency

- 상태: Accepted
- 날짜: 2026-07-22
- 결정자: 사용자
- 관련 결정: Q-MVP-002=A, Q-DB-004=A, Q-API-002=A, D-059~D-061

## 맥락

표본 T-16~T-18의 개인 조회·법적 판단은 시민에게 이유를 구분해 알려야 하지만 지원 분야 intent로
저장하면 DB 의미가 왜곡된다. 또한 local `/admin`은 write capability만 있고 목록·상세 read가 없으며,
브라우저 재시도는 DB 기록 뒤 응답이 유실될 때 같은 실패 질문을 중복 생성할 수 있다.

## 결정

1. `PERSONAL_LOOKUP`과 `LEGAL_JUDGMENT`는 `intent=UNKNOWN`, 정확한 reason,
   `candidate_eligible=false`로 응답한다. local MVP에서는 질문 text, event, failed row와 후보를 만들지 않는다.
2. 적용된 `00100`~`00600`을 수정하지 않고 `20260722000650_local_admin_read_capabilities.sql`에서
   실패 질문·KB 후보 list/get 네 `app_api` read 함수를 추가한다. backend EXECUTE만 허용하고 private
   table grant와 public admin은 금지한다.
3. `20260722000660_chat_idempotency.sql`에서 UUID key, domain-separated HMAC request digest,
   correlation ID와 무관한 opaque claim token, 5분 lease, safe response JSON, 상태와 시각만 저장한다.
   원문·마스킹 질문, correlation request ID, IP, 기기 식별자는 저장하지 않는다.
4. `Idempotency-Key`는 optional UUID 공개 header다. correlation `request_id`는 매 HTTP 요청마다 새로
   만들고 idempotency identity와 결합하지 않는다.
5. 같은 key·같은 요청의 완료 record는 안전 응답을 replay한다. 같은 key·다른 digest는 입력을
   echo하지 않는 422, 살아 있는 lease의 처리 중 key는 retryable 503이다. 일반 미완료 오류는
   abandon하고, process crash·완료 기록 장애는 5분 lease 만료 뒤 새 claim token으로 재획득한다.
6. local MVP idempotency record의 논리 TTL은 정확히 24시간이다. local app은 startup과 실행 중
   최대 60초 간격으로 만료 행을 멱등 purge하며, purge 장애 시 readiness를 닫는다. 질문 텍스트는
   이 저장소에 들어가지 않는다. public 보관기간과 배포는 별도 인간 승인을 받는다.
7. `00650`, `00660` 각각 matching compensation과 pgTAP을 두고, 전체 compensation 순서는
   `00660 → 00650 → 00600 → 00500 → 00400 → 00300 → 00200 → 00100`이다.
8. 실제 admin 후보의 source URL은 userinfo·non-default port·fragment·민감 query key와 PII가 없어야 하며,
   이중 percent decode 뒤에도 다음 exact six host만 허용한다: `www.sejong.go.kr`, `plus.gov.kr`,
   `www.gov.kr`, `www.law.go.kr`, `www.wetax.go.kr`, `www.sjwaste.kr`.

## 결과와 위험 완화

- 정책 질문이 지원 가능한 행정 intent나 개선 후보로 오염되지 않는다.
- process restart와 응답 유실 뒤에도 logical retry 중복을 막을 수 있다.
- 독립 claim token과 짧은 lease로 correlation ID 저장과 24시간 `IN_PROGRESS` 고착을 함께 막는다.
- HMAC digest는 raw hash의 사전 대입 위험을 낮춘다. key, digest와 safe response만 저장하며 로그에
  request body를 남기지 않는다.
- admin read는 local/private server gate와 고정 demo actor allowlist 뒤에서만 사용한다.
- actual DB replay, rollback, 동시 claim, same-key conflict, purge, self-approval, ACTIVE-only test가
  통과하기 전에는 실제 개선 루프 완료를 주장하지 않는다. `00650`/`00660`의 local DB focused
  evidence와 DATA-SEED `.2` initial 19/3/10 PASS는 기록됐지만, 20번째 ACTIVE requery와 final
  application/demo gate는 별도다.

## 기각한 대안

- 정책 질문을 지원 intent로 저장: 운영 통계와 candidate eligibility 의미를 오염시킨다.
- process-memory dedupe: restart와 다중 worker에서 중복을 막지 못한다.
- raw payload 또는 평문 hash 저장: 개인정보·사전 대입 위험이 커진다.
- public admin 동시 활성화: 인증·RBAC·CORS·배포 승인을 우회하므로 금지한다.
- correlation request ID를 claim owner로 저장: 공개 추적 ID와 durable identity를 결합하므로 기각한다.

## Migration과 rollback

- forward: `00650` 뒤 `00660`; reserved public `00700`은 계속 미구현이다.
- rollback: local disposable DB에서 `00660`, `00650` 순서로 capability와 table을 제거한다.
- applied migration은 수정하지 않는다. shared/remote DB에는 실행하지 않는다.

## 재검토 조건

- public/remote DB 또는 public admin을 활성화할 때
- idempotency 보관기간, 암호 key rotation 또는 multi-region 동시성을 변경할 때
- 실제 시민 LLM/provider 경로를 활성화할 때
