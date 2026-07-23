# MVP-001 4일 local/private 핵심 개선 루프 발견 감사

- 감사 시각: 2026-07-22T02:10:11+09:00
- 기준 commit: `9044ddb` (`origin/main`, PR #5 merge 포함)
- 목표 시각: 2026-07-25 토요일 local/private 데모 gate
- 결정: Q-MVP-001=A
- 성격: 현재 코드·계약·데이터와 최종 source-of-truth의 차이 감사. `legacy/`는 근거로 사용하지 않았다.

## 1. 결론

최종 제품 범위인 4개 분야, 20개 ACTIVE KB, `/`·`/chat`·`/admin`, 승인형 개선 루프,
표본 20개와 회귀 1개는 바꾸지 않는다. 7월 25일 목표는 이 중 **local/private에서 한 번
끝까지 작동하는 핵심 수직 흐름**을 먼저 완료하는 중간 마일스톤이다. 공개 배포·100명 부하·
자동 백업·DeepSeek 품질 튜닝·고급 UI는 7월 25일 인수 기준에서 제외하되 7월 31일 최종
백로그에서는 삭제하지 않는다.

현재 구현은 기반과 안전 경계는 강하지만 실제 시민·관리자 수직 흐름은 대부분 미구현이다.
가장 긴 critical path는 `협업 기준선 복구 → DATA-SEED-002 actual PASS → PII/chat 계약 →
chat 서비스/API → 실패 저장/admin → 20번째 ACTIVE 회귀`다.

## 2. 권위 기준과 실제 저장소 비교

| 영역 | 최종 기준 | 2026-07-22 실제 상태 | 7/25 조치 |
|---|---|---|---|
| Git/협업 | private single repo, frontend 역할 분리, PR/CI | PR #5는 `main`에 병합됨. PR #4는 `014`로 교정돼 head `37dfc8b`, 정확한 2파일, CLEAN/MERGEABLE와 hosted summaries green | Frontend collaborator/사용자가 정책에 따라 PR #4 병합 |
| 공식 데이터 | 승인된 20 ACTIVE KB, official/mock 분리 | PM 승인 projection은 19/3/10. `.1`은 immutable historical artifact, DB 공식 row 0 | DATA-SEED-002 `.2` actual PASS로 19건 반영. `KB-WASTE-03`은 개선 루프로 20번째 전환 |
| PII | 외부·DB 전 원문 차단, unresolved fail closed | pure redaction core와 동결 fixture 완료. consumer 없음 | `PRIVACY_UNRESOLVED` HTTP 200 no-text consumer와 raw-sentinel spy 동결 |
| 시민 chat | 분류→ACTIVE 검색→근거 gate→구조화 응답/폴백 | wire model/fixture만 있고 classifier, retriever, service, route 없음 | deterministic lexical/template 경로와 `/api/v1/chat` 구현. 실제 시민 DeepSeek 0 |
| 대화 기억 | 현재 탭 transcript + 15분 signed context | ADR/계약만 있고 signer/verifier 없음 | HMAC token 구현; 질문·답변·PII·URL·공식 사실 claim 0, 서버 저장 0 |
| 이벤트/실패 | 원문 0, OUT_OF_SCOPE/FOLLOWUP 실패 row 0 | DB function/repository write 경계 존재, route/service 미연결 | chat service에서 matrix를 연결하고 30일 masked text 정책 유지 |
| 관리자 | 운영자 작성, 다른 승인자 승인, atomic ACTIVE | DB capability와 self-approval 차단 존재. read API와 `/admin` UI 없음 | local/private 최소 list/detail/reason/candidate/submit/review와 역할 전환 UI |
| Frontend | 실제 `/chat`, `/admin`, 390/430, keyboard/contrast | `/`와 정적 `/chat`만 존재. typed API client 없음 | 계약 fixture UI를 먼저 병렬 구현하고 backend freeze 뒤 실제 fetch 연결 |
| 평가 | 표본 20, 회귀 1, 보안 gate, 데모 | 20개 CSV와 일부 정적 E2E 존재. 제품 수직 E2E 없음 | 20개 결과표, 승인 전후 1개, secret/privacy/ACTIVE gate, local rehearsal |
| 성능·배포 | 최종 P1 100명·조건부 공개 배포 | 미실행, public security `00700` 보류 | 7/25 이후. local smoke 외 production-ready 주장 금지 |

## 3. 즉시 발견된 통합 결함

1. `scripts/check_collaboration_scope.py`와 `scripts/tests/test_collaboration_scope.py`의 정책·fixture
   문자열이 공식 staging 검사에서 `RUNTIME_STAGING_REFERENCE`로 오탐된다. 이 때문에 canonical
   DATA-001 validation과 `.1` release verification이 실패한다. PR #5 통합 후 선행 복구 대상이다.
2. DATA-SEED-002 계획은 `jsonschema`가 existing이라고 가정하지만 `apps/api/pyproject.toml`과 현재
   frozen 환경에는 선언돼 있지 않다. 새 dependency를 추가하지 않고 저장소의 기존 strict schema
   validator를 재사용하도록 테스트를 정리한다.
3. 격리 worktree의 `.tools/`는 project root와 공유되지 않으므로 official offline runner가 PATH의
   `uv`를 찾지 못했다. root의 pinned `uv 0.11.28`을 PATH에 연결하면 preflight는 통과한다. DATA actual
   전에 exact patched Supabase runtime은 별도로 bootstrap/검증해야 한다.
4. public OpenAPI는 chat/admin 경로를 선언하지만 실제 FastAPI는 `/health`, `/ready`만 등록한다.
5. admin list/create/review 성공 response가 typed client를 만들기에 충분히 구체적이지 않다.

## 4. Q-MVP-001이 확정한 실행 해석

- DATA-SEED-002의 기존 명세·계획은 Q-MVP-001=A와 `즉시 실행` 지시로 승인 상태로 전환한다.
- PII consumer는 D-045를 그대로 구현한다. `PRIVACY_UNRESOLVED`는 시민 응답 계약에는 추가하지만
  실패 질문 row와 후보를 만들지 않는다. 7/25 local MVP에서는 이 outcome을 DB에 영속화하지 않아
  예약된 public-hardening `00700` 순서를 침범하지 않는다.
- chat의 기본 합성은 deterministic server template다. DeepSeek adapter/tuning은 critical path가 아니며
  실제 시민 질문은 계속 외부로 보내지 않는다.
- 최소 접근성, source server binding, ACTIVE-only, self-approval 차단, raw text 0은 일정 때문에
  완화할 수 없는 gate다.
- `/admin` 인증은 local/private demo actor 선택이며 실제 인증/RBAC이라고 표현하지 않는다.

## 5. 아직 사람에게 남는 일

- 팀원 계정의 MFA/recovery 확인과 corrected PR #4 병합은 팀원/사용자 계정 행위다.
- 후보의 공식 근거와 최종 20번째 ACTIVE 전환은 PM 역할의 사람 검수로 표시한다. local demo fixture에서
  `PM-LOCAL-001`은 기존 확정 reviewer identity를 사용하되 작성자와 동일하면 안 된다.
- public 배포, 실제 시민 DeepSeek, remote DB, `00700`, 100명 결과의 실서비스 해석은 이 승인에 포함되지 않는다.

## 6. 즉시 착수 순서

1. 협업 오탐 회귀와 PR #4 note-ID 충돌을 복구한다.
2. DATA-SEED-002를 TDD로 실행하고 local disposable DB actual PASS를 확보한다.
3. PII/chat public response 계약과 template chat core를 동결한다.
4. Frontend fixture lane을 병렬화하고 backend API가 고정되면 실제 연동한다.
5. event/admin/20번째 ACTIVE 회귀를 한 transaction/state-machine 흐름으로 완주한다.
6. 표본·보안·접근성·데모 gate를 실행하고 미실행 P1을 명확히 분리한다.
