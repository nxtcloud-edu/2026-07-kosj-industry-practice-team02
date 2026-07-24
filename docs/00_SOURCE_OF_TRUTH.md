# Source of Truth와 문서 충돌 해결 규칙

## 1. 목적

이 문서는 공개 평가 snapshot에서 현재 구현·정책·계약을 해석하는 권위 순서를 고정한다.

## 2. 권위 순서

| 순위 | 위치 | 역할 |
|---:|---|---|
| 1 | `README.md`, `WEEK3_EVALUATION.md` | 평가 범위·실행·검증 결과 |
| 2 | `docs/source-of-truth/TEAM_DECISIONS.md` | 최종 제품·범위·기술·정책 결정 |
| 3 | `docs/source-of-truth/PRIVACY_POLICY.md`, `APPROVAL_POLICY.md`, `KB_GUIDE.md` | 영역별 필수 정책 |
| 4 | `docs/source-of-truth/PROJECT_PLAN.md`, `RFP_MATRIX.md` | 일정·요구사항 추적·인수 기준 |
| 5 | `contracts/`, `supabase/migrations/`, `data/official/` | 실행 계약·DB·공식 데이터 권위 |
| 6 | `docs/adr/` | 아키텍처 결정과 트레이드오프 |
| 7 | `docs/implementation-notes/` | 실제 구현 이력과 증거 |

상위 문서와 하위 문서가 충돌하면 상위 문서를 따른다. 다만 상위 문서가 모호하거나 현실 구현과 불일치하면 임의로 해석하지 않고 모호성 레지스터와 인터뷰를 사용한다.

## 3. 현재 절대 범위

- 4개 민원 분야
- 공식 KB 20건
- 페이지 3개
- 표본 질문 20개 + 회귀 1개
- 관리자 승인형 개선 루프
- 실제 GPS/상태조회/다국어/고급 분석은 P2

2026-07-25의 Q-MVP-001 local/private 마일스톤은 위 최종 범위를 줄이지 않는다. 19개 초기 ACTIVE를
실제 local DB에 반영한 뒤 관리자 개선 루프로 20번째 ACTIVE를 만들고 표본 20·회귀 1·보안·데모를
완주한 local/private MVP gate다. 외부 LLM actual 품질 평가, 고급 UI, 100명 부하, 자동 백업과 공개 배포는 이
마일스톤 뒤로 연기하지만 최종 P1 백로그에서 삭제하지 않는다. 상세 권위는 D-058/ADR-0020과
승인된 MVP-001 명세·계획이다.

2026-07-23 Q-LLM-005=A/D-065/ADR-0022는 DeepSeek 선택을 대체한다. 외부 공급자는 Upstage exact
`solar-pro3`이며, adapter·runner·strict JSON 검증은 offline으로 구현됐다. 실제 network/model-quality
평가는 local/private server-allowlisted 합성 `T-01`~`T-10`으로만 수행한다. 결정론적 시민 경로는 계속
기본이고 실제 시민/free-input/public/remote provider 사용은 선택지 B의 별도 승인 전 금지한다.

## 4. 변경 절차

제품 범위, 공개 계약, DB, 개인정보, 외부 공급자, 배포 아키텍처가 바뀌면:

1. 인간 승인
2. ADR 또는 결정 로그
3. source-of-truth 갱신
4. 계약/스키마/테스트 갱신
5. 버전 매니페스트 갱신
6. 구현 노트 기록

## 5. 공개 snapshot 경계

비권위 legacy와 내부 작업계획은 공개 snapshot에서 제외했다. 현재 동작은 실행 계약·migration·
공식 release·자동 테스트로 판정하며, 역사 문서의 과거 수치는 현재 검증 결과를 대체하지 않는다.
