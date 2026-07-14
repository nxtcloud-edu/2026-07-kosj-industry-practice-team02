# 현재 업로드 프로젝트 감사와 마이그레이션 주의사항

## 1. 감사 결론

업로드된 `sejong_ai.zip`은 **초기 통합 패키지**로서 문서·FastAPI mock·CSV·정적 프로토타입을 제공하지만, 최종 확정 기준과 다수 충돌한다. 안전한 전략은 기존 파일을 `legacy/`에 보존하고, 신규 활성 구조에서 필요한 아이디어와 코드를 검증 후 선택적으로 이전하는 것이다.

## 2. 핵심 충돌

| 기존 파일/영역 | 현재 상태 | 최종 기준과 충돌 | Codex 조치 |
|---|---|---|---|
| 루트/ops 문서 | 10개 분야, 100개 테스트, 고급 분석 | 최종 4개 분야, 20개+회귀, 승인 루프 | legacy 참고만, source-of-truth 사용 |
| `backend/app/main.py` | CSV 매 요청 로드, 규칙형 mock | DB/승인/이벤트/adapter 없음 | 복사 전 설계 재검증, 새 API로 재구성 |
| intent KEYWORDS | 복지·청년·인허가·교통 등 포함 | 지원 분야 4개+OUT_OF_SCOPE | 지원 enum 재정의 |
| fallback code | `KB_MISSING`, `PRIVATE_LOOKUP` 등 | 최종 4개 폴백 코드와 FOLLOWUP | 계약과 enum 통일 |
| `/api/status` | mock 상태조회 | P2이며 MVP에서 제외 | 활성 API에서 제거 |
| analytics/recommendations | 급증·자동 추천 | P2 | 활성 API에서 제거 |
| quality report | 100개 고정 mock 수치 | 20개 실제 결과와 배지 구분 | 실제 평가 파이프라인으로 대체 |
| `db/schema.sql` messages | 질문/답변 텍스트 저장 가능 | 성공 질문 텍스트 미저장 | interaction_events/failed_questions 분리 |
| `audit_logs` full states | before/after 전체 객체 가능 | 전문 저장 금지 | 상태·변경 필드명만 저장 |
| KB schema | status/approval/verified 부족 | ACTIVE/승인/출처 필수 | v1 스키마로 교체 |
| `kb_seed.csv` 60행 | 다수 비공식·URL 공란 | 공식 20건·출처대장·확인일 | 시민 근거로 사용 금지, legacy 이동 |
| `offices_seed.csv` | 가상주소·가상전화 | 시민 화면 공식 데이터만 | 사용 금지, 공식 데이터 수집 |
| `test_questions_100.csv` | 초기 100문항 | 최종 20문항+REG-01 | 평가셋 교체 |
| 정적 프로토타입 | UI 참고 가능 | 최종 흐름과 탭이 다름 | 시각 참고만, 접근성 재검증 |
| requirements | 고정된 오래된 버전 | 신규 환경과 호환 미확인 | 패키지 관리자/버전 인터뷰 후 결정 |

## 3. 코드 수준 누락

- 프로젝트 패키지 관리자, Node/Python 버전, 로컬 실행 통합 명령 없음
- 실제 Next.js 앱 없음
- DB 마이그레이션 도구 없음
- 실제 Supabase 연결/RLS/권한 결정 없음
- LLM provider adapter와 구조화 출력 검증 없음
- 서버 결합 출처 카드 계약 없음
- 모든 요청용 비식별 event 모델 없음
- 실패 질문 보관/삭제 job 없음
- 역할 분리와 자기 승인 차단 없음
- 계약 테스트, 단위 테스트, E2E, 접근성, 부하 테스트 없음
- CI, secret scanning, format/lint/typecheck 규칙 없음
- 공식 KB 20건과 기관 3건 미수집

## 4. 재사용 후보

다음은 검증 후 아이디어/부분 코드로 재사용할 수 있다.

- FastAPI 라우팅 구조
- 기본 정규식 마스킹의 일부 패턴
- CSV loader는 마이그레이션/seed 도구 참고
- citizen/admin 정적 HTML의 레이아웃 아이디어
- 기존 prompt 초안의 근거 제한 문구

재사용 시 반드시 최종 enum, 저장정책, 출처정책, 테스트 기준을 적용한다.

## 5. 금지된 자동 조치

- 오래된 코드에 기능을 덧붙여 최종 앱이라고 가정
- 가상주소·가상전화번호를 시민 화면에 노출
- 60개 KB를 공식 데이터로 import
- mock KPI를 실제 운영 결과로 표시
- 100개 테스트를 최종 평가셋으로 복원
- P2 엔드포인트를 ‘이미 있는 코드’라는 이유로 유지
