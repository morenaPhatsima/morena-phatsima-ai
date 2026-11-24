from dataclasses import dataclass
from typing import Literal

Department = Literal["Support", "Security", "Engineering", "Training", "Advisory", "CommunityUplift"]
AssistanceMode = Literal["on_site_potchefstroom", "remote", "either", "saturday_clinic"]
BillingUnit = Literal["per_callout", "per_session", "per_project", "per_hour", "free_community"]


@dataclass(frozen=True)
class BusinessProfile:
    name: str
    base_location: str
    service_area: str
    whatsapp_phone: str
    email: str
    hours_mon_fri: str
    hours_sat: str
    hours_sun: str
    pricing_policy: str
    uplift_popia_policy: str


MORENA_PHATSIMA_PROFILE = BusinessProfile(
    name="Morena Phatsima IT",
    base_location="Ikageng, Potchefstroom, 2525",
    service_area="Potchefstroom & surrounding areas (on-site); anywhere (remote & web)",
    whatsapp_phone="066 126 2587",
    email="phatsima16@gmail.com",
    hours_mon_fri="09:00-16:30",
    hours_sat="08:00-13:00",
    hours_sun="Closed",
    pricing_policy="Every job is scoped, estimated, and priced upfront before any work or callout begins.",
    uplift_popia_policy=(
        "Community Uplift sessions are 100% free. Never collect or store child/learner personal data "
        "on the server; ECD readiness checklists and eCares counts remain local-only on the user's device."
    ),
)


@dataclass(frozen=True)
class ServiceDefinition:
    code: str
    catalogue_number: str
    name: str
    department: Department
    assistance_mode: AssistanceMode
    base_rate_zar: int
    billing_unit: BillingUnit
    auto_create_ticket: bool
    auto_create_lead: bool
    requires_human_quote_approval: bool
    default_missing_info: tuple[str, ...]


SERVICE_CATALOGUE: dict[str, ServiceDefinition] = {
    "it_wifi_support": ServiceDefinition(
        code="it_wifi_support",
        catalogue_number="01",
        name="IT & Wi-Fi Support Callout",
        department="Support",
        assistance_mode="either",
        base_rate_zar=450,
        billing_unit="per_callout",
        auto_create_ticket=True,
        auto_create_lead=False,
        requires_human_quote_approval=True,
        default_missing_info=(
            "Area / Suburb (for Potchefstroom on-site vs. remote check)",
            "Preferred assistance mode (On-Site Potchefstroom or Remote)",
            "Device / Windows version and exact issue symptoms",
            "Whether other devices are affected and when the issue started",
        ),
    ),
    "security_setup": ServiceDefinition(
        code="security_setup",
        catalogue_number="02",
        name="Device & Account Security Setup",
        department="Security",
        assistance_mode="either",
        base_rate_zar=500,
        billing_unit="per_session",
        auto_create_ticket=True,
        auto_create_lead=False,
        requires_human_quote_approval=True,
        default_missing_info=(
            "Area / Suburb and preferred assistance mode (On-Site or Remote)",
            "Devices or accounts to harden (Windows PC, router, email, banking)",
            "Current antivirus or MFA setup status",
        ),
    ),
    "backup_recovery": ServiceDefinition(
        code="backup_recovery",
        catalogue_number="03",
        name="Data Backup & Recovery Assistance",
        department="Support",
        assistance_mode="either",
        base_rate_zar=550,
        billing_unit="per_session",
        auto_create_ticket=True,
        auto_create_lead=False,
        requires_human_quote_approval=True,
        default_missing_info=(
            "Area / Suburb and preferred assistance mode (On-Site or Remote)",
            "Storage type (Windows PC, external drive, OneDrive/Google Drive)",
            "Whether files were recently deleted or physical drive damage is suspected",
        ),
    ),
    "website_development": ServiceDefinition(
        code="website_development",
        catalogue_number="04",
        name="Website Development",
        department="Engineering",
        assistance_mode="remote",
        base_rate_zar=3500,
        billing_unit="per_project",
        auto_create_ticket=False,
        auto_create_lead=True,
        requires_human_quote_approval=True,
        default_missing_info=(
            "Business name, industry, and target customers",
            "Required pages and WhatsApp/email enquiry flow needs",
            "Existing domain/logo status and target launch date",
        ),
    ),
    "training_skills": ServiceDefinition(
        code="training_skills",
        catalogue_number="05",
        name="Training & Skills Development",
        department="Training",
        assistance_mode="either",
        base_rate_zar=350,
        billing_unit="per_hour",
        auto_create_ticket=False,
        auto_create_lead=True,
        requires_human_quote_approval=True,
        default_missing_info=(
            "Area / Suburb and preferred mode (1-on-1 or small group, On-Site or Remote)",
            "Topics needed (computer basics, Office/cloud tools, Wi-Fi/smartphone, scam awareness)",
            "Current comfort level and preferred day/time",
        ),
    ),
    "technology_advice": ServiceDefinition(
        code="technology_advice",
        catalogue_number="06",
        name="Technology Advice & Setup Planning",
        department="Advisory",
        assistance_mode="either",
        base_rate_zar=400,
        billing_unit="per_session",
        auto_create_ticket=False,
        auto_create_lead=True,
        requires_human_quote_approval=True,
        default_missing_info=(
            "Home or small-business environment and Area / Suburb",
            "Equipment or workflow being planned (laptops, routers, printers, office setup)",
            "Estimated budget range and timeline",
        ),
    ),
    "community_uplift": ServiceDefinition(
        code="community_uplift",
        catalogue_number="07",
        name="Community Uplift & Saturday Literacy Clinics",
        department="CommunityUplift",
        assistance_mode="saturday_clinic",
        base_rate_zar=0,
        billing_unit="free_community",
        auto_create_ticket=False,
        auto_create_lead=False,
        requires_human_quote_approval=False,
        default_missing_info=(
            "Preferred Saturday session track (08:30 ECD eCares/Bana Pele, 10:15 Youth CV/Cloud, or 11:45 Family Security)",
            "Preferred Saturday date (08:00-13:00 clinic window)",
            "Reminder: Do NOT share any learner names, IDs, or centre child records (POPIA local-only policy)",
        ),
    ),
}


def get_service(code: str) -> ServiceDefinition:
    if code not in SERVICE_CATALOGUE:
        raise KeyError(f"Unknown service code: {code}")
    return SERVICE_CATALOGUE[code]