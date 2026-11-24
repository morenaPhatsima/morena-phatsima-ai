from dataclasses import dataclass

from phatsima_ai.core.catalogue import ServiceDefinition, get_service
from phatsima_ai.workflows.classifier import ClassificationResult


@dataclass(frozen=True)
class WorkflowPlan:
    service: ServiceDefinition
    create_ticket: bool
    create_lead: bool
    create_quotation: bool
    draft_amount_zar: int | None


def resolve_service(classification: ClassificationResult, message: str) -> ServiceDefinition:
    text = message.lower()

    if any(k in text for k in ("bana pele", "ecares", "ecd", "creche", "crèche", "uplift", "saturday clinic")):
        return get_service("community_uplift")

    if any(k in text for k in ("security", "antivirus", "mfa", "two-step", "hack", "phishing", "password")):
        return get_service("security_setup")

    if any(k in text for k in ("backup", "recover", "recovery", "deleted file", "onedrive", "google drive")):
        return get_service("backup_recovery")

    if any(k in text for k in ("training", "workshop", "learn", "lesson", "class", "coach")):
        return get_service("training_skills")

    if any(k in text for k in ("advice", "recommend", "which laptop", "which router", "setup plan")):
        return get_service("technology_advice")

    if classification.classification == "Sales lead" or any(
        k in text for k in ("website", "web app", "software", "build", "develop")
    ):
        return get_service("website_development")

    return get_service("it_wifi_support")


def build_workflow_plan(classification: ClassificationResult, message: str) -> WorkflowPlan:
    service = resolve_service(classification, message)
    is_quote = classification.classification == "Quotation request"

    return WorkflowPlan(
        service=service,
        create_ticket=service.auto_create_ticket and not is_quote,
        create_lead=service.auto_create_lead and not is_quote,
        create_quotation=is_quote,
        draft_amount_zar=service.base_rate_zar if is_quote else None,
    )