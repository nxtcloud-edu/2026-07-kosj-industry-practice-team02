from __future__ import annotations

from typing import cast

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sejong_ai_api.admin.service import AdminService
from sejong_ai_api.main import create_app


def enabled_admin_app() -> FastAPI:
    return create_app(admin_enabled=True, admin_service=cast(AdminService, object()))


def test_main_application_does_not_register_admin_routes_by_default() -> None:
    with TestClient(create_app()) as client:
        response = client.get(
            "/api/v1/admin/failed-questions",
            headers={
                "X-Demo-Actor-Id": "OPERATOR-LOCAL-001",
                "X-Demo-Role": "OPERATOR",
            },
        )

    assert response.status_code == 404


def test_main_application_maps_admin_request_validation_to_admin_envelope() -> None:
    with TestClient(enabled_admin_app()) as client:
        response = client.get(
            "/api/v1/admin/failed-questions/not-a-uuid",
            headers={
                "X-Demo-Actor-Id": "OPERATOR-LOCAL-001",
                "X-Demo-Role": "OPERATOR",
            },
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ADMIN_VALIDATION_FAILED"
    assert response.json()["error"]["message"] == "입력값을 확인해 주세요."
    assert "not-a-uuid" not in response.text


def test_generated_openapi_requires_both_fixed_demo_actor_headers() -> None:
    schema = enabled_admin_app().openapi()
    parameters = schema["paths"]["/api/v1/admin/failed-questions"]["get"]["parameters"]
    required_by_name = {item["name"]: item["required"] for item in parameters}

    assert required_by_name["X-Demo-Actor-Id"] is True
    assert required_by_name["X-Demo-Role"] is True
