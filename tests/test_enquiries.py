from pathlib import Path

from fastapi.testclient import TestClient

from phatsima_ai.api.app import create_app


def test_wifi_support_enquiry_auto_creates_ticket(tmp_path: Path) -> None:
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
        tickets = client.get("/tickets").json()

    assert response.status_code == 201
    data = response.json()
    assert data["classification"] == "Support request"
    assert data["service_code"] == "it_wifi_support"
    assert data["department"] == "Support"
    assert data["ticket_id"] == 1
    assert data["lead_id"] is None
    assert data["quotation_id"] is None
    assert len(tickets) == 1
    assert tickets[0]["status"] == "open"


def test_website_enquiry_auto_creates_lead(tmp_path: Path) -> None:
    app = create_app(db_path=tmp_path / "test.db")
    with TestClient(app) as client:
        response = client.post(
            "/enquiries",
            json={
                "customer_id": "customer-002",
                "channel": "whatsapp",
                "message": "My business needs a clean mobile-friendly website connected to WhatsApp.",
            },
        )
        leads = client.get("/leads").json()

    assert response.status_code == 201
    data = response.json()
    assert data["classification"] == "Sales lead"
    assert data["service_code"] == "website_development"
    assert data["department"] == "Engineering"
    assert data["lead_id"] == 1
    assert data["ticket_id"] is None
    assert len(leads) == 1
    assert leads[0]["status"] == "new"


def test_quotation_workflow_and_human_approval(tmp_path: Path) -> None:
    app = create_app(db_path=tmp_path / "test.db")
    with TestClient(app) as client:
        create_resp = client.post(
            "/enquiries",
            json={
                "customer_id": "customer-003",
                "message": "How much do you charge to build a business website?",
            },
        )
        assert create_resp.status_code == 201
        created = create_resp.json()
        assert created["classification"] == "Quotation request"
        assert created["human_approval_required"] is True
        assert created["quotation_id"] == 1

        # Verify initial pending_approval status
        quotes = client.get("/quotations").json()
        assert quotes[0]["status"] == "pending_approval"
        assert quotes[0]["draft_amount_zar"] == 3500

        # Human approves quotation
        decide_resp = client.post(
            "/quotations/1/decide",
            json={"decision": "approved", "reviewer": "Morena"},
        )
        assert decide_resp.status_code == 200
        decided = decide_resp.json()
        assert decided["status"] == "approved"
        assert decided["approved_by"] == "Morena"


def test_community_uplift_creates_no_commercial_records(tmp_path: Path) -> None:
    app = create_app(db_path=tmp_path / "test.db")
    with TestClient(app) as client:
        response = client.post(
            "/enquiries",
            json={
                "customer_id": "ecd-principal-01",
                "message": "I want to attend the Saturday clinic for Bana Pele and eCares help.",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["service_code"] == "community_uplift"
        assert data["ticket_id"] is None
        assert data["lead_id"] is None
        assert data["quotation_id"] is None
        assert client.get("/tickets").json() == []
        assert client.get("/leads").json() == []
        assert client.get("/quotations").json() == []


def test_rejects_extra_fields_and_blank_messages(tmp_path: Path) -> None:
    app = create_app(db_path=tmp_path / "test.db")
    with TestClient(app) as client:
        extra_field_resp = client.post(
            "/enquiries",
            json={
                "customer_id": "customer-004",
                "message": "Help with router",
                "unexpected_field": "malicious",
            },
        )
        blank_msg_resp = client.post(
            "/enquiries",
            json={
                "customer_id": "customer-004",
                "message": "   ",
            },
        )

    assert extra_field_resp.status_code == 422
    assert blank_msg_resp.status_code == 422