from pathlib import Path

from fastapi.testclient import TestClient

from phatsima_ai.api.app import create_app


def test_wifi_support_enquiry(tmp_path: Path) -> None:
    app = create_app(db_path=tmp_path / "test.db")
    with TestClient(app) as client:
        response = client.post(
            "/enquiries",
            json={
                "customer_id": "customer-001",
                "channel": "api",
                "message": "  My laptop connects to Wi-Fi, but there is no internet.  ",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["enquiry_id"] == 1
    assert data["customer_id"] == "customer-001"
    assert data["classification"] == "Support request"
    assert data["intent"] == "IT support"
    assert data["service"] == "Network troubleshooting"
    assert data["risk"] == "low"
    assert "Windows version" in data["missing_info"]
    assert data["next_action"] == "Collect diagnostic information"
    assert data["human_approval_required"] is False
    assert data["ticket_creation_allowed"] is True
    assert data["technical_commands_approval"] == "required"


def test_quotation_enquiry_requires_human_approval(tmp_path: Path) -> None:
    app = create_app(db_path=tmp_path / "test.db")
    with TestClient(app) as client:
        response = client.post(
            "/enquiries",
            json={
                "customer_id": "customer-002",
                "message": "How much do you charge for an office network setup quotation?",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["classification"] == "Quotation request"
    assert data["human_approval_required"] is True


def test_rejects_extra_fields_and_blank_messages(tmp_path: Path) -> None:
    app = create_app(db_path=tmp_path / "test.db")
    with TestClient(app) as client:
        extra_field_resp = client.post(
            "/enquiries",
            json={
                "customer_id": "customer-003",
                "message": "Help with router",
                "unexpected_field": "malicious",
            },
        )
        blank_msg_resp = client.post(
            "/enquiries",
            json={
                "customer_id": "customer-003",
                "message": "   ",
            },
        )

    assert extra_field_resp.status_code == 422
    assert blank_msg_resp.status_code == 422