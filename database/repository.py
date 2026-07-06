"""
Data-access layer (repository pattern).
All functions accept an open Session and do NOT commit — the caller owns the transaction.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session, selectinload

from database.models import AuditLog, Rule, RuleCondition

logger = logging.getLogger(__name__)


# ── Rule ───────────────────────────────────────────────────────────────────

def create_rule(
    session: Session,
    name: str,
    action: str,
    description: Optional[str] = None,
    priority: int = 100,
    created_by: str = "system",
) -> Rule:
    rule = Rule(
        name=name,
        description=description,
        priority=priority,
        action=action,
        created_by=created_by,
    )
    session.add(rule)
    session.flush()  # populate rule.id without committing
    return rule


def add_condition(
    session: Session,
    rule_id: int,
    field_name: str,
    operator: str,
    value: str,
    condition_order: int = 0,
) -> RuleCondition:
    cond = RuleCondition(
        rule_id=rule_id,
        field_name=field_name,
        operator=operator,
        value=value,
        condition_order=condition_order,
    )
    session.add(cond)
    return cond


def get_rule_by_id(session: Session, rule_id: int) -> Optional[Rule]:
    return (
        session.query(Rule)
        .options(selectinload(Rule.conditions))
        .filter(Rule.id == rule_id)
        .first()
    )


def get_rule_by_name(session: Session, name: str) -> Optional[Rule]:
    return session.query(Rule).filter(Rule.name == name).first()


def get_all_rules(session: Session, active_only: bool = False) -> list[Rule]:
    q = session.query(Rule).options(selectinload(Rule.conditions))
    if active_only:
        q = q.filter(Rule.is_active == True)  # noqa: E712
    return q.order_by(Rule.priority.asc(), Rule.created_at.asc()).all()


def update_rule(session: Session, rule_id: int, **kwargs) -> Optional[Rule]:
    rule = session.get(Rule, rule_id)
    if rule is None:
        return None
    for key, value in kwargs.items():
        if hasattr(rule, key):
            setattr(rule, key, value)
    rule.updated_at = datetime.now(timezone.utc)
    return rule


def delete_rule_conditions(session: Session, rule_id: int) -> None:
    session.query(RuleCondition).filter(RuleCondition.rule_id == rule_id).delete()


def delete_rule(session: Session, rule_id: int) -> bool:
    rule = session.get(Rule, rule_id)
    if rule is None:
        return False
    session.delete(rule)
    return True


def toggle_rule_status(session: Session, rule_id: int) -> Optional[Rule]:
    rule = session.get(Rule, rule_id)
    if rule is None:
        return None
    rule.is_active = not rule.is_active
    rule.updated_at = datetime.now(timezone.utc)
    return rule


def duplicate_rule(
    session: Session, rule_id: int, new_name: str
) -> Optional[Rule]:
    original = session.get(Rule, rule_id)
    if original is None:
        return None

    new_rule = Rule(
        name=new_name,
        description=f"Copy of: {original.description or original.name}",
        priority=original.priority,
        action=original.action,
        created_by=original.created_by,
    )
    session.add(new_rule)
    session.flush()

    for cond in original.conditions:
        session.add(
            RuleCondition(
                rule_id=new_rule.id,
                field_name=cond.field_name,
                operator=cond.operator,
                value=cond.value,
                condition_order=cond.condition_order,
            )
        )
    return new_rule


def get_rule_stats(session: Session) -> dict:
    total = session.query(func.count(Rule.id)).scalar() or 0
    active = (
        session.query(func.count(Rule.id))
        .filter(Rule.is_active == True)  # noqa: E712
        .scalar()
        or 0
    )
    return {"total": total, "active": active, "inactive": total - active}


# ── Audit Log ──────────────────────────────────────────────────────────────

def create_audit_log(
    session: Session,
    decision: str,
    invoice_id: Optional[str] = None,
    invoice_data: Optional[str] = None,
    matched_rule: Optional[str] = None,
    execution_time_ms: float = 0.0,
    error_message: Optional[str] = None,
) -> AuditLog:
    log = AuditLog(
        invoice_id=invoice_id,
        invoice_data=invoice_data,
        matched_rule=matched_rule,
        decision=decision,
        execution_time_ms=execution_time_ms,
        error_message=error_message,
    )
    session.add(log)
    return log


def get_audit_logs(
    session: Session,
    limit: int = 100,
    offset: int = 0,
    decision_filter: Optional[str] = None,
) -> list[AuditLog]:
    q = session.query(AuditLog)
    if decision_filter:
        q = q.filter(AuditLog.decision == decision_filter)
    return q.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit).all()


def get_audit_stats(session: Session) -> dict:
    total = session.query(func.count(AuditLog.id)).scalar() or 0
    by_decision = (
        session.query(AuditLog.decision, func.count(AuditLog.id))
        .group_by(AuditLog.decision)
        .all()
    )
    return {
        "total": total,
        "by_decision": {d: c for d, c in by_decision},
    }
