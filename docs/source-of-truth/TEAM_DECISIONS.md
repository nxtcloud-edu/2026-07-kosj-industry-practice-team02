# 팀 결정사항 요약

## 제품

- 서비스명: 세종 민원 AI 길잡이
- 구조: 시민용 민원 AI 플랫폼 + 관리자용 AI 민원 운영센터
- 기준 문장: **모르면 지어내지 않고, 알면 끝까지 안내한다.**
- 차별점: 실패 질문을 공식 KB 후보로 전환하고 담당자가 승인하는 개선 루프

## 구현 범위

- 실제 페이지: `/`, `/chat`, `/admin`
- 지원 분야: 전입·주민등록, 증명서 발급, 대형폐기물, 지방세 일반 안내
- P0: 질문·분류·공식 KB 답변·출처·후속질문·4개 폴백·지역 선택·기관 카드·관리자 승인 루프
- P1: 쉬운 말, 큰 글씨, 기본 명도 대비 4.5:1 이상, 실패 질문 필터, KPI, 품질 카드, 감사 이력, 성능 스모크 테스트
- P2: 실제 GPS·지도 내장·상태조회·정부24/내부망 연계·다국어·음성·고급 분석·전체 KB CRUD

## 데이터

- 공식 KB 20건: 4개 분야 × 5건
- 공식 기관 3개: 아름동, 도담동, 조치원읍 중심
- 공식 KB·기관 데이터 작성: AI/Data·Backend
- 공식 KB·기관 데이터 승인: PM 전수 검수
- 공식 데이터 완료 목표: 2026-07-20
- 표본 질문 20개 + 개선 전후 회귀 테스트 1개
- 실패 질문 mock 20~30건, 운영 이벤트 mock 50~100건, KB 후보 mock 5~10건
- 시민 기관 정보는 공식 데이터만 사용
- 관리자 mock 데이터에는 `시연용 샘플` 배지 표시

## 폴백

- INSUFFICIENT_GROUNDING: 후보 가능
- PERSONAL_LOOKUP: 후보 불가
- LEGAL_JUDGMENT: 후보 불가
- OUT_OF_SCOPE: 후보 불가, 질문 텍스트 저장 금지
- 모호 질문: FOLLOWUP, 실패 질문이 아님

## 개인정보

- 외부 LLM 호출 전 백엔드에서 마스킹
- 사용자 원문 DB 미저장
- 성공 질문 텍스트 미저장, 이벤트 메타데이터만 저장
- 실패 질문의 `masked_question` 텍스트만 생성 후 30일 보관하고 만료 시 NULL 파기
- 실패 질문 행·비텍스트 메타데이터·KB 후보 연결은 텍스트 파기 후에도 유지
- 애플리케이션 DB에서 IP·기기 ID 미수집
- 30일은 MVP 내부 운영 기준
- 이름·상세주소는 재현율 우선 보수적 마스킹; 답변 성공률 저하가 입증돼도 정밀도 우선 전환은 인간 재승인 후
- DeepSeek 외부 호출은 local/private의 서버 검증 합성 fixture에만 허용; 실제 시민·PII·민감정보·공개 운영은 금지
- 화면 transcript와 대화 token은 현재 탭 메모리에만 유지; 서버 세션·raw transcript·token 영속 저장 금지

## 기술

- Frontend: Next.js + TypeScript + Tailwind CSS
- Backend: FastAPI + Python
- 개발 기준: Node 24.x+pnpm, Python 3.12+uv
- DB/Search: Supabase PostgreSQL + Supabase CLI 버전 SQL migration + 키워드·메타데이터 검색; MVP embedding off
- LLM: 사용자 기존 DeepSeek API 잔액, local/private 합성 fixture 전용, 정확히 `deepseek-v4-flash`, thinking off, max output 1024, concurrency 1, retry 최대 1회, run당 외부 전송 시도 총 30회; provider adapter와 disabled/template fallback 필수
- 초기 실행: local-first, 외부 인프라 예산 0원
- 향후 배포 추천: Vercel(Frontend) + Render(Backend) + Supabase(DB); 공개 배포는 계정·리전·로그·CORS·예산 별도 승인 후
- 관리자: 초기 local/private 전용, public 환경에서는 서버측 gate 없이는 `/admin`과 관리자 API 비활성
- 저장소: 원본 원격 없는 새 독립 Git 저장소, 기본 브랜치 `main`, 작업 브랜치 `codex/<task-id>-<slug>`
- 협업 gate: 현재 원격/CI 없음, local 수동 lint·typecheck·test·build·contract·secret 검사; Git 연결은 사용자 재요청 시 결정
- 오류 계약: 정책 응답은 HTTP 200, 승인 근거로 안전 응답을 만들 수 없는 시스템 불능만 HTTP 503 `SERVICE_UNAVAILABLE`
- 대화 기억: 화면 기록은 현재 탭 메모리, 짧은 구조화 문맥은 15분 서명형 client-carried `context_token`; 서버 세션·raw 대화문·token 저장 금지, token은 인증이나 공식 사실 근거가 아님
- DB role bootstrap: PostgreSQL 17 non-superuser migration runner를 유지한다. role은 처음부터 안전 속성으로 생성하고, replay에서는 runner가 허용받은 `NOLOGIN`·`NOCREATEDB`·`NOCREATEROLE`만 재적용한 뒤 `NOSUPERUSER`·`NOREPLICATION`·`NOBYPASSRLS`, membership, role setting을 catalog로 검증한다. 안전하지 않으면 중단하며 privileged 자동 downgrade/bootstrap은 도입하지 않는다.
- 실패 사유 확인: backend-only `confirm_failed_question_reason(uuid,text,text,text)` capability로 OPERATOR만 `NEW → REASON_CONFIRMED`를 수행한다. 최초 `interaction_events.fallback_reason`은 자동 분류 기록으로 불변이고, 운영자 확인·정정값은 `failed_questions.fallback_reason`에만 반영하며 `candidate_eligible`을 다시 계산한다.
- 후보 gate: 후보 작성은 `REASON_CONFIRMED + INSUFFICIENT_GROUNDING + candidate_eligible=true` failure에서만 가능하다. 사유 확인은 질문/답변 snapshot 없이 metadata audit를 남긴다.
- 승인 comment: 공개 OpenAPI가 승인·반려 모두 `review_comment`를 요구하므로 내부 승인 capability도 `approve_kb_candidate(uuid,text,text,text)`를 사용해 승인 comment를 후보와 metadata audit에 저장한다. 공개 wire 계약은 바뀌지 않는다.
- 적용된 migration은 불변이다. 이미 commit된 `00100~00500`을 수정하지 않고 deferred ACTIVE-question trigger 권한 보정은 새 `00600`에 추가하며 compensation은 `00600 → 00500 → 00400 → 00300 → 00200 → 00100` 순서다.
- deferred ACTIVE-question trigger 실행: `app_private.validate_active_kb_question()` 하나만 새 `00600`에서 제한된 SECURITY DEFINER로 전환한다. `sejong_schema_owner`, `search_path=pg_catalog, pg_temp`(공식 PostgreSQL 17 SECURITY DEFINER 지침에 따라 임시 스키마를 마지막에 명시), PUBLIC·anon·authenticated·backend 직접 EXECUTE revoke를 재확인하며 backend private schema/table grant와 repository/admin-DSN 우회는 금지한다. 사용자의 직전 추천안 뒤 계속 진행 지시는 Q-DB-003=A 승인으로 해석했고 문자 A를 직접 입력했다고 기록하지 않는다.

## 제출 정보

- 팀명: [직접 입력]
- 팀원·역할: [직접 입력]
- 대표 연락처: [직접 입력]
- 제출일: [직접 입력]
- 최종 확인란: `팀 대표 확인`
- 문서 버전: v2.2
