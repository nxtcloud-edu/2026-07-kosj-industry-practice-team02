# 위험 레지스터

현재 local/private MVP의 제품·보안·데이터 위험만 유지한다. 협업 도구의 일회성 설정 이력은
평가 범위가 아니므로 이 레지스터에 포함하지 않는다.

| ID | 위험 | 가능성 | 영향 | 대응 | 확대 시 필요한 결정 |
|---|---|---:|---:|---|---|
| R-001 | 오래된 범위 재도입 | 중간 | 높음 | source-of-truth·RFP matrix·회귀 검사 | P2 범위 승인 |
| R-002 | 원문 질문·PII 로그 유출 | 중간 | 매우 높음 | 외부 호출 전 마스킹, 원문 DB/로그 미저장, secret scan | 개인정보 정책 승인 |
| R-003 | LLM 출처 환각 | 중간 | 매우 높음 | ACTIVE+OFFICIAL 검색, 서버 메타데이터 결합 | 근거 정책 변경 승인 |
| R-004 | 자기 승인 또는 MOCK 승격 | 중간 | 높음 | 작성자≠승인자, DB/API guard, OFFICIAL-only | 권한 정책 변경 승인 |
| R-005 | 공식 데이터 노후화 | 중간 | 높음 | source registry·확인일·immutable release·PM 승인 | 데이터 재승인 |
| R-006 | Upstage 비용·재시도 cap 우회 | 낮음 | 높음 | exact model pin, concurrency 1, hidden retry off, run cap 30 | 모델·비용 재승인 |
| R-007 | 보수적 마스킹의 의미 손실 | 중간 | 중간 | 품질 표본 분리, fail-closed, 완화 전 재승인 | 개인정보 완화 승인 |
| R-008 | local role selector를 인증으로 오해 | 중간 | 매우 높음 | public admin 비활성, local/private 표시 | 실제 인증/RBAC 설계 |
| R-009 | 30일 파기 정책을 오래된 backup이 우회 | 중간 | 높음 | dump 수명 제한, 복구 후 purge, restore drill | 실제 backup 정책 승인 |
| R-010 | local 증거를 public 운영 준비로 오해 | 중간 | 매우 높음 | `/ready` fail-closed, 배포·remote DB·100명 부하 별도 gate | 공개 배포 승인 |

평가 시점에 남아 있는 deferred 항목은 `docs/11_AMBIGUITY_REGISTER.md`에서 확인한다.
