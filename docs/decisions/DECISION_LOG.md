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
| D-018 | 2026-07-14 | DB 실행 권위는 Supabase CLI 버전 SQL 마이그레이션으로 관리 | Confirmed; six local forward/compensation files implemented, but DB-001 completion/version promotion is blocked by A-024/Q-SEC-006 after both Docker Desktop remediations proved insufficient | Q-DB-001, ADR-0008, DB-001 candidate report/handoff | 사용자 |
| D-019 | 2026-07-14 | 이름·상세주소는 재현율 우선 보수적 마스킹; 성공률 저하가 입증돼도 정밀도 우선 전환은 자동화하지 않고 재승인 | Confirmed with review gate | Q-PRIV-002, ADR-0004 | 사용자 |
| D-020 | 2026-07-14 | 정책 응답은 HTTP 200, 안전 대체가 없는 시스템 불능은 HTTP 503 `SERVICE_UNAVAILABLE` envelope | Confirmed | Q-API-001, ADR-0009 | 사용자 |
| D-021 | 2026-07-14 | 현재는 local Git+수동 검증 gate만 사용하고 원격 저장소·CI는 사용자가 다시 요청할 때 결정 | Confirmed for current phase; remote/CI deferred | Q-CI-001, ADR-0002 | 사용자 |
| D-022 | 2026-07-14 | 대화 기억 방식은 화면 기록·문맥 전달·서버 저장을 구분해 설명받은 뒤 결정 | Superseded by D-024 | Q-CHAT-001 | 사용자 |
| D-023 | 2026-07-14 | DeepSeek는 정확히 `deepseek-v4-flash`, thinking off, max output 1024, 동시성 1, 요청당 재시도 최대 1회, run당 외부 전송 시도 총 30회로 제한 | Confirmed for local/private synthetic evaluation; no top-up, cap/장애 시 template 또는 정책 폴백 | Q-LLM-004, ADR-0005 | 사용자 |
| D-024 | 2026-07-14 | 화면 대화는 현재 탭 메모리에만 두고 서버 세션·raw transcript를 저장하지 않으며 15분 서명형 client-carried context token을 사용 | Confirmed; API 2.0.0-draft breaking change, token is not auth and contains no free text/PII/official facts | Q-CHAT-001, ADR-0010 | 사용자 |
| D-025 | 2026-07-16 | 승인·보관·ACTIVE 공식 검색·권한 규칙은 DB function/trigger/RLS/GRANT와 백엔드 검증에서 이중 강제 | Confirmed; implementation evidence exists but final local baseline/version is blocked by A-024/Q-SEC-006; A-021 separately blocks public release | Q-DB-002, ADR-0011, DB-001 plan/candidate report/handoff | 사용자 |
| D-026 | 2026-07-16 | PostgreSQL 17 non-superuser migration runner를 유지하고 role replay는 허용된 속성만 재적용한 뒤 위험 속성·membership·setting을 catalog 검증해 fail closed | Confirmed; no privileged auto-downgrade/bootstrap; Task 5 accepted | Q-SEC-002, ADR-0011, IMP-20260716-009 | 사용자 |
| D-027 | 2026-07-16 | 별도 backend-only 사유 확인 capability로 `NEW → REASON_CONFIRMED`를 원자 처리하고 event의 최초 자동 사유는 불변, failure 사유·적격성만 정정; 후보는 확인 완료 IG만 허용하며 승인 comment도 필수 | Confirmed; internal DB/repository refinement, existing OpenAPI wire unchanged; Task 6 unblocked | Q-WF-001, ADR-0011, IMP-20260716-009 | 사용자 |
| D-028 | 2026-07-17 | 적용된 `00100`~`00500`은 불변으로 두고 새 `00600`에서 `app_private.validate_active_kb_question()` 하나만 제한된 SECURITY DEFINER로 전환; schema owner·고정 `search_path=pg_catalog, pg_temp`(임시 스키마 마지막)·직접 EXECUTE revoke를 재확인하고 backend private schema/table grant와 repository/admin-DSN 우회는 금지 | Confirmed by the user's continue instruction immediately after recommendation A; user did not literally type `A`; implemented/verified by `5266abc`, `04a944f`, `228d8cb`; full pgTAP 282 and integration 8/8 PASS; API/data/dependency/remote/readiness unchanged; A-021 remains a public-release blocker | Q-DB-003, ADR-0012, DB-001-T9A plan, IMP-20260717-005/006 | 사용자 |
| D-029 | 2026-07-17 | Q-SEC-004=A: Docker Desktop의 향후 HostIP 미지정 publish 기본값을 `default-local-port-binding`으로 바꾸고 완전 재시작한 뒤 actual binding을 검증 | Confirmed and applied; IPv4는 `127.0.0.1`이 됐지만 actual resolved binding에 IPv6 wildcard `::`가 함께 남아 exact local gate 실패. explicit `127.0.0.1` probe는 단일 loopback. 설정은 유지하되 DB-001 완료/버전 승격에는 사용하지 않고 A-023/Q-SEC-005로 후속 결정 | Q-SEC-004, A-022, IMP-20260717-008 | 사용자 |
| D-030 | 2026-07-17 | Q-SEC-005=A: Docker Desktop `PortBindingBehavior=local-only-port-binding`을 적용·재시작하고 HostIP 생략 actual binding을 먼저 검증 | Confirmed and applied; HostIP 생략 probe는 다시 `127.0.0.1`+IPv6 wildcard `::`로 exact gate 실패, explicit `127.0.0.1` control은 단일 loopback. 두 probe 제거·container 0·DB mutation 0. 설정은 유지하되 완료 근거로 사용하지 않고 A-024/Q-SEC-006으로 후속 결정 | Q-SEC-005, A-023, IMP-20260717-009 | 사용자 |
| D-031 | 2026-07-17 | Q-SEC-006=A: official Supabase CLI v2.109.1 exact source에서 local DB start HostIP만 `127.0.0.1`로 명시하는 project-local patched CLI를 source/tag/commit·patch·Go 1.25.11·binary SHA-256과 함께 pin | Confirmed architecture decision, written specification and five-task execution plan approved; implementation started after the user's `계획 승인, 구현 시작`. stock CLI 보존, exact gate 유지, public/API/schema/data/dependency 변화 없음 | Q-SEC-006, A-024, ADR-0013, IMP-20260717-010/011 | 사용자 |

새 결정은 기존 값을 덮어쓰지 않고 새 행과 ADR/노트 링크를 추가한다.
Q-SEC-004/A-022와 Q-SEC-005/A-023은 각각 D-029/D-030으로 결정됐지만 실제 보정이 불충분했다. A-024/Q-SEC-006은 D-031/ADR-0013으로 결정되고 서면 설계가 승인됐으며, 실행계획 승인·구현·검증 gate 전에는 DB-001 local 완료를 선언하지 않는다.
