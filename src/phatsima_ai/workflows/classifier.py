from dataclasses import dataclass

from phatsima_ai.models.enquiry import RiskLevel, TechnicalCommandApproval


@dataclass(frozen=True)
class ClassificationResult:
    classification: str
    intent: str
    service: str
    risk: RiskLevel
    missing_info: list[str]
    next_action: str
    human_approval_required: bool
    ticket_creation_allowed: bool
    technical_commands_approval: TechnicalCommandApproval


def classify_enquiry(message: str) -> ClassificationResult:
    text = message.lower()

    # 1. Check commercial/quotation requests first (requires human approval)
    if any(k in text for k in ("quote", "quotation", "price", "pricing", "cost", "how much")):
        return ClassificationResult(
            classification="Quotation request",
            intent="Commercial enquiry",
            service="Quotation drafting",
            risk="medium",
            missing_info=[
                "Requested service or hardware scope",
                "Quantity or user count",
                "Delivery or site location",
            ],
            next_action="Gather scope details and draft quotation for human approval",
            human_approval_required=True,
            ticket_creation_allowed=True,
            technical_commands_approval="not_applicable",
        )

    # 2. Check new project leads
    if any(k in text for k in ("website", "web app", "software", "build", "develop")):
        return ClassificationResult(
            classification="Sales lead",
            intent="Project enquiry",
            service="Website & software development",
            risk="low",
            missing_info=[
                "Business goals and target audience",
                "Required pages or features",
                "Desired launch timeline",
                "Estimated budget range",
            ],
            next_action="Qualify lead and schedule consultation",
            human_approval_required=False,
            ticket_creation_allowed=True,
            technical_commands_approval="not_applicable",
        )

    # 3. Check technical support requests
    if any(k in text for k in ("wi-fi", "wifi", "internet", "network", "router", "connection")):
        return ClassificationResult(
            classification="Support request",
            intent="IT support",
            service="Network troubleshooting",
            risk="low",
            missing_info=[
                "Windows version",
                "Exact connection status",
                "Whether other devices have internet",
                "When the problem started",
                "Customer location",
            ],
            next_action="Collect diagnostic information",
            human_approval_required=False,
            ticket_creation_allowed=True,
            technical_commands_approval="required",
        )

    # 4. General fallback
    return ClassificationResult(
        classification="General enquiry",
        intent="General triage",
        service="General IT consultation",
        risk="low",
        missing_info=[
            "Device or system affected",
            "Summary of desired outcome",
            "Urgency level",
        ],
        next_action="Request clarification from customer",
        human_approval_required=False,
        ticket_creation_allowed=True,
        technical_commands_approval="required",
    )