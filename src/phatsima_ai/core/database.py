import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from phatsima_ai.workflows.classifier import ClassificationResult
from phatsima_ai.workflows.resolver import WorkflowPlan

DEFAULT_DB_PATH = Path(os.getenv("PHATSIMA_DB_PATH", "phatsima_ai.db"))


@dataclass(frozen=True)
class PersistedEnquiryOutcome:
    enquiry_id: int
    created_at: datetime
    ticket_id: int | None
    lead_id: int | None
    quotation_id: int | None


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS enquiries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                message TEXT NOT NULL,
                classification TEXT NOT NULL,
                intent TEXT NOT NULL,
                service_code TEXT NOT NULL,
                service TEXT NOT NULL,
                risk TEXT NOT NULL,
                missing_info_json TEXT NOT NULL,
                next_action TEXT NOT NULL,
                human_approval_required INTEGER NOT NULL,
                ticket_creation_allowed INTEGER NOT NULL,
                technical_commands_approval TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_enquiries_customer_id ON enquiries (customer_id);

            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enquiry_id INTEGER NOT NULL REFERENCES enquiries(id),
                customer_id TEXT NOT NULL,
                service_code TEXT NOT NULL,
                department TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enquiry_id INTEGER NOT NULL REFERENCES enquiries(id),
                customer_id TEXT NOT NULL,
                service_code TEXT NOT NULL,
                status TEXT NOT NULL,
                qualification_score INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS quotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enquiry_id INTEGER NOT NULL REFERENCES enquiries(id),
                customer_id TEXT NOT NULL,
                service_code TEXT NOT NULL,
                status TEXT NOT NULL,
                draft_amount_zar INTEGER NOT NULL,
                approved_by TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                actor TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );
            """
        )


def _log_audit(
    conn: sqlite3.Connection,
    entity_type: str,
    entity_id: int,
    action: str,
    actor: str,
    timestamp: datetime,
) -> None:
    conn.execute(
        """
        INSERT INTO audit_log (entity_type, entity_id, action, actor, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """,
        (entity_type, entity_id, action, actor, timestamp.isoformat()),
    )


def save_enquiry_and_execute_workflow(
    customer_id: str,
    channel: str,
    message: str,
    result: ClassificationResult,
    plan: WorkflowPlan,
    db_path: Path = DEFAULT_DB_PATH,
) -> PersistedEnquiryOutcome:
    now = datetime.now(UTC)
    now_iso = now.isoformat()
    merged_missing_info = list(dict.fromkeys([*result.missing_info, *plan.service.default_missing_info]))

    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO enquiries (
                customer_id, channel, message, classification, intent, service_code,
                service, risk, missing_info_json, next_action, human_approval_required,
                ticket_creation_allowed, technical_commands_approval, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                customer_id,
                channel,
                message,
                result.classification,
                result.intent,
                plan.service.code,
                plan.service.name,
                result.risk,
                json.dumps(merged_missing_info),
                result.next_action,
                int(result.human_approval_required),
                int(result.ticket_creation_allowed),
                result.technical_commands_approval,
                now_iso,
            ),
        )
        enquiry_id = int(cursor.lastrowid or 0)
        _log_audit(conn, "enquiry", enquiry_id, "created", "system", now)

        ticket_id: int | None = None
        if plan.create_ticket:
            t_cur = conn.execute(
                """
                INSERT INTO tickets (enquiry_id, customer_id, service_code, department, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (enquiry_id, customer_id, plan.service.code, plan.service.department, "open", now_iso),
            )
            ticket_id = int(t_cur.lastrowid or 0)
            _log_audit(conn, "ticket", ticket_id, "auto_created", "system", now)

        lead_id: int | None = None
        if plan.create_lead:
            l_cur = conn.execute(
                """
                INSERT INTO leads (enquiry_id, customer_id, service_code, status, qualification_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (enquiry_id, customer_id, plan.service.code, "new", 50, now_iso),
            )
            lead_id = int(l_cur.lastrowid or 0)
            _log_audit(conn, "lead", lead_id, "auto_created", "system", now)

        quotation_id: int | None = None
        if plan.create_quotation:
            q_cur = conn.execute(
                """
                INSERT INTO quotations (
                    enquiry_id, customer_id, service_code, status, draft_amount_zar,
                    approved_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    enquiry_id,
                    customer_id,
                    plan.service.code,
                    "pending_approval",
                    plan.draft_amount_zar or 0,
                    None,
                    now_iso,
                    now_iso,
                ),
            )
            quotation_id = int(q_cur.lastrowid or 0)
            _log_audit(conn, "quotation", quotation_id, "drafted_pending_approval", "system", now)

    return PersistedEnquiryOutcome(
        enquiry_id=enquiry_id,
        created_at=now,
        ticket_id=ticket_id,
        lead_id=lead_id,
        quotation_id=quotation_id,
    )


def decide_quotation(
    quotation_id: int,
    decision: str,
    reviewer: str,
    db_path: Path = DEFAULT_DB_PATH,
) -> dict[str, Any] | None:
    now = datetime.now(UTC)
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM quotations WHERE id = ?", (quotation_id,)).fetchone()
        if row is None:
            return None

        conn.execute(
            """
            UPDATE quotations
            SET status = ?, approved_by = ?, updated_at = ?
            WHERE id = ?
            """,
            (decision, reviewer, now.isoformat(), quotation_id),
        )
        _log_audit(conn, "quotation", quotation_id, f"decision_{decision}", reviewer, now)
        updated = conn.execute("SELECT * FROM quotations WHERE id = ?", (quotation_id,)).fetchone()
        return dict(updated) if updated else None


def list_records(table: str, db_path: Path = DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    if table not in {"enquiries", "tickets", "leads", "quotations", "audit_log"}:
        raise ValueError(f"Unsupported table: {table}")
    with get_connection(db_path) as conn:
        rows = conn.execute(f"SELECT * FROM {table} ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]