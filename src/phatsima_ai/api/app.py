from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

from phatsima_ai.core.catalogue import MORENA_PHATSIMA_PROFILE, SERVICE_CATALOGUE
from phatsima_ai.core.database import (
    DEFAULT_DB_PATH,
    decide_quotation,
    init_db,
    list_records,
    save_enquiry_and_execute_workflow,
)
from phatsima_ai.models.enquiry import (
    EnquiryClassificationResponse,
    EnquiryRequest,
    LeadResponse,
    QuotationDecisionRequest,
    QuotationResponse,
    TicketResponse,
)
from phatsima_ai.workflows.classifier import classify_enquiry
from phatsima_ai.workflows.resolver import build_workflow_plan


def create_app(db_path: Path = DEFAULT_DB_PATH) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        init_db(db_path)
        yield

    app = FastAPI(
        title="Morena Phatsima IT AI",
        version="0.2.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok", "core": "PHATSIMA Core", "version": "0.2.0"}

    @app.get("/services")
    def get_services() -> dict[str, Any]:
        return {
            "profile": asdict(MORENA_PHATSIMA_PROFILE),
            "services": [asdict(svc) for svc in SERVICE_CATALOGUE.values()],
        }

    @app.post("/enquiries", response_model=EnquiryClassificationResponse, status_code=201)
    def create_enquiry(payload: EnquiryRequest) -> EnquiryClassificationResponse:
        result = classify_enquiry(payload.message)
        plan = build_workflow_plan(result, payload.message)
        outcome = save_enquiry_and_execute_workflow(
            customer_id=payload.customer_id,
            channel=payload.channel,
            message=payload.message,
            result=result,
            plan=plan,
            db_path=db_path,
        )
        merged_missing = list(dict.fromkeys([*result.missing_info, *plan.service.default_missing_info]))
        return EnquiryClassificationResponse(
            enquiry_id=outcome.enquiry_id,
            customer_id=payload.customer_id,
            classification=result.classification,
            intent=result.intent,
            service_code=plan.service.code,
            service=plan.service.name,
            department=plan.service.department,
            risk=result.risk,
            missing_info=merged_missing,
            next_action=result.next_action,
            human_approval_required=result.human_approval_required,
            ticket_creation_allowed=result.ticket_creation_allowed,
            technical_commands_approval=result.technical_commands_approval,
            ticket_id=outcome.ticket_id,
            lead_id=outcome.lead_id,
            quotation_id=outcome.quotation_id,
            created_at=outcome.created_at,
        )

    @app.get("/tickets", response_model=list[TicketResponse])
    def get_tickets() -> list[dict[str, Any]]:
        return list_records("tickets", db_path=db_path)

    @app.get("/leads", response_model=list[LeadResponse])
    def get_leads() -> list[dict[str, Any]]:
        return list_records("leads", db_path=db_path)

    @app.get("/quotations", response_model=list[QuotationResponse])
    def get_quotations() -> list[dict[str, Any]]:
        return list_records("quotations", db_path=db_path)

    @app.post("/quotations/{quotation_id}/decide", response_model=QuotationResponse)
    def approve_or_reject_quotation(
        quotation_id: int,
        payload: QuotationDecisionRequest,
    ) -> dict[str, Any]:
        updated = decide_quotation(
            quotation_id=quotation_id,
            decision=payload.decision,
            reviewer=payload.reviewer,
            db_path=db_path,
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Quotation not found")
        return updated

    return app


app = create_app()