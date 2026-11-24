# Technical Due-Diligence Report

**Reviewed:** 2026-11-24  
**Scope:** Repository source, project documentation, and local test/lint results. This is a codebase review, not a penetration test or deployment assessment.

## Executive summary

This repository is an early-stage FastAPI prototype for classifying incoming enquiries and recording them in SQLite. The core intake path works, request models enforce useful validation, and the current tests and Ruff checks pass.

Phase 1 is **substantially implemented**, but its persistence and validation behavior are not comprehensively tested. The project is **not production-ready** and is **not yet ready for broad Phase 2 feature development**: workflow records, status transitions, identity/authorization, approval enforcement, and operational database practices do not exist. Implement the minimum workflow and security foundations before adding dashboards or external integrations.

## Current architecture

- `src/phatsima_ai/api/app.py` creates the FastAPI application, initializes the database at startup, exposes the API routes, and connects enquiry requests to the classifier and persistence layer.
- `src/phatsima_ai/models/enquiry.py` defines Pydantic request/response models and validation rules.
- `src/phatsima_ai/workflows/classifier.py` uses deterministic keyword matching and ordered rules to classify enquiries.
- `src/phatsima_ai/core/database.py` creates and writes to a local SQLite database using parameterized SQL.
- The architecture and security documents describe broader provider integration, identity, permissions, orchestration, and audit controls; these are not implemented in the source yet.
- `src/phatsima_ai/core/catalogue.py` is currently an empty, untracked file. There is no implemented service catalogue.

## Implemented functionality

- `GET /health` returns a basic health response.
- `POST /enquiries` accepts an enquiry, classifies it, persists the classification, and returns HTTP 201 with the result.
- Classification rules cover quotation requests, project leads, network support, and a general fallback.
- Request validation rejects extra fields, blank values, invalid channel values, and values beyond configured length limits.
- SQLite persistence stores the raw message and classification outcome in an `enquiries` table.
- The test suite currently exercises a Wi-Fi support enquiry, a quotation approval flag, and rejection of extra fields/blank messages.

## API endpoints

| Method | Path | Behavior |
|---|---|---|
| `GET` | `/health` | Basic liveness-style response; does not check database readiness. |
| `POST` | `/enquiries` | Classify and persist an enquiry; returns `201`. |

No endpoints currently retrieve or update enquiries, manage tickets/leads/quotations, or expose a service catalogue.

## Database schema implemented

There is one table: `enquiries`, created by `init_db` in `src/phatsima_ai/core/database.py`.

It stores an auto-incrementing ID, caller-supplied customer ID, channel, raw message, classification, intent, service, risk, JSON-encoded missing information, next action, approval/ticket flags, technical-command approval state, and creation timestamp. An index exists on `customer_id`.

There are no customer, service, ticket, lead, quotation, approval, user, or audit-event tables. Schema creation uses `CREATE TABLE IF NOT EXISTS`; no migration/versioning mechanism is present.

## Phase 1 evidence and status

| Requirement | Status | Evidence / qualification |
|---|---|---|
| `POST /enquiries` | Implemented | Route is in `src/phatsima_ai/api/app.py`; an integration test expects HTTP 201. |
| Enquiry classification | Implemented, basic | `src/phatsima_ai/workflows/classifier.py` has four deterministic rule branches. Coverage is narrow and rules are not confidence-scored. |
| SQLite persistence | Implemented, lightly verified | Startup creates the schema and the endpoint inserts a row. Tests use a temporary SQLite database but do not assert row contents or persistence across restarts. |
| Unit tests | Partially met | Three pytest tests pass, but all are API-level tests; there are no focused classifier or database tests. |
| API validation | Implemented, partially tested | Pydantic limits and `extra="forbid"` are configured. The tests cover extra fields and blank messages, not the full invalid-input matrix. |

**Local validation:** `pytest -q` — **3 passed**, with one Starlette/httpx deprecation warning. `ruff check src tests` — **passed**. Coverage percentage is not configured or measured.

## Gaps, design issues, and risks

### High priority before production exposure

- **No authentication or authorization.** `customer_id` is supplied by the request and is not tied to an authenticated identity. The security document's customer-isolation claim is not demonstrated by an access-control mechanism.
- **Approval flags are data, not controls.** `human_approval_required`, `technical_commands_approval`, and `ticket_creation_allowed` are returned and persisted, but no workflow enforces them. In particular, setting `ticket_creation_allowed` does not create a ticket.
- **Sensitive message handling is undefined.** Raw customer messages are stored; retention/deletion, access controls, encryption, backup, and restore policies are not implemented or specified.
- **No production database operations.** There is no schema migration process, database readiness check, or documented backup/recovery procedure. The configured database path is local SQLite.

### Product and maintainability gaps

- Keyword substring matching can misclassify messages, is sensitive to phrasing, and has no confidence/uncertain-review path. Rule order also determines which category wins when a message matches several categories.
- The service catalogue, ticketing, lead qualification, quotation lifecycle, and status management are not implemented.
- There are no retrieval/update APIs, structured logging/metrics, rate limiting, idempotency handling, or documented operational deployment settings.
- The architecture/security docs describe goals rather than current capabilities; keep that distinction clear as the project grows.
- `.env.example` contains `DATABASE_URL` and `AI_PROVIDER`, while the current database implementation reads `PHATSIMA_DB_PATH` and does not use an AI provider. Configuration should be made consistent before relying on it operationally.

## Phase 2 roadmap assessment

The proposed direction is sensible, but implement it in dependency order rather than adding all domain objects and integrations at once:

1. Define customer identity/tenant boundaries, roles, and the exact human-approval rules. Treat a caller-provided customer ID as data, not authorization.
2. Introduce a versioned schema and a small workflow/service layer with explicit states, ownership, timestamps, and auditable state transitions.
3. Implement the first useful workflow end-to-end (likely support ticket creation from an enquiry), including persistence, retrieval, transition validation, and focused tests.
4. Add lead qualification and quotation drafting/approval as separate capabilities when their required data and transitions are defined. Keep quote sending and infrastructure changes behind enforced approval gates.
5. Add a dashboard only after the workflow API and permissions are stable. Add email/Teams adapters later, with retries and idempotency so integrations cannot silently duplicate work.

Avoid creating tickets, leads, and quotations as disconnected tables without defining their relationship to the originating enquiry, lifecycle, owner, and audit history. A thin workflow orchestration boundary is a better next foundation than expanding the classifier.

## Recommended next development phase

**Phase 1.5 — workflow and operational foundations:** define identity/authorization and approval semantics; add schema migrations and a persisted workflow lifecycle; test database persistence and state transitions; then deliver one end-to-end ticket workflow. Defer dashboards and channel integrations until those contracts are dependable.

## Readiness conclusion

- **Prototype / local development:** Ready.
- **Phase 1:** Core path exists; validation and persistence tests should be strengthened before calling it complete.
- **Phase 2:** Begin with workflow foundations and a single end-to-end ticket path, not the full catalogue/leads/quotations bundle.
- **Production MVP:** Not ready. Authentication/authorization, enforced approval controls, database migration/backup practices, operational visibility, and privacy/retention decisions remain prerequisites.
