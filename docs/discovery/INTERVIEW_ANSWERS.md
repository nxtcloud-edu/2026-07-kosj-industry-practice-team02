# Interview Answers

- Rule: 사용자 답변 원문은 그대로 보존하고, 해석은 별도 열에 기록한다.

## Batch 1 — 2026-07-14 KST

- Scope: `Q-REPO-001` ~ `Q-PRIV-001`

| Q-ID | Question summary | User answer | Interpretation | Decision/ADR | Status |
|---|---|---|---|---|---|
| Q-REPO-001 | 독립 Git 저장소 시작 여부 | `A — 원본 원격 저장소 없음` | 이 workspace를 새 독립 저장소로 만들고 `main`을 기본 브랜치로 사용한다. 실제 `git init`과 첫 브랜치는 최종 실행계획 승인 후 수행한다. | D-009 / ADR-0002 | Resolved |
| Q-DEV-001 | 런타임·패키지 관리자 | `A` | Node 24.x + pnpm, Python 3.12 + uv를 기준으로 한다. 도구의 정확한 patch 버전은 스캐폴딩 시 lock/manifest에 고정한다. 설치는 최종 계획 승인 후 수행한다. | D-010 / ADR-0002 | Resolved |
| Q-DATA-001 | 공식 KB·기관 데이터 책임과 기한 | `A — 작성 AI/Data·Backend, 승인 PM, 완료 목표 2026-07-20` | AI/Data와 Backend만 공식 데이터 작성자가 되고 PM이 전수 승인한다. 승인 전 데이터는 staging이며 시민 답변에 사용하지 않는다. | D-011 | Resolved |
| Q-LLM-001 | 첫 구현부터 실제 LLM 사용 여부 | `B` | 실제 provider/model을 사용하는 목표는 승인됐다. 단, 공급자·모델·키 책임자·데이터 보관·쿼터와 0원 예산의 양립 방식은 미정이므로 실제 연동은 계속 차단한다. | D-012 / ADR-0005 | Partially resolved — A blocker remains |
| Q-DEP-001 | 실행·배포 목표 | `A — local-first, 초기 예산 0원` | 초기 완료 기준은 로컬 재현이며 외부 인프라 지출 한도는 0원이다. 공개 demo/staging의 계정·리전·로그·CORS는 추후 별도 승인한다. | D-013 / ADR-0002 | Resolved for local; public deployment deferred |
| Q-SEC-001 | 관리자 보호 방식 | `추천안으로 ㄱ` | 추천안 그대로 초기에는 local/private에서만 `/admin`과 관리자 API를 활성화한다. 공개 배포 시에는 서버측 gate를 별도 승인·검증하기 전 관리자 경로를 비활성화한다. | D-014 / ADR-0007 | Resolved |
| Q-PRIV-001 | 30일 후 실패 질문 처리 | `A` | 30일 후 `masked_question` 텍스트만 `NULL`로 파기하고 파기 시각을 기록한다. 실패 행·비텍스트 메타데이터·KB 후보 FK는 유지한다. | D-015 / ADR-0004 | Resolved |

## 답변 원문

```text
Q-REPO-001: A — 원본 원격 저장소 없음
Q-DEV-001: A
Q-DATA-001: A — 작성 AI/Data·Backend, 승인 PM, 완료 목표 2026-07-20
Q-LLM-001: B
Q-DEP-001: A — local-first, 초기 예산 0원
Q-SEC-001: 추천안으로 ㄱ
Q-PRIV-001: A
```

## Batch 2 — 2026-07-14 KST

- Scope: `Q-LLM-002` ~ `Q-CI-001`

| Q-ID | Question summary | User answer | Interpretation | Decision/ADR | Status |
|---|---|---|---|---|---|
| Q-LLM-002 | 실제 LLM 공급자·비용 경로 | `내가 딥시크 api가 남아서 그거 쓰면 됨.` | 사용자 소유의 기존 DeepSeek API 잔액을 사용한다. 새 충전·자동 충전은 하지 않으며 키 값과 잔액은 저장소/문서에 기록하지 않는다. 현재 공식 V4 모델 ID와 호출 상한은 Q-LLM-004에서 확정한다. | D-016 / ADR-0005 | Partially resolved — exact model/quota blocker remains |
| Q-LLM-003 | 호스팅 LLM 입력 허용 범위 | `A - 어차피 실사용 까지는 안해서 괜찮을듯` | DeepSeek 호출은 local/private 환경의 서버 검증 합성 fixture에만 허용한다. 실제 시민 자유 입력·실제 PII·민감정보·공개 운영에는 사용하지 않는다. 공급자의 기본 디스크 캐시와 고정되지 않은 전체 보관기간을 수용하는 범위도 이 합성 시연으로 한정한다. | D-017 / ADR-0005 | Resolved for synthetic demo; public/real-user use prohibited |
| Q-DB-001 | DB 마이그레이션 체계 | `A` | Supabase CLI의 버전 SQL 마이그레이션을 실행 권위로 사용한다. Docker local stack과 CLI 설치·migration 생성은 최종 계획 승인 후 수행한다. 원격 push·파괴 변경은 별도 승인 대상이다. | D-018 / ADR-0008 | Resolved for local |
| Q-PRIV-002 | 이름·상세주소 마스킹 기준 | `A - 일단 a해보고 성능 안나오면 B로 변경하는 느낌으로 가자` | 재현율 우선 보수적 마스킹으로 시작한다. 동일 평가셋에서 답변 성공률 80% 미달의 원인이 과잉 마스킹으로 입증되면 B를 재검토하되 자동 전환하지 않고 개인정보 계약 변경으로 다시 승인받는다. 마스킹률 100% 기준은 유지한다. | D-019 / ADR-0004 | Resolved with human review gate |
| Q-CHAT-001 | 대화 기억·세션 | `대화기억이 없으면 챗봇느낌이 안나지않을까? 이건 아직 잘 모르겠음. 나중에 제대로 설명해줘.` | 사용자는 무상태 기본안에 우려를 표시했고 결정을 보류했다. 브라우저의 화면 대화기록·구조화 문맥 전달·서버 영속 저장을 분리해 설명한 뒤 다시 결정한다. 현재 `session_id` 의미와 TTL은 확정하지 않는다. | D-022 (Deferred) | Open — A blocker |
| Q-API-001 | 기술 장애 HTTP 계약 | `A` | 정책 폴백은 200 `ChatResponse`, 안전 응답을 만들 수 없는 실제 시스템 불능만 503 `SERVICE_UNAVAILABLE` envelope로 반환한다. provider 장애라도 ACTIVE KB 템플릿으로 안전 답변 가능하면 200이다. | D-020 / ADR-0009 | Resolved |
| Q-CI-001 | 원격 저장소·CI | `일단은 B 로가고 나중에 내가 git 연결해야할거같을때 다시 말해줄게.` | 2026-07-14 당시 local Git과 수동 검증 gate만 사용한다는 결정이다. 2026-07-20 private source remote/협업 방향은 Batch 6 D-047~D-052가 후속 결정하며 local-only gate는 유지한다. | D-021 / ADR-0002 / ADR-0019 | Historical; source-remote 부분 superseded, local gate 유지 |

## Batch 2 답변 원문

```text
Q-LLM-002: 내가 딥시크 api가 남아서 그거 쓰면 됨.
Q-LLM-003: A  - 어차피 실사용 까지는 안해서 괜찮을듯
Q-DB-001: A
Q-PRIV-002: A - 일단 a해보고 성능 안나오면 B로 변경하는 느낌으로 가자
Q-CHAT-001: 대화기억이 없으면 챗봇느낌이 안나지않을까? 이건 아직 잘 모르겠음. 나중에 제대로 설명해줘.
Q-API-001: A
Q-CI-001: 일단은 B 로가고 나중에 내가 git 연결해야할거같을때 다시 말해줄게.
```

## Batch 3 — 2026-07-14 KST

- Scope: `Q-LLM-004`, `Q-CHAT-001` 최종 선택

| Q-ID | Question summary | User answer | Interpretation | Decision/ADR | Status |
|---|---|---|---|---|---|
| Q-LLM-004 | DeepSeek V4 모델·thinking·비용 보호 한도 | `A` | 모델은 정확히 `deepseek-v4-flash`, thinking off, `max_tokens=1024`, 동시 외부 호출 1개, 요청당 재시도 최대 1회로 고정한다. 한 번의 명시적 평가/데모 run에서 재시도를 포함한 실제 외부 전송 시도는 총 30회를 넘지 않으며 새 충전·자동 충전은 하지 않는다. local/private의 서버 검증 합성 fixture만 허용하고, 한도 도달·429·장애 시 ACTIVE KB template 또는 정책 폴백으로 안전하게 전환한다. | D-023 / ADR-0005 | Resolved |
| Q-CHAT-001 | 대화 기억·세션 | `A` | 현재 탭 메모리에서 화면 대화를 유지하고 서버에는 raw transcript나 세션을 저장하지 않는다. API는 15분짜리 서명형 `context_token`만 클라이언트가 전달한다. 토큰에는 서버 정의 enum/ID·발급/만료 시각만 허용하며 질문·답변·PII·URL·공식 사실은 금지한다. 만료·위변조 토큰은 인증 오류가 아니라 문맥 없는 새 요청처럼 처리한다. | D-024 / ADR-0010 | Resolved |

## Batch 3 답변 원문

```text
Q-LLM-004: A
Q-CHAT-001: A
```

## Batch 4 — 2026-07-18 KST

- Scope: `Q-DATA-002` 공식 데이터 staging·approval artifact

| Q-ID | Question summary | User answer | Interpretation | Decision/ADR | Status |
|---|---|---|---|---|---|
| Q-DATA-002 | 승인 전 공식 데이터 artifact 저장 방식 | `A` | `data/staging/data-001/<draft-version>/`의 KB·기관·매핑 JSON과 hash-bound PM approval manifest를 canonical 경계로 사용한다. 승인 record의 immutable official release와 seed는 별도 DATA-SEED-001에서만 생성하고, 초기 19 KB+WASTE-03 보류 뒤 REG-001에서 최종 20 ACTIVE를 만든다. | D-033 / ADR-0015 | Resolved — written spec review pending |

## Batch 4 답변 원문

```text
Q-DATA-002: A
```

## Batch 5 — 2026-07-19 KST

- Scope: PM 승인 증거, DATA-SEED architecture, static `/chat` destination

| Q-ID | Question summary | User answer | Interpretation | Decision/ADR | Status |
|---|---|---|---|---|---|
| Q-DATA-003 | PM 검수 결과 materialization | `A — PM-LOCAL-001 ... 권고안 그대로 ... 이 답변 시각` | reviewer `PM-LOCAL-001`, current 35 recommendations, final confirmation `2026-07-19T02:06:19+09:00`을 canonical approval evidence로 사용한다. official release/seed 승인은 아님. | D-035 / ADR-0015 | Resolved — materialized/verified |
| Q-SEED-001 | approved record release/import 구조 | `A` | immutable filesystem release + existing-schema transactional seed; empty disposable local DB만 compensation. Initial version/projection AI default는 `0.1.0-initial.1`/19·3·10. | D-036 / ADR-0016 | Architecture resolved — written spec reviewed, user approval pending |
| Q-WEB-001 | chat pipeline 전 home CTA destination | `A` | 입력·저장·fetch가 없는 accessible static `/chat` preparation route를 만들고 홈 CTA를 연결한다. | D-037 / PLAN-001 | Resolved — implementation authorized |

## Batch 5 답변 원문

```text
Q-DATA-003: A — PM-LOCAL-001을 reviewer ID로 확인, 권고안 그대로 확정, 이 답변 시각을 final confirmation 시각으로 사용
Q-SEED-001: A
Q-WEB-001: A
그리고 이제부터 다시 멈추지 말고, 계속해서 ㄱㄱ. 7시간 동안 루프 ㄱㄱ. 너가 할수있는거 다 해줘. 사람이 해야하는건 따로 남겨두고.
```

## Batch 6 — 2026-07-20 KST

- Scope: private GitHub·Frontend ownership·Codex Cloud collaboration

| Q-ID | Question summary | User answer | Interpretation | Decision/ADR | Status |
|---|---|---|---|---|---|
| Q-GIT-001 | 공유 source remote 위치·가시성 | `A` | 사용자의 개인 GitHub 계정 아래 private repository를 만들고 Frontend 팀원을 collaborator로, Codex App은 이 repository 하나에만 허용한다. | D-047 / ADR-0019 | Resolved decision; execution pending |
| Q-OWN-001 | Frontend 위임 범위 | `A` | 팀원이 세 페이지, typed API client, 화면 상태, 반응형·접근성, frontend unit/E2E의 전체 frontend 수직 흐름을 소유한다. | D-048 / ADR-0019 | Resolved |
| Q-GIT-002 | private branch protection을 위한 유료 plan | `A` | GitHub Free·초기 0원을 유지하고 보호 기능의 완전 강제를 전제하지 않는다. | D-049 / ADR-0019 | Resolved |
| Q-GIT-003 | Frontend 팀원 자가 병합 | `B` | 허용 frontend-only green PR만 자가 병합하고 contract/backend/DB/data/security/dependency 경계는 사용자 검토로 승격한다. | D-050 / ADR-0019 | Resolved |
| Q-CLOUD-001 | Codex Cloud 병합 권한 | `A` | Cloud는 branch와 Draft PR까지만 만들고 사용자가 병합한다. | D-051 / ADR-0019 | Resolved |
| Q-COLLAB-001 | 전체 협업 운영 명세 | `A` | private single repo, role-scoped merge, Cloud Draft PR, local-only actual gate 설계를 승인한다. | D-052/D-054 / ADR-0019 | Written spec and execution plan Approved; implementation in progress |

## Batch 6 답변 원문

```text
Q-GIT-001: A
Q-OWN-001: A
Q-GIT-002: A
Q-GIT-003: B
Q-CLOUD-001: A
Q-COLLAB-001: A
```

COLLAB-001은 별도 실행계획 승인과 GitHub owner/repository/collaborator login 확인 전에는 remote,
push, 초대, workflow 또는 Codex App 설정을 완료로 기록하지 않는다.

전체 Git history 감사에서 credential/content secret은 0건이고 ignored local DeepSeek key의 exact
value도 history 0건이었다. 다만 도달 가능한 163개 commit의 실제 형태 author/committer email
metadata 공개 여부는 Q-GIT-004/A-039로 분리했다. 답 전에는 remote 생성·commit·push를 하지 않는다.

## Batch 7 — 2026-07-20 KST

- Scope: existing Git author identity privacy before first private remote push

| Q-ID | Question summary | User answer | Interpretation | Decision/ADR | Status |
|---|---|---|---|---|---|
| Q-GIT-004 | 기존 author/committer email metadata 공개 여부 | `A — 내 이메일이고 private 팀원에게 보여도 괜찮음` | 현재 reachable history와 SHA를 보존하고 noreply rewrite를 하지 않는다. | D-053 / ADR-0019 | Resolved; COLLAB-001 plan subsequently Approved by D-054 |

## Batch 7 답변 원문

```text
Q-GIT-004: A — 내 이메일이고 private 팀원에게 보여도 괜찮음
```

## 남은 구현 차단 조건

- DATA-SEED-002: approved architecture/spec 뒤 successor 실행계획의 명시적 승인.
- COLLAB-001: Q-GIT-004는 D-053으로 해결되고 실행계획은 D-054로 승인. GitHub account 식별자와
  browser 인증·collaborator 수락·Cloud rehearsal은 외부 실행 입력/증거로 pending.
- PII-CONSUMER-001: 공개 contract와 forward DB migration의 별도 명세·계획·승인.
- public release: D-046의 deferred `00700` 구현·검증과 별도 공개 배포 승인.
- 별도 미래 승인: 실제 시민 입력의 외부 LLM 전송, 실제 사용자 데이터, 파괴적 DB 변경.
