"""
Rule evaluator — orchestrates model building, ZEN Engine calls and audit logging.
"""
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import timezone
from typing import Any, Optional

from config.settings import settings
from database.db import get_db_session
from database import repository as repo
from engine.rule_builder import build_decision_model, save_decision_model
from engine.zen_service import get_zen_service

logger = logging.getLogger(__name__)

# ── Result dataclass ───────────────────────────────────────────────────────

ACTION_LABELS: dict[str, str] = {
    "BYPASS_HUMAN_QUEUE":  "Bypass Human Queue",
    "SEND_TO_HUMAN_QUEUE": "Send to Human Queue",
    "BLOCK_POSTING":       "Block Posting",
}

ACTION_COLORS: dict[str, str] = {
    "BYPASS_HUMAN_QUEUE":  "green",
    "SEND_TO_HUMAN_QUEUE": "orange",
    "BLOCK_POSTING":       "red",
}


@dataclass
class EvaluationResult:
    action: str
    matched_rule: Optional[str] = None
    execution_time_ms: float = 0.0
    decision_path: list[str] = field(default_factory=list)
    error: Optional[str] = None
    raw_response: Any = None

    @property
    def action_label(self) -> str:
        return ACTION_LABELS.get(self.action, self.action)

    @property
    def action_color(self) -> str:
        return ACTION_COLORS.get(self.action, "gray")

    def to_dict(self) -> dict:
        return {
            "action":          self.action,
            "matchedRule":     self.matched_rule,
            "executionTimeMs": round(self.execution_time_ms, 2),
            "decisionPath":    self.decision_path,
            "error":           self.error,
        }


# ── Public API ─────────────────────────────────────────────────────────────

def rebuild_decision_model() -> bool:
    """
    Fetch all active rules, build a fresh ZEN decision model and save it.
    Called automatically after any rule CRUD operation.
    """
    try:
        with get_db_session() as session:
            rules = repo.get_all_rules(session, active_only=True)
            model = build_decision_model(rules)
        save_decision_model(model)
        logger.info("Decision model rebuilt (%d active rules).", len(rules))
        return True
    except Exception as exc:
        logger.error("Decision model rebuild failed: %s", exc)
        return False


def evaluate_invoice(
    invoice_data: dict,
    invoice_id: Optional[str] = None,
) -> EvaluationResult:
    """
    Evaluate *invoice_data* against all active rules.

    Steps:
      1. Load active rules from the database.
      2. Build an in-memory ZEN decision model.
      3. Send the invoice to the ZEN Engine.
      4. Return an EvaluationResult and write an audit log entry.
    """
    start = time.perf_counter()

    try:
        with get_db_session() as session:
            rules = repo.get_all_rules(session, active_only=True)

        if not rules:
            elapsed = _elapsed_ms(start)
            result = EvaluationResult(
                action=settings.DEFAULT_ACTION,
                execution_time_ms=elapsed,
                decision_path=["No active rules — using default action."],
            )
            _write_audit(result, invoice_data, invoice_id)
            return result

        # Build model fresh (ensures latest rules are used)
        model = build_decision_model(rules)

        zen = get_zen_service()
        response = zen.evaluate(model, invoice_data)
        elapsed = _elapsed_ms(start)

        if response.get("error"):
            result = EvaluationResult(
                action=settings.DEFAULT_ACTION,
                execution_time_ms=elapsed,
                decision_path=[f"Engine error: {response['error']}"],
                error=response["error"],
            )
        else:
            action = response.get("action") or settings.DEFAULT_ACTION
            matched = response.get("matchedRule")
            path = (
                [f"Matched rule: «{matched}»"]
                if matched
                else [f"No rule matched → default: {settings.DEFAULT_ACTION}"]
            )
            result = EvaluationResult(
                action=action,
                matched_rule=matched,
                execution_time_ms=elapsed,
                decision_path=path,
                raw_response=response.get("raw"),
            )

        _write_audit(result, invoice_data, invoice_id)
        return result

    except Exception as exc:
        elapsed = _elapsed_ms(start)
        logger.error("evaluate_invoice failed: %s", exc)
        result = EvaluationResult(
            action=settings.DEFAULT_ACTION,
            execution_time_ms=elapsed,
            error=str(exc),
        )
        _write_audit(result, invoice_data, invoice_id)
        return result


# ── Private helpers ────────────────────────────────────────────────────────

def _elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1_000


def _write_audit(
    result: EvaluationResult,
    invoice_data: dict,
    invoice_id: Optional[str],
) -> None:
    try:
        with get_db_session() as session:
            repo.create_audit_log(
                session=session,
                decision=result.action,
                invoice_id=invoice_id,
                invoice_data=json.dumps(invoice_data, ensure_ascii=False),
                matched_rule=result.matched_rule,
                execution_time_ms=result.execution_time_ms,
                error_message=result.error,
            )
    except Exception as exc:
        logger.error("Failed to write audit log: %s", exc)
