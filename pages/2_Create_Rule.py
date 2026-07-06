"""
Create Rule page — form for building a new invoice routing rule.
"""
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from database.db import init_db
from engine.rule_builder import OPERATORS_BY_TYPE, RULE_ACTIONS, SUPPORTED_FIELDS
from services import rule_service

st.set_page_config(
    page_title="Create Rule | Invoice Rule Engine",
    page_icon="➕",
    layout="wide",
)

if "db_initialized" not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

# ── Session-state helpers ──────────────────────────────────────────────────

def _init_conditions() -> None:
    if "cr_conditions" not in st.session_state:
        st.session_state.cr_conditions = [
            {"id": _new_id(), "field_name": "vendor", "operator": "=", "value": ""}
        ]


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


def _add_condition() -> None:
    st.session_state.cr_conditions.append(
        {"id": _new_id(), "field_name": "vendor", "operator": "=", "value": ""}
    )


def _remove_condition(cond_id: str) -> None:
    st.session_state.cr_conditions = [
        c for c in st.session_state.cr_conditions if c["id"] != cond_id
    ]


def _reset_form() -> None:
    for key in ["cr_name", "cr_description", "cr_priority", "cr_action", "cr_conditions"]:
        st.session_state.pop(key, None)
    _init_conditions()


_init_conditions()

FIELD_LABELS = {k: v["label"] for k, v in SUPPORTED_FIELDS.items()}
FIELD_KEYS   = list(SUPPORTED_FIELDS.keys())
ACTION_KEYS  = list(RULE_ACTIONS.keys())

# ── Page ───────────────────────────────────────────────────────────────────
st.title("➕ Create Rule")
st.caption("Define the conditions and routing action for a new business rule.")
st.divider()

# ── Rule metadata ──────────────────────────────────────────────────────────
st.markdown("#### Rule Details")

meta1, meta2, meta3 = st.columns([3, 1, 2])

with meta1:
    rule_name = st.text_input(
        "Rule Name *",
        key="cr_name",
        placeholder="e.g. Vendor A Bypass",
        help="Unique name for this rule.",
    )

with meta2:
    priority = st.number_input(
        "Priority *",
        key="cr_priority",
        min_value=1,
        max_value=9999,
        value=100,
        step=10,
        help="Lower number = evaluated first.",
    )

with meta3:
    action = st.selectbox(
        "Action *",
        options=ACTION_KEYS,
        format_func=lambda k: RULE_ACTIONS[k],
        key="cr_action",
        help="What happens when this rule matches.",
    )

description = st.text_area(
    "Description",
    key="cr_description",
    placeholder="Explain what this rule does (optional)...",
    height=80,
)

st.divider()

# ── Conditions builder ─────────────────────────────────────────────────────
st.markdown("#### Conditions")
st.caption(
    "All conditions within a rule use **AND** logic — every condition must match."
)

for i, cond in enumerate(list(st.session_state.cr_conditions)):
    cid = cond["id"]

    if i > 0:
        st.markdown(
            "<div style='text-align:center;color:#6b7280;font-weight:600;"
            "margin:0.25rem 0;'>AND</div>",
            unsafe_allow_html=True,
        )

    col_field, col_op, col_val, col_del = st.columns([3, 2, 3, 1])

    with col_field:
        field_index = FIELD_KEYS.index(cond.get("field_name", "vendor"))
        selected_field = st.selectbox(
            "Field",
            options=FIELD_KEYS,
            format_func=lambda k: FIELD_LABELS[k],
            index=field_index,
            key=f"cr_field_{cid}",
            label_visibility="collapsed",
        )
        st.session_state.cr_conditions[i]["field_name"] = selected_field

    field_type = SUPPORTED_FIELDS[selected_field]["type"]
    available_ops = OPERATORS_BY_TYPE.get(field_type, ["="])

    with col_op:
        current_op = cond.get("operator", "=")
        op_index = available_ops.index(current_op) if current_op in available_ops else 0
        selected_op = st.selectbox(
            "Operator",
            options=available_ops,
            index=op_index,
            key=f"cr_op_{cid}",
            label_visibility="collapsed",
        )
        st.session_state.cr_conditions[i]["operator"] = selected_op

    with col_val:
        if field_type == "boolean":
            bool_val = st.selectbox(
                "Value",
                options=["True", "False"],
                index=0 if cond.get("value", "True").lower() != "false" else 1,
                key=f"cr_val_{cid}",
                label_visibility="collapsed",
            )
            st.session_state.cr_conditions[i]["value"] = bool_val
        else:
            hint = "e.g. Vendor A, Vendor B  (comma-separated for IN)" \
                   if selected_op in ("IN", "NOT IN") else "Enter value..."
            text_val = st.text_input(
                "Value",
                value=cond.get("value", ""),
                key=f"cr_val_{cid}",
                placeholder=hint,
                label_visibility="collapsed",
            )
            st.session_state.cr_conditions[i]["value"] = text_val

    with col_del:
        if len(st.session_state.cr_conditions) > 1:
            if st.button("🗑️", key=f"cr_del_{cid}", help="Remove this condition"):
                _remove_condition(cid)
                st.rerun()

st.markdown("")
if st.button("➕ Add Condition", type="secondary"):
    _add_condition()
    st.rerun()

st.divider()

# ── Save ───────────────────────────────────────────────────────────────────
save_col, _ = st.columns([2, 5])
with save_col:
    if st.button("💾 Save Rule", type="primary", use_container_width=True):
        # Collect current condition values
        conditions_payload = [
            {
                "field_name": c["field_name"],
                "operator":   c["operator"],
                "value":      c["value"],
            }
            for c in st.session_state.cr_conditions
        ]

        result = rule_service.create_rule(
            name=rule_name,
            action=st.session_state.get("cr_action", ACTION_KEYS[0]),
            conditions=conditions_payload,
            description=description or None,
            priority=int(st.session_state.get("cr_priority", 100)),
        )

        if result["success"]:
            st.success(f"✅ Rule **{rule_name}** saved (ID: {result['rule_id']}).")
            _reset_form()
            st.rerun()
        else:
            st.error(f"❌ {result['error']}")
