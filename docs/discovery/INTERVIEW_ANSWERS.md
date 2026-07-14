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
| Q-CI-001 | 원격 저장소·CI | `일단은 B 로가고 나중에 내가 git 연결해야할거같을때 다시 말해줄게.` | 현재 단계는 local Git과 수동 검증 gate만 사용한다. 원격/CI를 임의 생성하지 않으며 사용자가 다시 요청할 때 계정·백업·branch protection을 결정한다. | D-021 / ADR-0002 | Resolved for current phase; remote/CI deferred |

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

## 남은 구현 차단 조건

- 인간 결정형 A/Blocker: 없음
- 제품 구현 gate: 이 결정을 반영한 최종 실행계획과 명시된 초기 프로덕션 의존성 목록에 대한 사용자의 명시적 `진행`/`구현 시작`
- 별도 미래 승인: 공개 배포, 실제 시민 입력의 외부 LLM 전송, 원격 저장소/CI, 실제 사용자 데이터, 파괴적 DB 변경
