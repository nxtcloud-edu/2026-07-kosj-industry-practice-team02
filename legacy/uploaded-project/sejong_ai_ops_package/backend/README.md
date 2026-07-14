# Backend Starter

## 실행

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 주요 엔드포인트

- `POST /api/chat`
- `GET /api/admin/stats`
- `GET /api/admin/failed-questions`
- `GET /api/admin/analytics`
- `GET /api/admin/kb-recommendations`
- `GET /api/status/{receipt_no}`
