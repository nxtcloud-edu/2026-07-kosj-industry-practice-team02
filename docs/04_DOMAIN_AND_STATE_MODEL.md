# 도메인·상태 모델

## 핵심 enum

### Intent

- `MOVE_IN_RESIDENT_REGISTRATION`
- `CERTIFICATE_ISSUANCE`
- `BULKY_WASTE`
- `LOCAL_TAX_GENERAL`
- `OUT_OF_SCOPE`
- `UNKNOWN`

### AnswerStatus

- `SUCCESS`
- `FOLLOWUP`
- `FALLBACK`
- `SYSTEM_ERROR`

### FallbackReason

- `INSUFFICIENT_GROUNDING`
- `PERSONAL_LOOKUP`
- `LEGAL_JUDGMENT`
- `OUT_OF_SCOPE`

### CandidateStatus

- `NEW`
- `REASON_CONFIRMED`
- `DRAFTED`
- `PENDING_APPROVAL`
- `APPROVED`
- `REJECTED`

### KBStatus

- `DRAFT`
- `PENDING`
- `ACTIVE`
- `REJECTED`
- `RETIRED`

### DataOrigin

- `OFFICIAL`
- `MOCK`

### AdminRole

- `OPERATOR`
- `APPROVER`

## 불변조건

1. `SUCCESS`는 source 1개 이상이 필요하다.
2. source URL/title/verified date는 DB 메타데이터에서 온다.
3. `FOLLOWUP`에는 fallback_reason이 없다.
4. `FALLBACK`에는 정확히 하나의 fallback_reason이 있다.
5. `OUT_OF_SCOPE` event에는 question text가 없다.
6. candidate_eligible은 `INSUFFICIENT_GROUNDING`에서만 true다.
7. ACTIVE KB는 승인자와 승인시각이 필요하다.
8. 작성자와 승인자는 같을 수 없다.
9. audit log는 질문/답변 전문을 포함하지 않는다.
10. `SYSTEM_ERROR`는 민원 폴백 통계와 별도다.
11. `FALLBACK` 응답의 `context_token`은 항상 NULL이다.
12. 대화 token은 인증·공식 사실·ACTIVE 상태 근거가 아니며 raw/free text를 포함하지 않는다.
13. 새 실패 행은 `NEW`에서 부모 event의 최초 자동 intent/reason과 일치한다.
14. `NEW → REASON_CONFIRMED`에서는 부모 event reason을 바꾸지 않고 failure reason과 `candidate_eligible`만 운영자 확인값으로 갱신한다.
15. 후보 작성은 failure가 `REASON_CONFIRMED`, `INSUFFICIENT_GROUNDING`, `candidate_eligible=true`일 때만 가능하다.
16. 사유 확인은 `FAILED_QUESTION_REASON_CONFIRMED`/`FAILED_QUESTION` metadata audit 한 건과 같은 transaction이다.
17. 승인과 반려는 모두 비어 있지 않은 `review_comment`를 후보와 metadata audit에 저장한다.
18. 시민 read는 `ACTIVE + OFFICIAL` KB와 `OFFICIAL` 기관만 반환한다.
19. `kb_documents`, `offices`, `kb_candidates`는 default 없는 `data_origin`을 필수로 가진다.
20. 기관의 `is_official`은 직접 입력값이 아니라 `data_origin = OFFICIAL`의 generated 값이다.
21. `used_source_ids`는 중복 없는 비어 있지 않은 문자열 배열이며 `source_count`와 길이가 같다.
22. ACTIVE KB는 OFFICIAL provenance·승인자·승인시각·질문 예시 1개 이상을 모두 충족한다.
23. 실패 질문은 정확히 30일 뒤 masked text만 NULL 파기하며 행·event/candidate FK는 유지한다.
24. 감사 action은 후보 생성/제출/승인/반려와 실패 사유 확인만 허용하고 action별
    actor·target·old/new status·changed field shape를 DB check로 고정한다.

현재 실행 shape는 `0.4.0-local`의 7 enum·8 table이다. 9개 timestamp migration과 역순
compensation, trigger/capability, forced RLS, pgTAP 9 files/356 assertions 및 실제 backend
integration 8/8로 table-local 조건과 cross-row/transaction 조건을 이중 검증한다. 논리
projection만으로 정책을 강제했다고 판단하지 않는다.

## 실패 사유와 후보 상태 전이

```text
자동 분류 event(reason 불변)
→ failed question NEW(event와 reason 일치)
→ OPERATOR confirm/correct
→ failed question REASON_CONFIRMED(failure reason·candidate_eligible 재계산)
→ INSUFFICIENT_GROUNDING+eligible만 candidate DRAFTED
→ PENDING_APPROVAL
→ APPROVED 또는 REJECTED
```

동시 confirmation/candidate creation/review는 대상 행 잠금으로 직렬화하며 이미 전이된
상태의 두 번째 요청은 안정된 domain error로 거부한다.

## 사용자 표시 용어

| 내부 상태 | 시민 표시 |
|---|---|
| SUCCESS | 공식 근거 확인됨 |
| FOLLOWUP | 추가 확인이 필요해요 |
| INSUFFICIENT_GROUNDING | 공식 확인이 필요해요 |
| PERSONAL_LOOKUP | 본인 확인이 필요해요 |
| LEGAL_JUDGMENT | 담당자의 판단이 필요해요 |
| OUT_OF_SCOPE | 현재 지원 범위 밖이에요 |
| SYSTEM_ERROR | 잠시 후 다시 시도해 주세요 |
