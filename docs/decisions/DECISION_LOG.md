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
| D-018 | 2026-07-14 | DB 실행 권위는 Supabase CLI 버전 SQL 마이그레이션으로 관리 | Confirmed; six local forward/compensation files and patched-only local runner verified, DB-001 promoted to `0.3.0-local`; remote/public remains separately blocked | Q-DB-001, ADR-0008, DB-001 verified report/handoff | 사용자 |
| D-019 | 2026-07-14 | 이름·상세주소는 재현율 우선 보수적 마스킹; 성공률 저하가 입증돼도 정밀도 우선 전환은 자동화하지 않고 재승인 | Confirmed with review gate | Q-PRIV-002, ADR-0004 | 사용자 |
| D-020 | 2026-07-14 | 정책 응답은 HTTP 200, 안전 대체가 없는 시스템 불능은 HTTP 503 `SERVICE_UNAVAILABLE` envelope | Confirmed | Q-API-001, ADR-0009 | 사용자 |
| D-021 | 2026-07-14 | 현재는 local Git+수동 검증 gate만 사용하고 원격 저장소·CI는 사용자가 다시 요청할 때 결정 | Confirmed for current phase; remote/CI deferred | Q-CI-001, ADR-0002 | 사용자 |
| D-022 | 2026-07-14 | 대화 기억 방식은 화면 기록·문맥 전달·서버 저장을 구분해 설명받은 뒤 결정 | Superseded by D-024 | Q-CHAT-001 | 사용자 |
| D-023 | 2026-07-14 | DeepSeek는 정확히 `deepseek-v4-flash`, thinking off, max output 1024, 동시성 1, 요청당 재시도 최대 1회, run당 외부 전송 시도 총 30회로 제한 | Confirmed for local/private synthetic evaluation; no top-up, cap/장애 시 template 또는 정책 폴백 | Q-LLM-004, ADR-0005 | 사용자 |
| D-024 | 2026-07-14 | 화면 대화는 현재 탭 메모리에만 두고 서버 세션·raw transcript를 저장하지 않으며 15분 서명형 client-carried context token을 사용 | Confirmed; API 2.0.0-draft breaking change, token is not auth and contains no free text/PII/official facts | Q-CHAT-001, ADR-0010 | 사용자 |
| D-025 | 2026-07-16 | 승인·보관·ACTIVE 공식 검색·권한 규칙은 DB function/trigger/RLS/GRANT와 백엔드 검증에서 이중 강제 | Confirmed; local implementation and fresh disposable baseline verified; A-021 separately blocks public release | Q-DB-002, ADR-0011, DB-001 plan/verified report/handoff | 사용자 |
| D-026 | 2026-07-16 | PostgreSQL 17 non-superuser migration runner를 유지하고 role replay는 허용된 속성만 재적용한 뒤 위험 속성·membership·setting을 catalog 검증해 fail closed | Confirmed; no privileged auto-downgrade/bootstrap; Task 5 accepted | Q-SEC-002, ADR-0011, IMP-20260716-009 | 사용자 |
| D-027 | 2026-07-16 | 별도 backend-only 사유 확인 capability로 `NEW → REASON_CONFIRMED`를 원자 처리하고 event의 최초 자동 사유는 불변, failure 사유·적격성만 정정; 후보는 확인 완료 IG만 허용하며 승인 comment도 필수 | Confirmed; internal DB/repository refinement, existing OpenAPI wire unchanged; Task 6 unblocked | Q-WF-001, ADR-0011, IMP-20260716-009 | 사용자 |
| D-028 | 2026-07-17 | 적용된 `00100`~`00500`은 불변으로 두고 새 `00600`에서 `app_private.validate_active_kb_question()` 하나만 제한된 SECURITY DEFINER로 전환; schema owner·고정 `search_path=pg_catalog, pg_temp`(임시 스키마 마지막)·직접 EXECUTE revoke를 재확인하고 backend private schema/table grant와 repository/admin-DSN 우회는 금지 | Confirmed by the user's continue instruction immediately after recommendation A; user did not literally type `A`; implemented/verified by `5266abc`, `04a944f`, `228d8cb`; full pgTAP 282 and integration 8/8 PASS; API/data/dependency/remote/readiness unchanged; A-021 remains a public-release blocker | Q-DB-003, ADR-0012, DB-001-T9A plan, IMP-20260717-005/006 | 사용자 |
| D-029 | 2026-07-17 | Q-SEC-004=A: Docker Desktop의 향후 HostIP 미지정 publish 기본값을 `default-local-port-binding`으로 바꾸고 완전 재시작한 뒤 actual binding을 검증 | Confirmed and applied; IPv4는 `127.0.0.1`이 됐지만 actual resolved binding에 IPv6 wildcard `::`가 함께 남아 exact local gate 실패. explicit `127.0.0.1` probe는 단일 loopback. 설정은 유지하되 DB-001 완료/버전 승격에는 사용하지 않고 A-023/Q-SEC-005로 후속 결정 | Q-SEC-004, A-022, IMP-20260717-008 | 사용자 |
| D-030 | 2026-07-17 | Q-SEC-005=A: Docker Desktop `PortBindingBehavior=local-only-port-binding`을 적용·재시작하고 HostIP 생략 actual binding을 먼저 검증 | Confirmed and applied; HostIP 생략 probe는 다시 `127.0.0.1`+IPv6 wildcard `::`로 exact gate 실패, explicit `127.0.0.1` control은 단일 loopback. 두 probe 제거·container 0·DB mutation 0. 설정은 유지하되 완료 근거로 사용하지 않고 A-024/Q-SEC-006으로 후속 결정 | Q-SEC-005, A-023, IMP-20260717-009 | 사용자 |
| D-031 | 2026-07-17 | Q-SEC-006=A: official Supabase CLI v2.109.1 exact source에서 local DB start HostIP만 `127.0.0.1`로 명시하는 project-local patched CLI를 source/tag/commit·patch·Go 1.25.11·binary SHA-256과 함께 pin | Implemented and verified locally: source/patch/runtime hashes, patched-only runner, bounded child process trees (`73f300b`), exact one `127.0.0.1:54322`, fresh 282/8/8/replay and cleanup 0/0; code review 0/0/0, public/API/migration/data/dependency 변화 없음 | Q-SEC-006, A-024, ADR-0013, patched plan, DB-001 verified report | 사용자 |
| D-032 | 2026-07-18 | Q-TOOL-001=A: patched CLI의 두 Windows checkout만 `.tools/s/a`와 `.tools/s/b`로 줄이고 checkout 전 absolute path budget을 fail-closed 검증한다. 기존 `.tools/supabase-source/...` partial tree는 자동 삭제하지 않는다. | Implemented and verified locally after user `수정 계획 승인, 구현 시작`; short-root/path-budget/legacy deny-only TDD와 reproducible build 통과. 새 dependency·native delete·global Git/Docker/WSL·API/DB/data/deployment 변화 없음 | Q-TOOL-001, A-025, ADR-0014, IMP-20260718-002, patched plan | 사용자 |
| D-033 | 2026-07-18 | Q-DATA-002=A: 공식 데이터 canonical authoring은 `data/staging/data-001/<draft-version>/`의 KB·기관·매핑 JSON과 hash-bound PM approval manifest로 관리하고, 승인 레코드만 별도 DATA-SEED-001에서 immutable official release로 승격 | Specification approved by user `명세 승인`; AI scope complete / Review (PM pending) with DRAFT KB 20·office 3·mapping 12 and validator PASS. Remediation 3 reproduced no deterministic `TEST-ROOT` defect (direct 171 tests/511.715s and fresh full verify PASS). 초기 release 후보는 19 KB+3 office+10 mapping, KB-WASTE-03은 REG-001 전까지 보류. official release/seed/DB/API/dependency는 변경 0 | Q-DATA-002, A-026, ADR-0015, DATA-001 spec/plan, IMP-20260718-007 | 사용자 |
| D-034 | 2026-07-19 | 사용자의 `pm 검수 다 완료` 발화를 PM 검수 완료 진술로 접수하되, canonical manifest의 reviewer metadata와 35건 decision/comment가 없으므로 AI 권고안을 사람의 승인 증거로 자동 변환하지 않는다 | Confirmed attestation intake; DATA-001 approval materialization은 Q-DATA-003/A-027, official release/seed는 Q-SEED-001/A-028까지 blocked. 제품 코드·DB·official data 변경 없음 | POST_PM_NEXT_VERTICAL_SLICE_AUDIT, A-027/A-028, IMP-20260719-003 | 사용자 진술 + 비협상 승인 규칙 |
| D-035 | 2026-07-19 | Q-DATA-003=A: PM reviewer ID `PM-LOCAL-001`, DATA-001의 35개 current recommendation을 최종 disposition으로 채택하고 이 답변 처리 시각 `2026-07-19T02:06:19+09:00`을 final confirmation 시각으로 사용 | Confirmed/materialized/verified: canonical state APPROVED, 19/3/10 projection, 63 tests+validator+hash/final review PASS. 이 결정은 DATA-001 승인 증거만 확정하며 official release/seed/ACTIVE/DB를 승인하지 않음 | Q-DATA-003, A-027, DATA-001 plan, IMP-20260719-004 | 사용자/PM |
| D-036 | 2026-07-19 | Q-SEED-001=A: approved record를 immutable filesystem release와 기존 schema용 deterministic transactional seed로 승격하고, compensation은 참조 row 없는 빈 disposable local DB에만 허용 | Architecture confirmed; ADR-0016 accepted. Initial `0.1.0-initial.1`/19·3·10 written spec은 3차 독립 review 0/0/0까지 완료됐으며 사용자 `명세 승인`과 후속 plan 승인 전 구현 금지 | Q-SEED-001, A-028, ADR-0016, DATA-SEED design, IMP-20260719-006 | 사용자 |
| D-037 | 2026-07-19 | Q-WEB-001=A: 실제 chat pipeline 전에 입력·저장·API 호출이 없는 접근 가능한 정적 `/chat` 준비 화면을 만들고 홈 CTA를 연결 | Confirmed for local/private; 기존 PLAN-001과 사용자의 연속 구현 지시 아래 WEB-HOME narrow plan/TDD 실행 허용. API/DB/LLM/data/dependency/public 배포 변경 없음 | Q-WEB-001, A-029, PLAN-001, WEB-HOME plan | 사용자 |

새 결정은 기존 값을 덮어쓰지 않고 새 행과 ADR/노트 링크를 추가한다.
Q-SEC-004/A-022와 Q-SEC-005/A-023은 각각 D-029/D-030으로 결정됐지만 실제 보정이 불충분했다.
A-024/Q-SEC-006은 D-031/ADR-0013, A-025/Q-TOOL-001은 D-032/ADR-0014로 해결됐고 사용자의
수정 계획 승인 뒤 runtime/full gate까지 local에서 구현·검증됐다. Q-DATA-002/A-026은
D-033/ADR-0015로 해결되고 DRAFT 20/3/12를 거쳐 D-035의 exact reviewer/disposition/time과
canonical APPROVED 19/3/10 evidence까지 materialize·검증됐다. D-036은 DATA-SEED architecture만
확정했으며 written spec/plan gate를 유지한다. D-037은 static WEB-HOME/chat shell 실행을 허용한다.
DB-001은 disposable `0.3.0-local`로 완료됐지만 A-021/Q-SEC-003 기본값 B는 public release를
계속 차단한다.
