from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from phatsima_ai.core.database import DEFAULT_DB_PATH, init_db, save_enquiry
from phatsima_ai.models.enquiry import EnquiryClassificationResponse, EnquiryRequest
from phatsima_ai.workflows.classifier import classify_enquiry


def create_app(db_path: Path = DEFAULT_DB_PATH) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        init_db(db_path)
        yield

    app = FastAPI(
        title="Morena Phatsima IT AI",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok", "core": "PHATSIMA Core"}

    @app.post("/enquiries", response_model=EnquiryClassificationResponse, status_code=201)
    def create_enquiry(payload: EnquiryRequest) -> EnquiryClassificationResponse:
        result = classify_enquiry(payload.message)
        enquiry_id, created_at = save_enquiry(
            customer_id=payload.customer_id,
            channel=payload.channel,
            message=payload.message,
            result=result,
            db_path=db_path,
        )
        return EnquiryClassificationResponse(
            enquiry_id=enquiry_id,
            customer_id=payload.customer_id,
            classification=result.classification,
            intent=result.intent,
            service=result.service,
            risk=result.risk,
            missing_info=result.missing_info,
            next_action=result.next_action,
            human_approval_required=result.human_approval_required,
            ticket_creation_allowed=result.ticket_creation_allowed,
            technical_commands_approval=result.technical_commands_approval,
            created_at=created_at,
        )

    return app


app = create_app()