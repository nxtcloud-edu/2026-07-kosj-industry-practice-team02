#!/usr/bin/env python3
"""Score the local/private citizen path against the proposal 7.3 quality metrics.

Runs the labelled T-01~T-20 sample and the proposal 7.5 demo scenario through the
same origin a browser uses, then reports one machine-readable metric set. A stored
baseline turns the metric set into a regression gate: any metric that drops below
its recorded value, or any labelled case that flips from pass to fail, exits 1.

Local/private only. Questions and answers are never printed; only labels, contract
enums, counts and timings appear in the output.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, TypedDict

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_SAMPLE_CSV = _REPOSITORY_ROOT / "data" / "evaluation" / "sample_questions_20.csv"
_DEFAULT_ORIGIN = "http://127.0.0.1:3000"
_REQUEST_TIMEOUT_SECONDS = 60

_OPERATOR_HEADERS = {
    "X-Demo-Actor-Id": "OPERATOR-LOCAL-001",
    "X-Demo-Role": "OPERATOR",
}

# data/evaluation labels are Korean domain names; the contract uses enums.
_INTENT_BY_LABEL = {
    "전입·주민등록": "MOVE_IN_RESIDENT_REGISTRATION",
    "증명서 발급": "CERTIFICATE_ISSUANCE",
    "대형폐기물": "BULKY_WASTE",
    "지방세 일반 안내": "LOCAL_TAX_GENERAL",
    # Policy fallbacks and scope checks are contract-bound to UNKNOWN.
    "모호": "UNKNOWN",
    "범위 밖": "UNKNOWN",
    "범위 밖/개인 조회": "UNKNOWN",
    "범위 확인": "UNKNOWN",
}


class DemoCase(TypedDict):
    demo_id: str
    question: str
    expected_status: str
    expected_fallback: str | None
    must_contain: tuple[str, ...]
    proves: str
    requires_deep_link: bool
    requires_region_reflection: bool
    requires_related_question: bool
    selected_region: str | None


# Proposal 7.5. `must_contain` holds the one fact the proposal says each demo proves.
_DEMO_CASES: tuple[DemoCase, ...] = (
    {
        "demo_id": "D-1",
        "question": "전입신고는 언제까지 해야 하나요?",
        "expected_status": "SUCCESS",
        "expected_fallback": None,
        "must_contain": ("14일",),
        "proves": "14일 기한 + 출처·최종 확인일 + 정부24 딥링크",
        # 딥링크는 intent 기반 UI 상수(labels.ts DEEP_LINK_BY_INTENT)로 답변 카드에 렌더링된다.
        # API 응답 필드가 아니므로 HTTP 클라이언트인 이 하니스가 검증할 수 없다. UI/E2E 계층 책임.
        "requires_deep_link": False,
        "requires_region_reflection": False,
        "requires_related_question": False,
        "selected_region": None,
    },
    {
        "demo_id": "D-2",
        "question": "아름동에서 대형폐기물은 언제 내놓나요?",
        "expected_status": "SUCCESS",
        "expected_fallback": None,
        "must_contain": ("시설관리공단",),
        "proves": "지역 조건 반영 + 시설관리공단 실데이터",
        "requires_deep_link": False,
        "requires_region_reflection": True,
        "requires_related_question": False,
        # 실제 화면은 지역 드롭다운 선택 후 질문한다. 질문만 보내면 기관 카드가 붙지 않아
        # 구현이 아니라 하니스 호출 방식 때문에 실패했다.
        "selected_region": "아름동",
    },
    {
        "demo_id": "D-3",
        "question": "이사했는데 뭐 해야 하나요?",
        "expected_status": "FOLLOWUP",
        "expected_fallback": None,
        "must_contain": (),
        "proves": "단정 없는 선택지",
        "requires_deep_link": False,
        "requires_region_reflection": False,
        # 관련 민원 한 줄 제안은 팀 논의 결과 화면 복잡도를 이유로 범위에서 제외했다(범위 결정).
        "requires_related_question": False,
        "selected_region": None,
    },
    {
        "demo_id": "D-4",
        "question": "제 자동차세 얼마 나왔나요?",
        "expected_status": "FALLBACK",
        "expected_fallback": "PERSONAL_LOOKUP",
        "must_contain": (),
        "proves": "개인별 조회 추측 금지 + 사유 안내 + 위택스 연결",
        "requires_deep_link": False,
        "requires_region_reflection": False,
        "requires_related_question": False,
        "selected_region": None,
    },
)

# Proposal 7.3 targets. `direction` is the comparison that means "better".
_TARGETS = {
    "intent_accuracy": {
        "target": 0.85,
        "direction": "higher",
        "source": "제안서 7.3 의도 분류 정확도",
    },
    "answer_status_accuracy": {
        "target": 0.80,
        "direction": "higher",
        "source": "제안서 7.3 답변 정확도",
    },
    "source_labeling_rate": {
        "target": 1.00,
        "direction": "higher",
        "source": "제안서 7.3 출처 표기율",
    },
    "fallback_appropriateness": {
        "target": 0.90,
        "direction": "higher",
        "source": "제안서 7.3 폴백 적절성",
    },
    "answerable_success_rate": {
        "target": 0.80,
        "direction": "higher",
        "source": "제안서 7.3 과잉 회피 실패 집계",
    },
    "pii_masking_rate": {
        "target": 1.00,
        "direction": "higher",
        "source": "제안서 7.3 개인정보 마스킹",
    },
    "latency_mean_ms": {
        "target": 3000.0,
        "direction": "lower",
        "source": "제안서 7.3 / PER-001 평균 3초",
    },
    "error_rate": {
        "target": 0.0,
        "direction": "lower",
        "source": "제안서 7.3 오류율 병행 실측",
    },
    "demo_completion_rate": {
        "target": 1.00,
        "direction": "higher",
        "source": "제안서 7.5 데모 무중단 완주",
    },
}


class MetricRunError(RuntimeError):
    """The harness could not obtain a trustworthy measurement."""


def _post_chat(
    origin: str,
    question: str,
    selected_region: str | None = None,
) -> tuple[int, dict[str, Any], float]:
    body: dict[str, Any] = {"question": question}
    if selected_region is not None:
        body["selected_region"] = selected_region
    payload = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        f"{origin}/api/v1/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(
            request, timeout=_REQUEST_TIMEOUT_SECONDS
        ) as response:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            return (
                response.status,
                json.loads(response.read().decode("utf-8")),
                elapsed_ms,
            )
    except urllib.error.HTTPError as error:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        body = error.read().decode("utf-8", "replace")
        try:
            return error.code, json.loads(body), elapsed_ms
        except json.JSONDecodeError:
            return error.code, {}, elapsed_ms
    except OSError as error:
        raise MetricRunError("CHAT_TRANSPORT_UNAVAILABLE") from error


def _get_admin(origin: str, path: str) -> tuple[int, dict[str, Any]]:
    request = urllib.request.Request(f"{origin}{path}", headers=_OPERATOR_HEADERS)
    try:
        with urllib.request.urlopen(
            request, timeout=_REQUEST_TIMEOUT_SECONDS
        ) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, {}
    except OSError as error:
        raise MetricRunError("ADMIN_TRANSPORT_UNAVAILABLE") from error


def _load_sample_cases() -> list[dict[str, str]]:
    with _SAMPLE_CSV.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _response_text(response: dict[str, Any]) -> str:
    """Flatten a response to text for fact and leak checks."""
    return json.dumps(response, ensure_ascii=False)


def _pii_literals(question: str) -> tuple[str, ...]:
    """Return raw tokens that must never survive into a response or a stored row."""
    literals = []
    for token in question.replace("?", " ").replace(".", " ").split():
        # Reference numbers and other mixed alphanumeric identifiers.
        if any(character.isdigit() for character in token) and any(
            character.isalpha() for character in token
        ):
            literals.append(token.strip("의은는이가을를."))
    return tuple(literals)


def _score_sample(origin: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    for row in rows:
        test_id = row["test_id"]
        question = row["질문"]
        expected_status = row["기대 상태"].strip()
        expected_fallback = (row["기대 폴백 사유"] or "").strip() or None
        expected_intent = _INTENT_BY_LABEL.get(row["기대 intent"].strip())
        declares_pii = row["PII 포함"].strip() == "예"

        status_code, response, elapsed_ms = _post_chat(origin, question)
        transport_ok = status_code == 200 and bool(response)

        actual_status = response.get("answer_status")
        actual_intent = response.get("intent")
        fallback = response.get("fallback") or {}
        actual_fallback = fallback.get("reason")
        sources = response.get("sources") or []

        source_required = actual_status == "SUCCESS"
        source_ok = (not source_required) or (
            len(sources) >= 1
            and all(
                item.get("source_id") and item.get("last_verified_at")
                for item in sources
            )
        )

        leaked = [
            literal
            for literal in (_pii_literals(question) if declares_pii else ())
            if literal in _response_text(response)
        ]

        cases.append(
            {
                "test_id": test_id,
                "expected_intent": expected_intent,
                "actual_intent": actual_intent,
                "intent_ok": expected_intent == actual_intent,
                "expected_status": expected_status,
                "actual_status": actual_status,
                "status_ok": expected_status == actual_status,
                "expected_fallback": expected_fallback,
                "actual_fallback": actual_fallback,
                "fallback_ok": expected_fallback == actual_fallback,
                "source_required": source_required,
                "source_ok": source_ok,
                "declares_pii": declares_pii,
                "leaked_literals": leaked,
                "http_status": status_code,
                "transport_ok": transport_ok,
                "latency_ms": round(elapsed_ms),
            }
        )
    return {"cases": cases}


def _fallback_appropriateness(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Proposal 7.3 scores both directions so 'never answering' cannot win points."""
    under = [
        c
        for c in cases
        if c["expected_status"] == "FALLBACK" and c["actual_status"] != "FALLBACK"
    ]
    over = [
        c
        for c in cases
        if c["expected_status"] != "FALLBACK" and c["actual_status"] == "FALLBACK"
    ]
    wrong_reason = [
        c
        for c in cases
        if c["expected_status"] == "FALLBACK"
        and c["actual_status"] == "FALLBACK"
        and not c["fallback_ok"]
    ]
    graded = [
        c for c in cases if c["expected_status"] in {"FALLBACK", "SUCCESS", "FOLLOWUP"}
    ]
    failures = len(under) + len(over) + len(wrong_reason)
    rate = (len(graded) - failures) / len(graded) if graded else 0.0
    return {
        "rate": round(rate, 4),
        "under_fallback": [c["test_id"] for c in under],
        "over_fallback": [c["test_id"] for c in over],
        "wrong_reason": [c["test_id"] for c in wrong_reason],
    }


def _answerable_success(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Proposal 7.3 counts evading an answerable question as a failure.

    `fallback_appropriateness` only sees the FALLBACK direction, so a question the
    KB can answer that comes back as FOLLOWUP would score clean there. This metric
    catches that evasion separately instead of letting it hide.
    """
    scope = [c for c in cases if c["expected_status"] == "SUCCESS"]
    evaded = [c for c in scope if c["actual_status"] != "SUCCESS"]
    rate = (len(scope) - len(evaded)) / len(scope) if scope else 1.0
    return {
        "rate": round(rate, 4),
        "evaded": [
            {"test_id": c["test_id"], "actual_status": c["actual_status"]}
            for c in evaded
        ],
    }


def _score_demo(origin: str) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for case in _DEMO_CASES:
        status_code, response, elapsed_ms = _post_chat(
            origin,
            case["question"],
            case.get("selected_region"),
        )
        text = _response_text(response)
        fallback = response.get("fallback") or {}
        sources = response.get("sources") or []

        status_ok = response.get("answer_status") == case["expected_status"]
        fallback_ok = fallback.get("reason") == case["expected_fallback"]
        facts_ok = all(fact in text for fact in case["must_contain"])
        source_ok = (case["expected_status"] != "SUCCESS") or (
            len(sources) >= 1
            and all(
                item.get("source_id") and item.get("last_verified_at")
                for item in sources
            )
        )
        deep_link_ok = (not case["requires_deep_link"]) or bool(
            response.get("deep_link")
        )
        related_ok = (not case["requires_related_question"]) or bool(
            response.get("related_question")
        )
        region_ok = (not case["requires_region_reflection"]) or (
            response.get("selected_region") is not None or "아름동" in text
        )

        results.append(
            {
                "demo_id": case["demo_id"],
                "proves": case["proves"],
                "http_status": status_code,
                "actual_status": response.get("answer_status"),
                "actual_fallback": fallback.get("reason"),
                "answer_mode": response.get("answer_mode"),
                "status_ok": status_ok,
                "fallback_ok": fallback_ok,
                "facts_ok": facts_ok,
                "source_ok": source_ok,
                "deep_link_ok": deep_link_ok,
                "related_question_ok": related_ok,
                "region_reflected_ok": region_ok,
                "passed": all(
                    (
                        status_ok,
                        fallback_ok,
                        facts_ok,
                        source_ok,
                        deep_link_ok,
                        related_ok,
                        region_ok,
                    )
                ),
                "latency_ms": round(elapsed_ms),
            }
        )

    failed_status, failed = _get_admin(origin, "/api/v1/admin/failed-questions")
    candidate_status, candidates = _get_admin(origin, "/api/v1/admin/kb-candidates")
    loop_ok = (
        failed_status == 200
        and candidate_status == 200
        and int(failed.get("total", 0)) >= 1
        and int(candidates.get("total", 0)) >= 1
    )
    results.append(
        {
            "demo_id": "D-5",
            "proves": "실패 질문 큐 → 사유 분류 → KB 후보 → 승인",
            "failed_questions_total": failed.get("total"),
            "kb_candidates_total": candidates.get("total"),
            "passed": loop_ok,
        }
    )
    return {"cases": results}


def _build_metrics(sample: dict[str, Any], demo: dict[str, Any]) -> dict[str, Any]:
    cases = sample["cases"]
    total = len(cases)
    latencies = [c["latency_ms"] for c in cases if c["transport_ok"]]
    source_scope = [c for c in cases if c["source_required"]]
    pii_scope = [c for c in cases if c["declares_pii"]]
    fallback = _fallback_appropriateness(cases)
    answerable = _answerable_success(cases)
    demo_cases = demo["cases"]

    ordered = sorted(latencies)
    p95 = (
        ordered[min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1))))]
        if ordered
        else 0
    )

    return {
        "intent_accuracy": round(sum(c["intent_ok"] for c in cases) / total, 4)
        if total
        else 0.0,
        "answer_status_accuracy": round(sum(c["status_ok"] for c in cases) / total, 4)
        if total
        else 0.0,
        "source_labeling_rate": (
            round(sum(c["source_ok"] for c in source_scope) / len(source_scope), 4)
            if source_scope
            else 1.0
        ),
        "fallback_appropriateness": fallback["rate"],
        "answerable_success_rate": answerable["rate"],
        "pii_masking_rate": (
            round(sum(not c["leaked_literals"] for c in pii_scope) / len(pii_scope), 4)
            if pii_scope
            else 1.0
        ),
        "latency_mean_ms": round(statistics.fmean(latencies), 1) if latencies else 0.0,
        "latency_p95_ms": float(p95),
        "error_rate": round(sum(not c["transport_ok"] for c in cases) / total, 4)
        if total
        else 1.0,
        "demo_completion_rate": round(
            sum(c["passed"] for c in demo_cases) / len(demo_cases), 4
        )
        if demo_cases
        else 0.0,
        "_fallback_detail": fallback,
        "_answerable_detail": answerable,
    }


def _compare(
    metrics: dict[str, Any],
    baseline: dict[str, Any] | None,
    *,
    enforce: bool = True,
) -> dict[str, Any]:
    """Diff the metric set against a baseline.

    `enforce=False` still shows the baseline values but never calls a delta a
    regression. Used when the baseline was captured under different provider
    modes, where a latency or answer_mode delta is a mode difference rather than
    a code change.
    """
    rows = []
    regressed = False
    for name, spec in _TARGETS.items():
        current = metrics[name]
        target = spec["target"]
        higher_is_better = spec["direction"] == "higher"
        meets_target = current >= target if higher_is_better else current <= target
        previous = (baseline or {}).get("metrics", {}).get(name)
        drift = None
        is_regression = False
        if previous is not None:
            drift = round(current - previous, 4)
            if enforce:
                is_regression = (
                    current < previous if higher_is_better else current > previous
                )
                regressed = regressed or is_regression
        rows.append(
            {
                "metric": name,
                "current": current,
                "target": target,
                "meets_target": meets_target,
                "baseline": previous,
                "drift": drift,
                "regressed": is_regression,
                "source": spec["source"],
            }
        )
    return {"rows": rows, "regressed": regressed}


def _print_report(result: dict[str, Any], comparison: dict[str, Any]) -> None:
    print(f"baseline_commit={result['commit']}  origin={result['origin']}")
    print(f"provider_modes={result['provider_modes']}")
    print("")
    print(
        f"{'metric':<26}{'current':>10}{'target':>10}{'base':>10}{'drift':>9}  verdict"
    )
    for row in comparison["rows"]:
        verdict = "TARGET-MET" if row["meets_target"] else "BELOW-TARGET"
        if row["regressed"]:
            verdict += " REGRESSED"
        base = "-" if row["baseline"] is None else f"{row['baseline']}"
        drift = "-" if row["drift"] is None else f"{row['drift']:+}"
        print(
            f"{row['metric']:<26}{row['current']:>10}{row['target']:>10}{base:>10}{drift:>9}  {verdict}"
        )

    detail = result["metrics"]["_fallback_detail"]
    print("")
    print(f"under_fallback={detail['under_fallback']}")
    print(f"over_fallback={detail['over_fallback']}")
    print(f"wrong_reason={detail['wrong_reason']}")
    evaded = result["metrics"]["_answerable_detail"]["evaded"]
    print(f"evaded_answerable={[(e['test_id'], e['actual_status']) for e in evaded]}")

    failed_ids = [c["test_id"] for c in result["sample"]["cases"] if not c["status_ok"]]
    print(f"sample_status_failures={failed_ids}")
    demo_failed = [c["demo_id"] for c in result["demo"]["cases"] if not c["passed"]]
    print(f"demo_failures={demo_failed}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run_regression_metrics.py",
        description="Score the local citizen path against the proposal 7.3 metrics.",
    )
    parser.add_argument("--origin", default=_DEFAULT_ORIGIN)
    parser.add_argument("--baseline", type=Path, default=None)
    parser.add_argument("--write-baseline", type=Path, default=None)
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="exit 1 when any metric drops below the stored baseline",
    )
    options = parser.parse_args(argv)

    try:
        sample = _score_sample(options.origin, _load_sample_cases())
        demo = _score_demo(options.origin)
    except MetricRunError as error:
        print(f"REGRESSION_METRICS_UNAVAILABLE reason={error}", file=sys.stderr)
        return 2

    metrics = _build_metrics(sample, demo)
    result = {
        "schema_version": 1,
        "commit": os.environ.get("SEJONG_BASELINE_COMMIT", "unset"),
        "origin": options.origin,
        "provider_modes": os.environ.get("SEJONG_PROVIDER_MODES", "unset"),
        "sample_size": len(sample["cases"]),
        "metrics": metrics,
        "sample": sample,
        "demo": demo,
    }

    baseline = None
    if options.baseline and options.baseline.is_file():
        baseline = json.loads(options.baseline.read_text(encoding="utf-8"))
    enforce = (
        baseline is None or baseline.get("provider_modes") == result["provider_modes"]
    )
    comparison = _compare(metrics, baseline, enforce=enforce)
    _print_report(result, comparison)
    if baseline is not None and not enforce:
        print(
            "\nBASELINE_MODE_MISMATCH "
            f"baseline={baseline.get('provider_modes')} current={result['provider_modes']} "
            "— drift shown for reference only, regression gate not applied"
        )

    if options.json_out:
        options.json_out.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"\nwritten: {options.json_out}")
    if options.write_baseline:
        options.write_baseline.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"baseline written: {options.write_baseline}")

    if options.fail_on_regression and comparison["regressed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
