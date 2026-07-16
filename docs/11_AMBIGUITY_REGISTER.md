# 모호성·미지의 영역 레지스터

Codex는 초기 감사에서 이 목록을 검증하고 추가/해결한다. 이미 결정된 것은 재질문하지 않는다.

| ID | 우선도 | 영역 | 현재 상태 | 질문/결정 | 기본 추천 |
|---|---|---|---|---|---|
| A-001 | A | LLM | Resolved | `deepseek-v4-flash`, thinking off, max 1024, concurrency 1, retry 1, run당 외부 전송 시도 30회; 합성 전용 | Q-LLM-004 / D-023 / ADR-0005 |
| A-002 | A | 개발환경 | Resolved | Node 24.x+pnpm, Python 3.12+uv; exact patch는 스캐폴딩에서 고정 | Q-DEV-001 / D-010 |
| A-003 | A | DB/배포 | Resolved for local; public deferred | Supabase CLI 버전 SQL migration과 Docker local stack 사용. 공개 DB·원격 push는 별도 승인 | Q-DB-001 / ADR-0008; 설치는 계획 승인 후 |
| A-004 | A | Admin 보안 | Resolved | local/private 전용, 공개 시 서버측 gate 없이는 관리자 경로 비활성 | Q-SEC-001 / ADR-0007 |
| A-005 | A | 데이터 | Resolved | AI/Data·Backend 작성, PM 승인, 2026-07-20 목표 | Q-DATA-001 / D-011 |
| A-006 | B | 마스킹 | Resolved with review gate | 이름·상세주소는 재현율 우선 보수적 감지. 과잉 마스킹이 성공률 80% 미달 원인으로 입증돼도 B 전환은 재승인 | Q-PRIV-002 / ADR-0004 |
| A-007 | B | 검색 | Defaulted / Deferred | MVP는 keyword/metadata만 사용하고 embedding flag는 off | ADR-0006; 품질 근거와 비용 승인 전 활성화 금지 |
| A-008 | B | CI | Resolved for current phase; deferred | local Git+수동 검증 gate. 원격/CI는 사용자가 다시 요청할 때 결정 | Q-CI-001 / D-021 |
| A-009 | B | 데모 | Defaulted / Deferred | 현재 완료 기준은 local live demo+재시작 runbook. 공개 URL·녹화본은 별도 발표/배포 승인 시 선택 | D-013/D-021 범위의 0원·local-first 기본값 |
| A-010 | C | UI | Defaultable | 디자인 시스템 세부 | 기존 아이디어노트 톤, 접근성 우선 |
| A-011 | C | 코드 | Defaultable | 모듈 명명·파일 분할 | framework conventions |
| A-012 | A | 저장소 | Resolved | 원본 원격 없음; 독립 Git repo와 `main` 사용 | Q-REPO-001 / D-009; init은 계획 승인 후 |
| A-013 | A | 개인정보 | Resolved | 30일 후 masked text만 파기, 행·비텍스트 메타·후보 FK 유지 | Q-PRIV-001 / ADR-0004 |
| A-014 | A | 대화 | Resolved | 현재 탭 메모리 transcript + 15분 서명형 client-carried context token; 서버 세션·raw transcript 없음 | Q-CHAT-001 / D-024 / ADR-0010 |
| A-015 | B | 오류 계약 | Resolved | 정책 응답은 200, 안전 대체가 없는 기술 장애는 503 `SERVICE_UNAVAILABLE` envelope | Q-API-001 / ADR-0009 |
| A-016 | B | 복구 | Defaulted for disposable local demo; public deferred | 재현 가능한 migration+승인 seed 우선, 파괴 변경/마일스톤 전 gitignored 수동 dump, local RPO 24h/RTO 60m, 30일 넘은 dump 삭제, 복구 후 개방 전 retention 재실행 | 실제/비재현 데이터·공개 운영 전 인간 재승인 |
| A-017 | B | DB 안전 경계 | Resolved | Q-DB-002: DB function/trigger/RLS/GRANT + 백엔드 이중 검증 | 2026-07-16 사용자 A 승인 / D-025 / ADR-0011 |

## 우선도 정의

- A: 구현 전 인간 결정 필요
- B: 빠른 인간 결정이 유리
- C: AI 기본값 가능, 기록 필요
- D: 내부 구현 판단

현재 인간 결정형 A/Blocker는 0개다. 구현은 최종 실행계획에 대한 사용자의 명시적 승인 전까지 시작하지 않는다.

## 질문 규칙

- 한 번에 7개 이하
- 옵션/장단점/추천/기본값/영향 포함
- 답변 후 결정 로그·ADR·계획·버전 갱신
