"""
Rule Service — business-logic layer for rule CRUD operations.

All functions return plain Python dicts so the UI layer has no SQLAlchemy
dependencies. The decision model is rebuilt after every mutation.
"""
import logging
from typing import Optional

from database.db import get_db_session
from database import repository as repo
from engine.evaluator import rebuild_decision_model

logger = logging.getLogger(__name__)


def create_rule(
    name: str,
    action: str,
    conditions: list[dict],
    description: Optional[str] = None,
    priority: int = 100,
    created_by: str = "system",
) -> dict:
    """
    Create a new rule with its conditions.

    *conditions* is a list of dicts with keys: field_name, operator, value.
    Returns ``{"success": True, "rule_id": int}`` or ``{"success": False, "error": str}``.
    """
    if not name or not name.strip():
        return {"success": False, "error": "Rule name is required."}
    if not action:
        return {"success": False, "error": "Action is required."}
    if not conditions:
        return {"success": False, "error": "At least one condition is required."}
    for i, cond in enumerate(conditions):
        if not cond.get("value", "").strip():
            return {"success": False, "error": f"Condition {i + 1}: value cannot be empty."}

    with get_db_session() as session:
        if repo.get_rule_by_name(session, name.strip()):
            return {"success": False, "error": f"A rule named '{name.strip()}' already exists."}

        rule = repo.create_rule(
            session=session,
            name=name.strip(),
            action=action,
            description=description,
            priority=priority,
            created_by=created_by,
        )
        for i, cond in enumerate(conditions):
            repo.add_condition(
                session=session,
                rule_id=rule.id,
                field_name=cond["field_name"],
                operator=cond["operator"],
                value=str(cond["value"]).strip(),
                condition_order=i,
            )
        rule_id = rule.id

    rebuild_decision_model()
    logger.info("Rule created: '%s' (id=%d)", name, rule_id)
    return {"success": True, "rule_id": rule_id}


def update_rule(
    rule_id: int,
    name: Optional[str] = None,
    action: Optional[str] = None,
    conditions: Optional[list[dict]] = None,
    description: Optional[str] = None,
    priority: Optional[int] = None,
) -> dict:
    """Update an existing rule. Pass only the fields you want to change."""
    with get_db_session() as session:
        rule = repo.get_rule_by_id(session, rule_id)
        if rule is None:
            return {"success": False, "error": f"Rule {rule_id} not found."}

        if name is not None and name.strip() != rule.name:
            if repo.get_rule_by_name(session, name.strip()):
                return {"success": False, "error": f"A rule named '{name.strip()}' already exists."}

        updates: dict = {}
        if name is not None:
            updates["name"] = name.strip()
        if action is not None:
            updates["action"] = action
        if description is not None:
            updates["description"] = description
        if priority is not None:
            updates["priority"] = priority
        if updates:
            repo.update_rule(session, rule_id, **updates)

        if conditions is not None:
            if not conditions:
                return {"success": False, "error": "At least one condition is required."}
            repo.delete_rule_conditions(session, rule_id)
            for i, cond in enumerate(conditions):
                repo.add_condition(
                    session=session,
                    rule_id=rule_id,
                    field_name=cond["field_name"],
                    operator=cond["operator"],
                    value=str(cond["value"]).strip(),
                    condition_order=i,
                )

    rebuild_decision_model()
    logger.info("Rule updated: id=%d", rule_id)
    return {"success": True}


def delete_rule(rule_id: int) -> dict:
    with get_db_session() as session:
        if not repo.delete_rule(session, rule_id):
            return {"success": False, "error": f"Rule {rule_id} not found."}

    rebuild_decision_model()
    logger.info("Rule deleted: id=%d", rule_id)
    return {"success": True}


def toggle_rule(rule_id: int) -> dict:
    with get_db_session() as session:
        rule = repo.toggle_rule_status(session, rule_id)
        if rule is None:
            return {"success": False, "error": f"Rule {rule_id} not found."}
        is_active = rule.is_active

    rebuild_decision_model()
    status = "enabled" if is_active else "disabled"
    logger.info("Rule %d %s.", rule_id, status)
    return {"success": True, "is_active": is_active}


def duplicate_rule(rule_id: int, new_name: str) -> dict:
    if not new_name.strip():
        return {"success": False, "error": "New rule name is required."}

    with get_db_session() as session:
        if repo.get_rule_by_name(session, new_name.strip()):
            return {"success": False, "error": f"A rule named '{new_name.strip()}' already exists."}
        new_rule = repo.duplicate_rule(session, rule_id, new_name.strip())
        if new_rule is None:
            return {"success": False, "error": f"Rule {rule_id} not found."}
        new_id = new_rule.id

    rebuild_decision_model()
    logger.info("Rule %d duplicated → '%s' (id=%d)", rule_id, new_name, new_id)
    return {"success": True, "rule_id": new_id}


def get_all_rules(active_only: bool = False) -> list[dict]:
    """Return all rules as plain dicts (conditions eagerly loaded)."""
    with get_db_session() as session:
        rules = repo.get_all_rules(session, active_only=active_only)
        return [_rule_to_dict(r) for r in rules]


def get_rule_by_id(rule_id: int) -> Optional[dict]:
    with get_db_session() as session:
        rule = repo.get_rule_by_id(session, rule_id)
        return _rule_to_dict(rule) if rule else None


def get_stats() -> dict:
    with get_db_session() as session:
        return repo.get_rule_stats(session)


# ── Private ────────────────────────────────────────────────────────────────

def _rule_to_dict(rule) -> dict:
    return {
        "id":          rule.id,
        "name":        rule.name,
        "description": rule.description,
        "priority":    rule.priority,
        "action":      rule.action,
        "is_active":   rule.is_active,
        "created_by":  rule.created_by,
        "created_at":  rule.created_at,
        "updated_at":  rule.updated_at,
        "conditions": [
            {
                "id":              c.id,
                "field_name":      c.field_name,
                "operator":        c.operator,
                "value":           c.value,
                "condition_order": c.condition_order,
            }
            for c in rule.conditions
        ],
    }
