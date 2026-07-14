# 06. DB/API 명세 요약

## 1. API 요약

자세한 OpenAPI 명세는 `api/openapi.yaml`을 참고한다.

### 시민용

- `POST /api/chat`
- `GET /api/categories`
- `GET /api/services`
- `GET /api/offices/search`
- `GET /api/status/{receipt_no}`
- `POST /api/feedback`

### 관리자용

- `GET /api/admin/stats`
- `GET /api/admin/failed-questions`
- `GET /api/admin/analytics`
- `GET /api/admin/kb-recommendations`
- `GET /api/admin/quality-report`
- `GET /api/admin/department-routing`
- `POST /api/admin/weekly-report`

## 2. 주요 응답 JSON

### `/api/chat`

```json
{
  "answer_status": "answered",
  "intent": "MOVE_IN_REPORT",
  "confidence": 0.91,
  "title": "전입신고 안내",
  "summary": "전입신고는 이사 후 새 주소를 등록하는 민원입니다.",
  "steps": ["새 주소 확인", "서류 준비", "온라인 또는 방문 신청"],
  "documents": ["신분증", "전입신고서"],
  "sources": [
    {"id": "KB-001", "title": "전입신고 안내 FAQ", "last_updated": "2026-07-08"}
  ],
  "fallback_reason": null,
  "followup_questions": []
}
```

### `/api/admin/stats`

```json
{
  "total_questions": 328,
  "answer_success_rate": 0.84,
  "fallback_rate": 0.16,
  "avg_response_time_ms": 1700,
  "source_coverage_rate": 1.0,
  "pii_detected_count": 8,
  "new_kb_candidates": 12
}
```
