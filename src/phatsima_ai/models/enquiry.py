from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Channel = Literal["api", "whatsapp", "web", "cli"]
RiskLevel = Literal["low", "medium", "high"]
TechnicalCommandApproval = Literal["required", "not_applicable"]


class EnquiryRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    customer_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique customer identifier",
        examples=["customer-001"],
    )
    channel: Channel = "api"
    message: str = Field(
        ...,
        min_length=1,
        max_length=10_000,
        description="Raw unstructured customer message",
        examples=[
            "My laptop connects to Wi-Fi, but there is no internet."
        ],
    )

    @field_validator("customer_id", "message")
    @classmethod
    def reject_blank_values(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value cannot be blank")
        return value


class EnquiryClassificationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enquiry_id: int = Field(..., ge=1)
    customer_id: str
    classification: str
    intent: str
    service: str
    risk: RiskLevel
    missing_info: list[str] = Field(default_factory=list)
    next_action: str
    human_approval_required: bool
    ticket_creation_allowed: bool
    technical_commands_approval: TechnicalCommandApproval
    created_at: datetime