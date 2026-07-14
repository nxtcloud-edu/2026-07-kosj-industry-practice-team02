# 위험 레지스터

| ID | 위험 | 가능성 | 영향 | 조기 신호 | 대응 | 인간 승인 |
|---|---|---:|---:|---|---|---|
| R-001 | 오래된 범위 재도입 | 높음 | 높음 | 100문항/status/고급분석 코드 | authority/drift 검사 | 범위 변경 시 필요 |
| R-002 | 원문 질문 로그 유출 | 중간 | 매우 높음 | request body 로그 | 공통 redaction·테스트 | 정책 변경 필요 |
| R-003 | LLM 출처 환각 | 중간 | 매우 높음 | source field가 모델 출력 | 서버 metadata 결합 | 원칙 변경 필요 |
| R-004 | 자기 승인 | 중간 | 높음 | actor==created_by | DB/API guard | 권한 변경 필요 |
| R-005 | 가상 기관 정보 노출 | 높음 | 높음 | 044-000/가상주소 | 공식 데이터만 active | 데이터 예외 필요 |
| R-006 | DeepSeek 잔액 소진·cap 우회·숨은 재시도 | 중간 | 높음 | outbound attempt 30 초과·429/잔액 부족 | exact Flash pin·원자적 cap·hidden retry off·concurrency 1·disabled/template | model/cap 변경·충전 시 필요 |
| R-007 | 4주 범위 초과 | 높음 | 높음 | P2 작업 증가 | P0/P1 gate | 범위 변경 필요 |
| R-008 | mock KPI 오해 | 중간 | 높음 | 배지 없음 | 집계/표본/mock 구분 | 없음 |
| R-009 | 배포 무료 플랜 sleep | 중간 | 중간 | 첫 응답 지연 | warm-up/로컬 백업 | 계정 플랜 필요 |
| R-010 | KB 최신성 | 중간 | 높음 | 오래된 verified date | registry/review date | 공식 검수 필요 |
| R-011 | DeepSeek 기본 디스크 cache·불명확한 전체 보관/학습 조건 | 중간 | 매우 높음 | 실제 시민/PII payload 시도 | 합성 allowlist·보수적 마스킹·public/real-user 호출 차단 | 범위 확대 시 필요 |
| R-012 | 보수적 마스킹이 질문 의미를 과도하게 제거 | 중간 | 중간 | 고정 평가 성공률 80% 미달 | PII 100% 유지·원인분석·대안 비교 | 완화 시 필요 |
| R-013 | 원격/CI 부재로 단일 PC 손실·수동 gate 누락 | 중간 | 높음 | 백업 지연·검사 미기록 | local backup·명령 증거·handoff | Git 연결 시 필요 |
| R-014 | HMAC context token을 암호화·인증으로 오해하거나 브라우저에 영속 저장 | 중간 | 매우 높음 | free-text claim·localStorage·token 로그 | closed claims·15분 TTL·current-tab only·재검증 | TTL/claim/storage 변경 시 필요 |
| R-015 | 오래된 local backup이 30일 텍스트 파기 정책을 우회 | 중간 | 높음 | 30일 초과 dump 존재 | dump 30일 삭제·복구 전 purge·restore drill | 실제/원격 backup 전 필요 |
