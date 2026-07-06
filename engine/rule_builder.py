"""
Rule Builder — converts database Rule objects into a ZEN Engine decision model.

The output is a standard ZEN Engine decision graph JSON (decision table node
with hitPolicy="first"). The model is rebuilt automatically whenever a rule is
created, updated, or deleted.
"""
import json
import logging
import uuid
from pathlib import Path
from typing import Optional

from config.settings import DECISION_MODELS_DIR

logger = logging.getLogger(__name__)

DECISION_MODEL_PATH: Path = DECISION_MODELS_DIR / "invoice_rules.json"

# ── Field catalogue ────────────────────────────────────────────────────────
# Maps invoice JSON field names → display label and FEEL type
SUPPORTED_FIELDS: dict[str, dict] = {
    "vendor":           {"label": "Vendor",            "type": "string"},
    "amount":           {"label": "Invoice Amount",    "type": "number"},
    "store":            {"label": "Store",             "type": "string"},
    "validationPassed": {"label": "Validation Passed", "type": "boolean"},
    "missingFields":    {"label": "Missing Fields",    "type": "array"},
    "currency":         {"label": "Currency",          "type": "string"},
    "country":          {"label": "Country",           "type": "string"},
}

# Operators available per field type
OPERATORS_BY_TYPE: dict[str, list[str]] = {
    "string":  ["=", "!=", "Contains", "Starts With", "Ends With", "IN", "NOT IN"],
    "number":  ["=", "!=", ">", "<", ">=", "<="],
    "boolean": ["="],
    "array":   ["Contains", "Not Contains"],
}

RULE_ACTIONS: dict[str, str] = {
    "BYPASS_HUMAN_QUEUE":  "Bypass Human Queue",
    "SEND_TO_HUMAN_QUEUE": "Send to Human Queue",
    "BLOCK_POSTING":       "Block Posting",
}


# ── FEEL expression builder ────────────────────────────────────────────────

def build_feel_expression(field_type: str, operator: str, value: str) -> str:
    """
    Convert a (field_type, operator, value) triple into a ZEN Engine FEEL
    unary-test expression suitable for a decision-table input cell.

    An empty string means "wildcard — match any value".
    """
    value = value.strip()
    if not value:
        return ""

    if field_type == "boolean":
        return "true" if value.lower() in ("true", "yes", "1") else "false"

    if field_type == "number":
        try:
            num = float(value)
        except ValueError:
            logger.warning("Invalid numeric value for FEEL: %s", value)
            return value
        mapping = {
            "=":  str(num),
            "!=": f"!= {num}",
            ">":  f"> {num}",
            "<":  f"< {num}",
            ">=": f">= {num}",
            "<=": f"<= {num}",
        }
        return mapping.get(operator, str(num))

    if field_type == "string":
        if operator == "=":
            return f'"{value}"'
        if operator == "!=":
            return f'not("{value}")'
        if operator == "IN":
            items = ", ".join(f'"{v.strip()}"' for v in value.split(","))
            return f"[{items}]"
        if operator == "NOT IN":
            items = ", ".join(f'"{v.strip()}"' for v in value.split(","))
            return f"not([{items}])"
        if operator == "Contains":
            return f'contains(?, "{value}")'
        if operator == "Starts With":
            return f'startsWith(?, "{value}")'
        if operator == "Ends With":
            return f'endsWith(?, "{value}")'
        return f'"{value}"'

    if field_type == "array":
        # Check membership in an array field (e.g. missingFields)
        if operator in ("Contains",):
            return f'contains(?, "{value}")'
        if operator in ("Not Contains",):
            return f'not(contains(?, "{value}"))'
        return f'"{value}"'

    return f'"{value}"'


# ── Decision model builder ─────────────────────────────────────────────────

def _uid(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:8]}"


def build_decision_model(rules: list) -> dict:
    """
    Build a ZEN Engine decision graph from a list of Rule ORM objects.

    Rules are sorted by priority (ascending). Each rule maps to one row
    in a decision table with hitPolicy="first".
    """
    # Collect all field names actually used across all rules
    used_fields: set[str] = set()
    for rule in rules:
        for cond in rule.conditions:
            used_fields.add(cond.field_name)

    if not used_fields:
        # Provide a minimal schema so the model is still syntactically valid
        used_fields = {"vendor"}

    # Build ordered input columns (sorted for determinism)
    col_id_map: dict[str, str] = {}
    input_cols: list[dict] = []
    for field_name in sorted(used_fields):
        info = SUPPORTED_FIELDS.get(field_name, {"label": field_name, "type": "string"})
        col_id = _uid("inp_")
        col_id_map[field_name] = col_id
        input_cols.append(
            {"id": col_id, "name": info["label"], "field": field_name, "defaultValue": ""}
        )

    # Fixed output columns
    action_col_id = _uid("out_")
    rule_name_col_id = _uid("out_")
    output_cols: list[dict] = [
        {"id": action_col_id,    "name": "Action",       "field": "action",      "defaultValue": '""'},
        {"id": rule_name_col_id, "name": "Matched Rule", "field": "matchedRule", "defaultValue": '""'},
    ]

    # Build one row per active rule, sorted by priority
    table_rules: list[dict] = []
    for rule in sorted(rules, key=lambda r: (r.priority, r.id)):
        row: dict[str, str] = {"_id": f"rule_{rule.id}"}

        for field_name, col_id in col_id_map.items():
            matching = next(
                (c for c in rule.conditions if c.field_name == field_name), None
            )
            if matching:
                ftype = SUPPORTED_FIELDS.get(field_name, {}).get("type", "string")
                row[col_id] = build_feel_expression(ftype, matching.operator, matching.value)
            else:
                row[col_id] = ""  # wildcard

        row[action_col_id]    = f'"{rule.action}"'
        row[rule_name_col_id] = f'"{rule.name}"'
        table_rules.append(row)

    # Node IDs (stable strings)
    input_node_id = "node_input"
    dt_node_id    = "node_decision_table"
    output_node_id = "node_output"

    model = {
        "contentType": "application/vnd.gorules.decision",
        "nodes": [
            {
                "id": input_node_id,
                "name": "Invoice Input",
                "type": "inputNode",
                "position": {"x": 100, "y": 200},
            },
            {
                "id": dt_node_id,
                "name": "Invoice Rules",
                "type": "decisionTableNode",
                "position": {"x": 450, "y": 200},
                "content": {
                    "hitPolicy": "first",
                    "inputs":  input_cols,
                    "outputs": output_cols,
                    "rules":   table_rules,
                },
            },
            {
                "id": output_node_id,
                "name": "Decision Output",
                "type": "outputNode",
                "position": {"x": 800, "y": 200},
            },
        ],
        "edges": [
            {
                "id": "edge_1",
                "sourceId": input_node_id,
                "targetId": dt_node_id,
                "sourceHandle": None,
                "targetHandle": None,
            },
            {
                "id": "edge_2",
                "sourceId": dt_node_id,
                "targetId": output_node_id,
                "sourceHandle": None,
                "targetHandle": None,
            },
        ],
    }
    return model


def save_decision_model(model: dict) -> Path:
    """Persist the decision model as JSON."""
    DECISION_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DECISION_MODEL_PATH, "w", encoding="utf-8") as fh:
        json.dump(model, fh, indent=2)
    logger.info("Decision model saved → %s", DECISION_MODEL_PATH)
    return DECISION_MODEL_PATH


def load_decision_model() -> Optional[dict]:
    """Load the persisted decision model, or None if it does not exist."""
    if not DECISION_MODEL_PATH.exists():
        return None
    with open(DECISION_MODEL_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)
