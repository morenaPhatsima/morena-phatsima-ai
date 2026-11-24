import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from phatsima_ai.workflows.classifier import ClassificationResult

DEFAULT_DB_PATH = Path(os.getenv("PHATSIMA_DB_PATH", "phatsima_ai.db"))


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS enquiries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                message TEXT NOT NULL,
                classification TEXT NOT NULL,
                intent TEXT NOT NULL,
                service TEXT NOT NULL,
                risk TEXT NOT NULL,
                missing_info_json TEXT NOT NULL,
                next_action TEXT NOT NULL,
                human_approval_required INTEGER NOT NULL,
                ticket_creation_allowed INTEGER NOT NULL,
                technical_commands_approval TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_enquiries_customer_id ON enquiries (customer_id)"
        )


def save_enquiry(
    customer_id: str,
    channel: str,
    message: str,
    result: ClassificationResult,
    db_path: Path = DEFAULT_DB_PATH,
) -> tuple[int, datetime]:
    created_at = datetime.now(UTC)
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO enquiries (
                customer_id, channel, message, classification, intent, service,
                risk, missing_info_json, next_action, human_approval_required,
                ticket_creation_allowed, technical_commands_approval, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                customer_id,
                channel,
                message,
                result.classification,
                result.intent,
                result.service,
                result.risk,
                json.dumps(result.missing_info),
                result.next_action,
                int(result.human_approval_required),
                int(result.ticket_creation_allowed),
                result.technical_commands_approval,
                created_at.isoformat(),
            ),
        )
        if cursor.lastrowid is None:
            raise RuntimeError("Failed to retrieve inserted enquiry ID.")
        enquiry_id = int(cursor.lastrowid)
    return enquiry_id, created_at