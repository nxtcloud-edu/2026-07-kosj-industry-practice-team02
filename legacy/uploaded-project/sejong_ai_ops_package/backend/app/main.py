from __future__ import annotations

from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional
import csv
import re
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

app = FastAPI(title="Sejong AI Civil Service Platform", version="0.1.0")

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    area: Optional[str] = None

class ChatResponse(BaseModel):
    answer_status: str
    intent: str
    confidence: float
    title: str
    summary: str
    steps: list[str] = []
    documents: list[str] = []
    fee: Optional[str] = None
    processing_time: Optional[str] = None
    department: Optional[str] = None
    sources: list[dict] = []
    fallback_reason: Optional[str] = None
    followup_questions: list[str] = []


def load_csv(name: str) -> list[dict]:
    path = DATA / name
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def mask_pii(text: str) -> tuple[str, bool]:
    original = text
    text = re.sub(r"\d{6}-\d{7}", "[주민등록번호]", text)
    text = re.sub(r"01[016789]-?\d{3,4}-?\d{4}", "[전화번호]", text)
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[이메일]", text)
    return text, text != original

KEYWORDS = {
    "MOVE_IN_REPORT": ["전입", "이사", "주민등록", "세대주"],
    "CERTIFICATE_ISSUE": ["등본", "초본", "증명서", "무인민원", "발급"],
    "BULKY_WASTE": ["대형폐기물", "침대", "소파", "스티커", "폐가전", "버리"],
    "LOCAL_TAX": ["자동차세", "지방세", "재산세", "세금", "체납", "납부"],
    "WELFARE": ["복지", "기초생활", "긴급복지", "지원"],
    "YOUTH_JOB": ["청년", "월세", "일자리", "지원금"],
    "BUSINESS_PERMIT": ["영업신고", "음식점", "가게", "인허가", "창업"],
    "TRAFFIC_PARKING": ["불법주정차", "주차", "교통", "버스"],
    "LIFE_ENV": ["소음", "환경", "반려동물", "동물등록", "무단투기"],
    "OFFICE_LOOKUP": ["주민센터", "행정복지센터", "전화번호", "위치", "어디"],
    "STATUS_LOOKUP": ["접수번호", "조회", "처리", "상태", "SJ-"],
}

PRIVATE_LOOKUP_TERMS = ["내 자동차세", "내 세금", "체납액", "내 복지", "대상 여부", "확인해줘"]


def classify(question: str) -> tuple[str, float]:
    if "[주민등록번호]" in question or "[전화번호]" in question:
        return "UNSAFE_OR_PRIVATE", 0.99
    scores = Counter()
    for intent, kws in KEYWORDS.items():
        for kw in kws:
            if kw in question:
                scores[intent] += 1
    if not scores:
        return "UNKNOWN", 0.30
    intent, score = scores.most_common(1)[0]
    return intent, min(0.55 + score * 0.15, 0.95)


def search_kb(intent: str, question: str) -> Optional[dict]:
    rows = load_csv("kb_seed.csv")
    for row in rows:
        if row["intent"] == intent:
            return row
    return None


def make_fallback(intent: str, reason: str) -> ChatResponse:
    dept = {
        "LOCAL_TAX": "세정과",
        "WELFARE": "복지정책과 또는 주민센터 복지 담당",
        "BULKY_WASTE": "자원순환과",
        "BUSINESS_PERMIT": "인허가 담당 부서",
    }.get(intent, "민원 담당 부서")
    return ChatResponse(
        answer_status="fallback",
        intent=intent,
        confidence=0.0,
        title="담당 부서 확인이 필요한 민원입니다",
        summary="현재 확인된 행정 지식베이스만으로는 정확한 답변을 제공하기 어려워 담당 부서 안내로 연결합니다.",
        department=dept,
        fallback_reason=reason,
        sources=[],
        followup_questions=[]
    )

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    q, pii = mask_pii(req.question.strip())
    intent, conf = classify(q)

    if pii:
        return make_fallback("UNSAFE_OR_PRIVATE", "PRIVATE_INFO_DETECTED")
    if any(term in q for term in PRIVATE_LOOKUP_TERMS):
        return make_fallback(intent, "PRIVATE_LOOKUP")
    if intent == "UNKNOWN" or conf < 0.55:
        return ChatResponse(
            answer_status="clarification",
            intent="UNKNOWN",
            confidence=conf,
            title="어떤 민원을 원하시나요?",
            summary="질문만으로는 민원 유형을 특정하기 어렵습니다. 아래 선택지 중 가까운 항목을 골라주세요.",
            followup_questions=["전입신고", "증명서 발급", "대형폐기물", "지방세", "복지", "인허가"]
        )
    if intent == "STATUS_LOOKUP":
        return ChatResponse(
            answer_status="fallback",
            intent=intent,
            confidence=conf,
            title="접수번호 조회는 별도 메뉴에서 확인할 수 있습니다",
            summary="MVP에서는 시연용 mock 접수번호 조회를 제공합니다. 실제 행정 시스템 연동은 고도화 단계에서 진행합니다.",
            fallback_reason="STATUS_LOOKUP_ROUTE"
        )

    kb = search_kb(intent, q)
    if not kb:
        return make_fallback(intent, "KB_MISSING")
    return ChatResponse(
        answer_status="answered",
        intent=intent,
        confidence=conf,
        title=kb["title"],
        summary=kb["answer_summary"],
        steps=[s.strip() for s in kb["procedure_steps"].split(">")],
        documents=[s.strip() for s in kb["required_documents"].split(";")],
        fee=kb["fee"],
        processing_time=kb["processing_time"],
        department=kb["department"],
        sources=[{"id": kb["kb_id"], "title": kb["source_title"], "last_updated": kb["last_updated"]}],
        fallback_reason=None,
        followup_questions=[]
    )

@app.get("/api/offices/search")
def search_offices(area: Optional[str] = Query(None), service: Optional[str] = Query(None)):
    rows = load_csv("offices_seed.csv")
    result = []
    for row in rows:
        if area and area not in row["area_name"] and area not in row["office_name"]:
            continue
        if service and service not in row["services"]:
            continue
        result.append(row)
    return {"items": result[:10]}

@app.get("/api/status/{receipt_no}")
def status(receipt_no: str):
    for row in load_csv("mock_status_cases.csv"):
        if row["receipt_no"] == receipt_no:
            return row
    return {"receipt_no": receipt_no, "status": "조회 결과 없음", "message": "시연용 mock 데이터에 없는 접수번호입니다."}

@app.get("/api/admin/stats")
def admin_stats():
    logs = load_csv("admin_mock_logs.csv")
    total = len(logs)
    answered = sum(1 for r in logs if r["answer_status"] == "answered")
    fallback = sum(1 for r in logs if r["answer_status"] == "fallback")
    avg_ms = sum(int(r["response_time_ms"]) for r in logs) // max(total, 1)
    pii = sum(1 for r in logs if "[주민등록번호]" in r["question_masked"] or "[전화번호]" in r["question_masked"])
    return {
        "total_questions": total,
        "answer_success_rate": round(answered / total, 2),
        "fallback_rate": round(fallback / total, 2),
        "avg_response_time_ms": avg_ms,
        "source_coverage_rate": 1.0,
        "pii_detected_count": pii,
        "new_kb_candidates": 3,
    }

@app.get("/api/admin/failed-questions")
def failed_questions():
    logs = load_csv("admin_mock_logs.csv")
    items=[]
    for r in logs:
        if r["answer_status"] == "fallback":
            action = {
                "KB_MISSING": "FAQ 추가 필요",
                "PRIVATE_LOOKUP": "공식 시스템/담당 부서 안내 유지",
                "NEEDS_LATEST_INFO": "최신 공고 확인 필요",
                "PRIVATE_INFO_DETECTED": "개인정보 마스킹 정책 유지",
            }.get(r["fallback_reason"], "관리자 검토 필요")
            items.append({
                "question": r["question_masked"],
                "intent": r["intent"],
                "failure_reason": r["fallback_reason"],
                "recommended_action": action,
                "status": "new",
            })
    return {"items": items}

@app.get("/api/admin/analytics")
def analytics():
    logs = load_csv("admin_mock_logs.csv")
    by_intent = Counter(r["intent"] for r in logs)
    by_area = Counter(r["user_area"] or "미상" for r in logs)
    by_dept = Counter(r["office_routed"] or "미상" for r in logs)
    return {
        "by_intent": by_intent,
        "by_area": by_area,
        "by_department": by_dept,
        "surge_alerts": [
            {"title": "청년 월세 지원 관련 질문 증가", "growth_rate": 0.60, "recommendation": "최신 신청 기간 FAQ 보완"},
            {"title": "반려동물 등록 문의 발생", "growth_rate": 0.25, "recommendation": "생활/환경 카테고리 FAQ 추가"},
        ]
    }

@app.get("/api/admin/kb-recommendations")
def kb_recommendations():
    return {"items": [
        {"title": "반려동물 등록 FAQ 추가", "related_questions": 12, "priority_score": 86, "reason": "KB_MISSING"},
        {"title": "청년 월세 지원 신청 기간 최신화", "related_questions": 15, "priority_score": 84, "reason": "NEEDS_LATEST_INFO"},
        {"title": "대형폐기물 품목별 수수료 보완", "related_questions": 21, "priority_score": 92, "reason": "SOURCE_INSUFFICIENT"},
    ]}

@app.get("/api/admin/quality-report")
def quality_report():
    return {
        "test_cases": 100,
        "correct": 82,
        "partial": 11,
        "wrong": 7,
        "accuracy": 0.82,
        "source_rate": 1.0,
        "fallback_appropriateness": 0.90,
        "pii_masking_rate": 1.0,
        "avg_response_time_ms": 1800,
    }
