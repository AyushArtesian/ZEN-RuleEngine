"""
Audit Service — query and export evaluation history.
"""
import csv
import io
import logging
from typing import Optional

from database.db import get_db_session
from database import repository as repo

logger = logging.getLogger(__name__)


def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    decision_filter: Optional[str] = None,
) -> list[dict]:
    with get_db_session() as session:
        logs = repo.get_audit_logs(
            session, limit=limit, offset=offset, decision_filter=decision_filter
        )
        return [
            {
                "id":                log.id,
                "invoice_id":        log.invoice_id,
                "invoice_data":      log.invoice_data,
                "matched_rule":      log.matched_rule,
                "decision":          log.decision,
                "execution_time_ms": log.execution_time_ms,
                "error_message":     log.error_message,
                "timestamp":         log.timestamp,
            }
            for log in logs
        ]


def get_audit_stats() -> dict:
    with get_db_session() as session:
        return repo.get_audit_stats(session)


def export_to_csv(logs: list[dict]) -> str:
    """Serialise a list of audit-log dicts to a CSV string."""
    output = io.StringIO()
    fieldnames = [
        "id", "invoice_id", "matched_rule", "decision",
        "execution_time_ms", "timestamp", "error_message",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for log in logs:
        row = {k: log.get(k, "") for k in fieldnames}
        if row.get("timestamp"):
            row["timestamp"] = str(row["timestamp"])
        writer.writerow(row)
    return output.getvalue()
