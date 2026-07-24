# ADR-0004: 질문 텍스트와 이벤트 메타데이터 분리

- Status: Accepted
- Date: 2026-07-13 (updated 2026-07-20 by Q-PRIV-001, Q-PRIV-002, D-041, D-043, D-045)

## Decision

모든 요청은 질문 없는 interaction event를 저장할 수 있다. 개선 검토 대상 실패 질문만 `masked_question`을 생성 후 30일 보관한다. 만료 시 행을 삭제하지 않고 `masked_question`만 원자적으로 `NULL` 처리하며 `text_purged_at`을 기록한다. 실패 행의 비텍스트 메타데이터와 `kb_candidates.failed_question_id` 연결은 유지한다.

`OUT_OF_SCOPE`는 `failed_questions` 행을 만들지 않고 interaction event만 남긴다. 성공 질문과 FOLLOWUP 텍스트도 저장하지 않는다. KB 후보의 `representative_question`은 만료 대상 텍스트를 복사한 보관소가 아니며, 운영자가 일반화해 작성하고 PII 재검사를 통과해야 한다.

한국어 이름·상세주소는 재현율 우선의 보수적 마스킹을 적용한다. 개인정보 가능성이 있는데 안전하게 판정할 수 없으면 외부 provider를 호출하지 않고 안전 폴백한다. 동일한 승인 평가셋에서 답변 성공률 80% 미달이 측정되고 과잉 마스킹이 원인으로 입증되면 정밀도 우선 대안을 비교할 수 있지만, 개인정보 계약 변경과 인간 재승인 없이 자동 완화하지 않는다. 개인정보 마스킹률 100%와 raw 원문 미저장은 변경되지 않는다.

2026-07-20 addendum: 초기 runtime 마스커는 새 프로덕션 의존성 없는 결정론적 typed rule
engine으로 구현한다. 원문 값 없는 고정 토큰과 finding만 반환하며, 안전한 마스킹 문자열을
만들지 못하면 `masked_text`를 반환하지 않는다. 이 경우 provider 호출과 실패 질문 텍스트/row
생성은 금지하고 질문 없는 interaction event만 허용한다. 마스킹 성공도 실제 시민 질문의
DeepSeek 전송을 허용하지 않는다.

2026-07-20 D-043 addendum: 시민 입력의 “공식 대표번호” label은 신뢰하지 않는다. 질문에
포함된 모든 phone-shaped value를 마스킹하고, 공식 기관 연락처는 승인된 KB·기관 메타데이터를
서버가 결합한 카드에서만 제공한다. 이 결정은 one-argument pure core와 공식 데이터 계보의
분리를 유지하며, 번호 없는 “대표전화는 어디서 확인하나요?” 같은 문의 문구는 안전한 negative
표본으로 남긴다.

2026-07-20 D-045 addendum: 안전한 마스킹 문자열을 만들 수 없는 시민 요청은 시스템 장애나
기존 4개 행정-domain 폴백으로 가장하지 않는다. 후속 public consumer는 HTTP 200
`PRIVACY_UNRESOLVED` 정책 outcome으로 “개인정보를 빼거나 표현을 바꿔 다시 질문”하는 다음
행동을 제공한다. provider 호출, source/context/office, 질문 text 저장, `failed_questions` row와
후보 전환은 모두 금지하고 질문 없는 interaction metadata만 기록할 수 있다. 이 결정은 시민
동작을 확정하지만 현재 OpenAPI·JSON Schema·Pydantic·TypeScript·DB enum을 즉시 변경하지
않는다. consumer 명세에서 기존 migration 불변을 지키는 forward DB migration과 공개 계약을
함께 설계·승인한 뒤에만 route를 활성화한다.

## Consequences

운영 KPI·상태·후보 연결을 유지하면서 텍스트 노출 기간을 제한한다. 만료 후 관리자는 텍스트가 파기된 빈 상태를 보게 되며 자유로운 대화 재생은 제공하지 않는다. 백업 복구 직후에는 서비스 개방 전에 만료 텍스트 파기를 재실행해야 한다. 보수적 마스킹은 답변 의미를 일부 손상할 수 있으므로 PII 누락률과 답변 성공률을 같은 고정 평가셋에서 함께 측정한다. `PRIVACY_UNRESOLVED`는 별도 KPI reason이며 근거 부족 개선 수요에 합산하지 않는다.
