"""Bounded prompt for the closed Upstage topic and coverage selector."""

from __future__ import annotations

import json

from sejong_ai_api.chat.classification import SafeQuestion
from sejong_ai_api.chat.topic_catalog import TopicCatalog
from sejong_ai_api.db.models import Intent

_MAX_QUESTION_CHARS = 1024
_PROVIDER_INTENT_ORDER = (
    Intent.MOVE_IN_RESIDENT_REGISTRATION,
    Intent.CERTIFICATE_ISSUANCE,
    Intent.BULKY_WASTE,
    Intent.LOCAL_TAX_GENERAL,
)
_SYSTEM_MESSAGE = (
    "JSON only;"
    "keys=route,intent,topic_id,coverage_id,pending_slot;"
    "5 strings;"
    "no extra/prose/MD;"
    "NONE uppercase ASCII;"
    "translation/null/empty forbidden;"
    "intents=MOVE_IN_RESIDENT_REGISTRATION|CERTIFICATE_ISSUANCE|"
    "BULKY_WASTE|LOCAL_TAX_GENERAL|NONE;"
    "cat[intent]=[topic_id,coverage_id,coverage_label,approved_examples];"
    "SUPPORTED=one cat row covers ask;"
    "NO_TOPIC_MATCH=supported intent/no row covers asked fact/procedure;"
    "NEEDS_FOLLOWUP=missing/ambiguous detail blocks safe choice;"
    "CIVIC_SCOPE_GAP=government/admin service outside intents;"
    "NON_CIVIC=not government/admin service;"
    "decide in this order and stop at the first match;"
    "1 ask is only a bare category word(서류/증명서/신고/민원/발급) "
    "with no specific kind=NEEDS_FOLLOWUP;"
    "2 asked service/item fits one cat row=SUPPORTED;"
    "3 asked service/item belongs to a cat intent but no row covers it=NO_TOPIC_MATCH;"
    "4 asked service is government/admin but outside cat intents=CIVIC_SCOPE_GAP;"
    "5 not a government/admin service=NON_CIVIC;"
    "never widen a row to a service it does not name;"
    "pick narrowest covered row;"
    "exclusions bind;"
    "SUPPORTED:intent/topic_id/coverage_id=same row,pending_slot=NONE;"
    "NO_TOPIC_MATCH:intent=supported,other3=NONE;"
    "CIVIC_SCOPE_GAP/NON_CIVIC:other4=NONE;"
    "NEEDS_FOLLOWUP:topic_id/coverage_id=NONE;"
    "pairs=NONE:DOMAIN|supported:TOPIC_CHOICE/REGION|"
    "CERTIFICATE_ISSUANCE:CERTIFICATE_KIND|BULKY_WASTE:WASTE_ITEM;"
)


def _build_grouped_catalog(catalog: TopicCatalog) -> dict[str, list[list[object]]]:
    grouped: dict[str, list[list[object]]] = {}
    for intent in _PROVIDER_INTENT_ORDER:
        rows: list[list[object]] = [
            [
                topic.record.public_id,
                topic.coverage.coverage_id,
                topic.coverage.coverage_label,
                list(topic.record.question_examples[:2]),
            ]
            for topic in catalog.topics
            if topic.record.category is intent
        ]
        if rows:
            grouped[intent.value] = rows
    return grouped


def build_classifier_messages(
    question: SafeQuestion,
    catalog: TopicCatalog,
    *,
    max_input_chars: int,
) -> tuple[dict[str, str], ...]:
    """Serialize every eligible governed topic without truncation or sampling."""

    if (
        type(question) is not SafeQuestion
        or type(catalog) is not TopicCatalog
        or not catalog.provider_eligible
        or type(max_input_chars) is not int
        or max_input_chars <= 0
        or max_input_chars > _MAX_QUESTION_CHARS
        or len(question.text) > max_input_chars
    ):
        raise ValueError("CLASSIFIER_PROMPT_INVALID")
    first = catalog.topics[0]
    payload = {
        "ask": question.text,
        "cat": _build_grouped_catalog(catalog),
        "ex": [
            [
                "SUPPORTED",
                first.record.category.value,
                first.record.public_id,
                first.coverage.coverage_id,
                "NONE",
            ],
            ["NEEDS_FOLLOWUP", "NONE", "NONE", "NONE", "DOMAIN"],
            ["CIVIC_SCOPE_GAP", "NONE", "NONE", "NONE", "NONE"],
        ],
    }
    return (
        {"role": "system", "content": _SYSTEM_MESSAGE},
        {
            "role": "user",
            "content": json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        },
    )


def estimate_classifier_input_upper_bound(
    messages: tuple[dict[str, str], ...],
) -> int:
    """Conservatively overestimate Korean token use before transport."""

    return sum(len(message["content"]) for message in messages)


__all__ = [
    "build_classifier_messages",
    "estimate_classifier_input_upper_bound",
]
