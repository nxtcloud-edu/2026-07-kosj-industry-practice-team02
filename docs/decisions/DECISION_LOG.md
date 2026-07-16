# Decision Log

| ID | 날짜 | 결정 | 상태 | 근거/ADR | 변경 승인자 |
|---|---|---|---|---|---|
| D-001 | 2026-07-13 | 시민용 AI + 관리자 승인형 개선 루프 | Confirmed | TEAM_DECISIONS | 사용자 |
| D-002 | 2026-07-13 | 4개 민원 분야, 공식 KB 20건 | Confirmed | PROJECT_PLAN | 사용자 |
| D-003 | 2026-07-13 | 실제 페이지 3개, 탭/모달 통합 | Confirmed | PROJECT_PLAN | 사용자 |
| D-004 | 2026-07-13 | OUT_OF_SCOPE는 후보 불가·텍스트 미저장 | Confirmed | PRIVACY/APPROVAL | 사용자 |
| D-005 | 2026-07-13 | LLM 공급자 미정, provider adapter | Superseded by D-016/D-017 for provider and data boundary; adapter remains | ADR-0005 | 사용자 |
| D-006 | 2026-07-13 | Vercel+Render+Supabase 권장 | Confirmed recommendation | ADR-0002 | 사용자 |
| D-007 | 2026-07-13 | Codex는 감사·인터뷰·계획 후 구현 | Confirmed | AGENTS | 사용자 |
| D-008 | 2026-07-13 | 모든 요청마다 구현 노트 의무 | Confirmed | AGENTS | 사용자 |
| D-009 | 2026-07-14 | 원본 원격 없이 이 workspace를 새 독립 Git 저장소로 시작하고 기본 브랜치를 `main`으로 사용 | Confirmed; execution deferred until plan approval | Q-REPO-001, ADR-0002 | 사용자 |
| D-010 | 2026-07-14 | 개발 기준을 Node 24.x+pnpm, Python 3.12+uv로 통일 | Confirmed; exact tool patch versions deferred to scaffold | Q-DEV-001, ADR-0002 | 사용자 |
| D-011 | 2026-07-14 | 공식 KB·기관 데이터는 AI/Data·Backend가 작성하고 PM이 전수 승인하며 2026-07-20 완료 목표 | Confirmed | Q-DATA-001, PROJECT_PLAN | 사용자 |
| D-012 | 2026-07-14 | 실제 LLM provider/model을 사용하는 목표 | Superseded by D-016/D-017/D-023 for provider, data boundary, and exact model/cap | Q-LLM-001, ADR-0005 | 사용자 |
| D-013 | 2026-07-14 | 초기 환경은 local-first, 외부 인프라 예산 0원; 공개 배포는 별도 승인 | Confirmed for local; public deployment deferred | Q-DEP-001, ADR-0002 | 사용자 |
| D-014 | 2026-07-14 | 초기 `/admin`과 관리자 API는 local/private 전용; 공개 시 서버측 gate 없이는 비활성 | Confirmed | Q-SEC-001, ADR-0007 | 사용자 |
| D-015 | 2026-07-14 | 실패 질문은 30일 후 `masked_question`만 NULL 파기하고 비텍스트 메타데이터·후보 연결 유지 | Confirmed | Q-PRIV-001, ADR-0004 | 사용자 |
| D-016 | 2026-07-14 | 실제 LLM 공급자는 사용자가 보유한 기존 DeepSeek API 잔액을 사용하고 새 충전·자동 충전은 하지 않음 | Confirmed; exact runtime guard completed by D-023 | Q-LLM-002, ADR-0005 | 사용자 |
| D-017 | 2026-07-14 | DeepSeek 호스팅 호출은 local/private의 서버 검증 합성 fixture에만 허용하고 실제 시민·PII·민감정보·공개 운영에는 사용하지 않음 | Confirmed for synthetic demo; real-user/public use prohibited pending new review | Q-LLM-003, ADR-0005 | 사용자 |
| D-018 | 2026-07-14 | DB 실행 권위는 Supabase CLI 버전 SQL 마이그레이션으로 관리 | Confirmed for local; install and migration creation deferred until plan approval | Q-DB-001, ADR-0008 | 사용자 |
| D-019 | 2026-07-14 | 이름·상세주소는 재현율 우선 보수적 마스킹; 성공률 저하가 입증돼도 정밀도 우선 전환은 자동화하지 않고 재승인 | Confirmed with review gate | Q-PRIV-002, ADR-0004 | 사용자 |
| D-020 | 2026-07-14 | 정책 응답은 HTTP 200, 안전 대체가 없는 시스템 불능은 HTTP 503 `SERVICE_UNAVAILABLE` envelope | Confirmed | Q-API-001, ADR-0009 | 사용자 |
| D-021 | 2026-07-14 | 현재는 local Git+수동 검증 gate만 사용하고 원격 저장소·CI는 사용자가 다시 요청할 때 결정 | Confirmed for current phase; remote/CI deferred | Q-CI-001, ADR-0002 | 사용자 |
| D-022 | 2026-07-14 | 대화 기억 방식은 화면 기록·문맥 전달·서버 저장을 구분해 설명받은 뒤 결정 | Superseded by D-024 | Q-CHAT-001 | 사용자 |
| D-023 | 2026-07-14 | DeepSeek는 정확히 `deepseek-v4-flash`, thinking off, max output 1024, 동시성 1, 요청당 재시도 최대 1회, run당 외부 전송 시도 총 30회로 제한 | Confirmed for local/private synthetic evaluation; no top-up, cap/장애 시 template 또는 정책 폴백 | Q-LLM-004, ADR-0005 | 사용자 |
| D-024 | 2026-07-14 | 화면 대화는 현재 탭 메모리에만 두고 서버 세션·raw transcript를 저장하지 않으며 15분 서명형 client-carried context token을 사용 | Confirmed; API 2.0.0-draft breaking change, token is not auth and contains no free text/PII/official facts | Q-CHAT-001, ADR-0010 | 사용자 |
| D-025 | 2026-07-16 | 승인·보관·ACTIVE 공식 검색·권한 규칙은 DB function/trigger/RLS/GRANT와 백엔드 검증에서 이중 강제 | Confirmed; written spec and execution plan approved, implementation in progress; remote/public scope unchanged | Q-DB-002, ADR-0011, DB-001 plan | 사용자 |
| D-026 | 2026-07-16 | PostgreSQL 17 non-superuser migration runner를 유지하고 role replay는 허용된 속성만 재적용한 뒤 위험 속성·membership·setting을 catalog 검증해 fail closed | Confirmed; no privileged auto-downgrade/bootstrap; Task 5 accepted | Q-SEC-002, ADR-0011, IMP-20260716-009 | 사용자 |
| D-027 | 2026-07-16 | 별도 backend-only 사유 확인 capability로 `NEW → REASON_CONFIRMED`를 원자 처리하고 event의 최초 자동 사유는 불변, failure 사유·적격성만 정정; 후보는 확인 완료 IG만 허용하며 승인 comment도 필수 | Confirmed; internal DB/repository refinement, existing OpenAPI wire unchanged; Task 6 unblocked | Q-WF-001, ADR-0011, IMP-20260716-009 | 사용자 |

새 결정은 기존 값을 덮어쓰지 않고 새 행과 ADR/노트 링크를 추가한다.
