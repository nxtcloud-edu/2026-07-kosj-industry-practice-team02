# 02. 개발용 가이드 — 시민용 민원 AI 플랫폼 + 관리자용 AI 민원 운영센터

## 0. 개발 목표

이 문서는 4인 팀이 2026년 7월 한 달 동안 실제 구현할 수 있는 수준으로 개발 범위, 기술 스택, DB/API 구조, 일정, 역할, 구현 우선순위를 정리한 개발 가이드이다.

최종 구현 목표는 다음 두 서비스를 하나의 제품으로 제공하는 것이다.

1. **시민용 민원 AI 플랫폼**: 시민이 자연어로 민원을 질문하고 출처 기반 답변을 받는 서비스
2. **관리자용 AI 민원 운영센터**: 답변 실패 질문과 민원 로그를 분석하여 지식베이스 개선 후보를 관리하는 대시보드

## 1. 추천 기술 스택

### 1.1 추천안 A — 발표 완성도 우선

| 영역 | 기술 |
|---|---|
| Frontend | Next.js 14+, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11+ |
| Database | PostgreSQL, pgvector 또는 Supabase |
| AI/Search | LLM API, Embedding, BM25/Vector Hybrid Search |
| 지도 | Kakao/Naver/Google 지도 링크 또는 API |
| 배포 | Vercel + Render/Railway + Supabase |

### 1.2 추천안 B — 구현 안정성 우선

| 영역 | 기술 |
|---|---|
| Frontend/Backend | Streamlit |
| Database | SQLite |
| AI/Search | Python keyword search + optional LLM |
| 배포 | Streamlit Cloud 또는 로컬 데모 |

### 1.3 최종 추천

개발 경험이 조금이라도 있다면 **Next.js + FastAPI + PostgreSQL/Supabase**를 추천한다. 화면 완성도와 관리자 대시보드 표현력이 좋기 때문이다. 단, 시간이 부족하면 backend는 FastAPI mock API로 시작하고 DB 연동은 점진적으로 붙인다.

## 2. 저장소 구조

```text
sejong-ai-civil-platform/
├─ frontend/
│  ├─ app/
│  │  ├─ page.tsx                 # 시민용 홈
│  │  ├─ chat/page.tsx            # 시민용 챗봇
│  │  ├─ offices/page.tsx         # 기관 찾기
│  │  ├─ status/page.tsx          # mock 상태조회
│  │  └─ admin/
│  │     ├─ page.tsx              # 관리자 Overview
│  │     ├─ failed/page.tsx       # 답변 실패 질문
│  │     ├─ analytics/page.tsx    # 민원 자동 분석
│  │     ├─ recommendations/page.tsx
│  │     └─ quality/page.tsx
│  ├─ components/
│  │  ├─ ChatBox.tsx
│  │  ├─ AnswerCard.tsx
│  │  ├─ SourceCard.tsx
│  │  ├─ KpiCard.tsx
│  │  ├─ AnalyticsChart.tsx
│  │  └─ FailedQuestionTable.tsx
│  └─ lib/api.ts
│
├─ backend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ routers/
│  │  │  ├─ chat.py
│  │  │  ├─ admin.py
│  │  │  ├─ offices.py
│  │  │  └─ status.py
│  │  ├─ services/
│  │  │  ├─ classifier.py
│  │  │  ├─ kb_search.py
│  │  │  ├─ answer_generator.py
│  │  │  ├─ fallback.py
│  │  │  ├─ analytics.py
│  │  │  └─ pii_masker.py
│  │  ├─ models/
│  │  └─ db.py
│  ├─ requirements.txt
│  └─ .env.example
│
├─ db/schema.sql
├─ data/
│  ├─ kb_seed.csv
│  ├─ offices_seed.csv
│  ├─ mock_status_cases.csv
│  ├─ admin_mock_logs.csv
│  └─ test_questions_100.csv
└─ docs/
```

## 3. 개발 우선순위

### 3.1 1순위 — 반드시 구현

| 우선순위 | 기능 | 이유 |
|---:|---|---|
| 1 | 시민용 챗봇 UI | 서비스의 본체 |
| 2 | 민원 의도 분류 | RFP 핵심 요구 |
| 3 | KB 검색 및 출처 표시 | 환각 방지 핵심 |
| 4 | 절차·서류 답변 카드 | 공공 민원 특화 |
| 5 | 폴백/후속질문 | 안전한 공공 AI |
| 6 | 비식별 로그 저장 | 관리자 분석 기반 |
| 7 | 관리자 KPI Overview | 차별화 진입점 |
| 8 | 답변 실패 질문 관리 | 핵심 차별점 |
| 9 | 민원 자동 분석 | 운영형 플랫폼 증명 |
| 10 | 지식베이스 개선 추천 | 지속 개선 구조 |

### 3.2 2순위 — 가능하면 구현

- 담당 기관/주민센터 연결
- mock 상태조회
- 품질 리포트
- 급증 민원 탐지
- 주간 리포트 자동 생성
- 개인정보 마스킹 모니터링

### 3.3 3순위 — 발표용 확장

- 다국어 일부
- 음성 입력/읽기
- 지도 마커 시각화
- KB CRUD
- 관리자 리포트 PDF 다운로드

## 4. 데이터 모델 요약

### 4.1 핵심 테이블

| 테이블 | 설명 |
|---|---|
| `categories` | 민원 대분류 |
| `civil_services` | 민원 상세 서비스 |
| `kb_documents` | 행정 지식베이스 문서 |
| `kb_chunks` | 검색 단위 청크 |
| `offices` | 주민센터/부서 정보 |
| `conversations` | 비식별 대화 세션 |
| `messages` | 질문/답변 메시지 로그 |
| `failed_questions` | 답변 실패 질문 |
| `kb_recommendations` | KB 개선 후보 |
| `mock_status_cases` | 접수번호 상태조회 mock |
| `evaluation_cases` | 테스트 질문 |
| `evaluation_results` | 평가 결과 |

자세한 SQL은 `db/schema.sql`을 기준으로 한다.

## 5. API 명세 요약

### 5.1 시민용 API

| Method | Endpoint | 설명 |
|---|---|---|
| POST | `/api/chat` | 사용자 질문 처리 |
| GET | `/api/categories` | 민원 카테고리 조회 |
| GET | `/api/services` | 민원 서비스 목록 조회 |
| GET | `/api/offices/search` | 지역/민원 기반 기관 검색 |
| GET | `/api/status/{receipt_no}` | mock 접수번호 조회 |
| POST | `/api/feedback` | 답변 만족도/피드백 저장 |

### 5.2 관리자용 API

| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/api/admin/stats` | KPI 요약 |
| GET | `/api/admin/failed-questions` | 답변 실패 질문 목록 |
| GET | `/api/admin/analytics` | 민원 자동 분석 |
| GET | `/api/admin/kb-recommendations` | 지식베이스 개선 추천 |
| GET | `/api/admin/quality-report` | 답변 품질 리포트 |
| GET | `/api/admin/department-routing` | 담당 부서 연결 현황 |
| POST | `/api/admin/weekly-report` | 주간 인사이트 리포트 생성 |

자세한 명세는 `api/openapi.yaml`을 기준으로 한다.

## 6. AI 처리 로직

### 6.1 전체 함수 구조

```python
def handle_chat(question: str, session_id: str, area: str | None):
    masked_question, pii_flags = mask_pii(question)
    safety = check_safety(masked_question)
    if not safety.ok:
        return fallback_response(reason="unsafe_or_private")

    intent = classify_intent(masked_question)
    if intent.confidence < 0.55:
        save_log(status="clarification")
        return clarification_response(intent.candidates)

    documents = search_kb(masked_question, intent.code)
    if len(documents) == 0 or documents[0].score < 0.50:
        save_failed_question(reason="kb_missing")
        return fallback_response(reason="kb_missing", intent=intent)

    answer = generate_grounded_answer(masked_question, documents)
    verified = verify_sources(answer, documents)
    if not verified:
        save_failed_question(reason="source_insufficient")
        return fallback_response(reason="source_insufficient", intent=intent)

    save_log(status="answered", source_count=len(documents))
    return answer
```

### 6.2 민원 의도 코드

| 코드 | 한글명 |
|---|---|
| `MOVE_IN_REPORT` | 전입신고 |
| `CERTIFICATE_ISSUE` | 증명서 발급 |
| `BULKY_WASTE` | 대형폐기물 |
| `LOCAL_TAX` | 지방세 |
| `WELFARE` | 복지 |
| `YOUTH_JOB` | 청년/일자리 |
| `CHILDCARE_EDU` | 보육/교육 |
| `BUSINESS_PERMIT` | 인허가 |
| `TRAFFIC_PARKING` | 교통/주차 |
| `LIFE_ENV` | 생활/환경 |
| `STATUS_LOOKUP` | 상태 조회 |
| `OFFICE_LOOKUP` | 기관 찾기 |
| `UNSAFE_OR_PRIVATE` | 개인정보/민감 조회 |
| `UNKNOWN` | 미분류 |

## 7. 관리자 대시보드 구현 방법

### 7.1 Overview KPI 계산

```sql
SELECT COUNT(*) AS total_questions FROM messages WHERE role='user';

SELECT
  AVG(CASE WHEN answer_status='answered' THEN 1 ELSE 0 END) AS answer_success_rate,
  AVG(CASE WHEN answer_status='fallback' THEN 1 ELSE 0 END) AS fallback_rate,
  AVG(response_time_ms) AS avg_response_ms
FROM messages
WHERE role='assistant';
```

### 7.2 답변 실패 질문 저장 조건

다음 케이스에서 `failed_questions`에 저장한다.

- `fallback_reason = 'kb_missing'`
- `fallback_reason = 'source_insufficient'`
- `fallback_reason = 'department_unknown'`
- `fallback_reason = 'needs_latest_info'`
- `fallback_reason = 'private_lookup'`

단, 개인정보가 포함된 원문은 저장하지 않고 마스킹된 질문만 저장한다.

### 7.3 유사 실패 질문 그룹화

초기 버전은 키워드 기반으로 구현한다.

```python
KEYWORD_GROUPS = {
    "반려동물 등록": ["반려동물", "강아지", "고양이", "동물등록"],
    "대형폐기물 수수료": ["침대", "소파", "폐가전", "스티커", "대형폐기물"],
    "청년 월세 지원": ["청년", "월세", "지원금", "신청기간"],
}
```

시간이 남으면 embedding 기반 clustering으로 확장한다.

### 7.4 지식베이스 개선 우선순위

```python
priority_score = frequency * 0.4 + failure_rate * 0.3 + growth_rate * 0.2 + importance * 0.1
```

## 8. 화면별 구현 체크리스트

### 8.1 시민용 챗봇

- [ ] 질문 입력창
- [ ] 예시 질문 버튼
- [ ] 민원 분류 표시
- [ ] 답변 카드
- [ ] 절차 카드
- [ ] 필요 서류 카드
- [ ] 출처 카드
- [ ] 담당 부서 카드
- [ ] 후속질문 선택지
- [ ] 폴백 안내
- [ ] 모바일 반응형

### 8.2 관리자 Overview

- [ ] 총 질문 수 KPI
- [ ] 자동 답변 성공률
- [ ] 폴백 비율
- [ ] 평균 응답시간
- [ ] 출처 표기율
- [ ] 개인정보 감지 건수
- [ ] 신규 KB 후보 수
- [ ] 최근 급증 민원 알림

### 8.3 답변 실패 질문

- [ ] 실패 질문 목록
- [ ] 실패 원인 태그
- [ ] 추정 민원 유형
- [ ] 추천 조치
- [ ] 처리 상태
- [ ] 유사 질문 묶음

### 8.4 민원 자동 분석

- [ ] 유형별 비율
- [ ] 시간대별 문의
- [ ] 지역별 문의
- [ ] 담당 부서 연결 건수
- [ ] 폴백 사유 분석
- [ ] 급증 민원 탐지

### 8.5 지식베이스 개선 추천

- [ ] 개선 후보 목록
- [ ] 관련 질문 수
- [ ] 실패율
- [ ] 증가율
- [ ] 우선순위 점수
- [ ] 추천 조치

## 9. 4주 개발 일정

### 1주차 — 분석 + 뼈대 구축

| 역할 | 할 일 |
|---|---|
| PM | RFP 분석, 요구사항 매트릭스, 제안서 목차 |
| Frontend | 시민용 홈/챗봇/관리자 레이아웃 |
| Backend | FastAPI 세팅, mock API, DB 스키마 |
| AI/Data | 카테고리, KB seed 50개, 테스트 질문 30개 |

### 2주차 — 핵심 챗봇 + 로그 저장

| 역할 | 할 일 |
|---|---|
| PM | 입찰제안서 초안 작성 |
| Frontend | 답변 카드, 출처 카드, 폴백 UI |
| Backend | `/api/chat`, `/api/offices`, 로그 저장 |
| AI/Data | 분류/검색/폴백 로직, KB 100개 |

### 3주차 — 관리자 대시보드 + 분석

| 역할 | 할 일 |
|---|---|
| PM | 발표 흐름, 차별점 문장 정리 |
| Frontend | 관리자 Overview/Failed/Analytics 화면 |
| Backend | admin API, 통계 쿼리, mock status |
| AI/Data | 실패 질문 그룹화, KB 추천, 품질평가 |

### 4주차 — 안정화 + 발표

| 역할 | 할 일 |
|---|---|
| PM | 제안서/발표자료 최종화 |
| Frontend | UI polish, 모바일 확인 |
| Backend | 배포/백업/성능 점검 |
| AI/Data | 테스트 리포트, 데모 질문 고정 |

## 10. 데모 시나리오

1. 정상 민원: “이사했는데 전입신고 어떻게 해요?”
2. 모호한 질문: “신고하려고요.”
3. 기관 연결: “아름동에서 등본 발급 어디서 해요?”
4. 폴백: “내 자동차세 체납액 알려줘.”
5. 개인정보: “주민등록번호 900101-1234567인데 확인해줘.”
6. 관리자: 답변 실패 질문 → KB 개선 추천 → 민원 자동 분석

## 11. 완료 기준

| 영역 | 완료 기준 |
|---|---|
| 시민용 | 대표 질문 30개 이상 정상/폴백 동작 |
| 관리자 | KPI/실패질문/자동분석/KB추천/품질리포트 표시 |
| 데이터 | KB 100개 이상, 테스트 질문 100개 |
| 품질 | 출처 표기율 100%, 평균 응답 3초 이내 목표 |
| 발표 | 데모 질문 6개가 안정적으로 동작 |

## 12. 개발 중 주의사항

- 개인정보 원문 저장 금지
- 출처 없는 답변 금지
- LLM이 지어내는 답변 방지
- 복지·세금·인허가 최종 판단은 담당 부서 연결
- 4주차에는 신규 기능 추가보다 안정화 우선
- 발표 직전에는 배포 구조 변경 금지
