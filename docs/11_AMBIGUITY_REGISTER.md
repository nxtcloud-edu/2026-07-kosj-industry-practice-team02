# 공개 평가 Snapshot — 보류 범위와 해석 경계

현재 local/private Week 3 MVP를 막는 미결정은 없습니다. 아래 항목은 결함이나 누락으로 숨기지
않고, 평가 범위 밖의 후속 결정으로 명시합니다.

| ID | 항목 | 현재 상태 | 이번 평가에서 확인 가능한 것 | 후속 승인 필요 |
|---|---|---|---|---|
| EVAL-001 | 공개 배포 | Deferred | local Web/API/DB 재현과 검증 | 계정·리전·도메인·CORS·로그·비용 |
| EVAL-002 | 실제 시민 provider 호출 | Prohibited | deterministic 시민 경로와 Upstage 합성 adapter | 개인정보·국외 처리·비용·품질 |
| EVAL-003 | public 관리자 인증 | Deferred | local demo actor와 작성자≠승인자 불변식 | SSO/RBAC·감사·세션 정책 |
| EVAL-004 | 운영 부하 | Deferred | 표본 20, 회귀, 제한적 local 테스트 | 100명 이상 목표·인프라·SLO |
| EVAL-005 | 자동 백업 | Deferred | migration·rollback·immutable seed 재현 | 암호화 backup·RPO/RTO·삭제 전파 |
| EVAL-006 | 고급 검색/UI | Deferred | keyword/metadata 검색, 필수 접근성·반응형 | embedding 비용·고급 분석·추가 UI |

## 확정된 안전 경계

- 근거가 부족하면 지어내지 않고 폴백합니다.
- 개인 조회·법적 판단·지원 범위 밖 질문은 개선 후보로 저장하지 않습니다.
- 질문 원문과 실제 개인정보를 DB·로그·오류 추적에 저장하지 않습니다.
- ACTIVE+OFFICIAL KB만 시민 검색에 사용합니다.
- local `/admin` 역할 전환은 인증이 아니며 public에서 활성화하지 않습니다.
- `/ready=200`과 ACTIVE 19→20은 disposable local/private 증거입니다.

상세 결정은 [`docs/source-of-truth/TEAM_DECISIONS.md`](source-of-truth/TEAM_DECISIONS.md),
아키텍처 선택은 [`docs/adr/`](adr/README.md), 평가 결과는
[`WEEK3_EVALUATION.md`](../WEEK3_EVALUATION.md)를 따릅니다.
