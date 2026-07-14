# UI 상태 매트릭스

## /chat

| 상태 | 필수 요소 | 금지 |
|---|---|---|
| Initial | 서비스 범위, 예시 질문, 지역 선택 | 미지원 기능 약속 |
| Loading | 진행 상태, 중복 전송 방지 | 무한 spinner |
| SUCCESS | intent, 구조화 카드, source, verified date | source 없는 답변 |
| FOLLOWUP | 4개 지원 분야 + 그 밖의 민원 | 미지원 개별 기능 선택지 |
| INSUFFICIENT_GROUNDING | 이유, 다음 행동, 공식 기관/경로 | 추정 값 |
| PERSONAL_LOOKUP | 본인 확인 필요, 공식 조회 경로 | 추가 PII 요구 |
| LEGAL_JUDGMENT | 일반 한계, 담당자/전문기관 | 자격/법적 단정 |
| OUT_OF_SCOPE | 지원 범위, 관련 공식 기관 가능 시 | 후보 개선 약속 |
| HTTP 503 `SERVICE_UNAVAILABLE` | 로딩 해제, 중복 방지 재시도, 대체 공식 경로 | 내부 stack/provider/error detail, 질문을 client log에 기록 |
| Empty office | 공식 정보 미확인 안내 | 가상 정보 생성 |

화면 transcript와 opaque context token은 current-tab 메모리에만 둔다. local/session storage, IndexedDB, cookie, URL, service-worker cache, analytics, client error log에 넣지 않으며 새로고침·탭 종료 시 초기 상태로 돌아간다. token은 화면에 표시하지 않는다.

## /admin

| 탭/상태 | 필수 요소 |
|---|---|
| Failed list | masked text, reason, eligibility, status, text expiry, filter; 만료 시 `보관기간 만료로 질문 텍스트가 삭제됨` 빈 상태 |
| Detail | source IDs, routed office, state action; raw text 없음 |
| Candidate draft | 사람 입력 답변/출처/확인일, PII 검사 |
| Pending approval | 작성자/승인자, 체크리스트, 자기 승인 차단 |
| Rejected | review comment, 재작성 경로 |
| Quality | EVENT/EVALUATION/MOCK 배지 |

`/admin` 상태는 초기 local/private 환경에만 제공한다. public 환경에서는 승인된 서버측 gate가 없으면 관리자 route를 표시하거나 호출하지 않는다.

## 접근성

- focus order와 skip link
- dialog name/description, escape/close, focus return
- 200% zoom에서 기능 손실 없음
- 상태 배지에 텍스트
- 클릭 영역 최소 크기 검토
