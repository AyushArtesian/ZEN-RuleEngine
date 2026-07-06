"""
Manage Rules page — view, edit, toggle, duplicate and delete rules.
"""
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from database.db import init_db
from engine.rule_builder import OPERATORS_BY_TYPE, RULE_ACTIONS, SUPPORTED_FIELDS
from services import rule_service

st.set_page_config(
    page_title="Manage Rules | Invoice Rule Engine",
    page_icon="⚙️",
    layout="wide",
)

if "db_initialized" not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

# ── Constants ──────────────────────────────────────────────────────────────
ACTION_LABELS = {k: v for k, v in RULE_ACTIONS.items()}
FIELD_KEYS    = list(SUPPORTED_FIELDS.keys())
FIELD_LABELS  = {k: v["label"] for k, v in SUPPORTED_FIELDS.items()}
ACTION_KEYS   = list(RULE_ACTIONS.keys())


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


# ── Helpers ────────────────────────────────────────────────────────────────

def _cond_summary(conditions: list[dict]) -> str:
    parts = [
        f"{FIELD_LABELS.get(c['field_name'], c['field_name'])} {c['operator']} {c['value']}"
        for c in conditions
    ]
    return " AND ".join(parts)


# ── Page ───────────────────────────────────────────────────────────────────
st.title("⚙️ Manage Rules")
st.caption("View, edit and manage all invoice routing rules.")
st.divider()

rules = rule_service.get_all_rules()

if not rules:
    st.info("No rules defined yet. Go to **Create Rule** to add your first rule.")
    if st.button("➕ Create Rule", type="primary"):
        st.switch_page("pages/2_Create_Rule.py")
    st.stop()

# ── Summary table ──────────────────────────────────────────────────────────
st.markdown(f"**{len(rules)} rule(s) found**")

summary_rows = []
for r in rules:
    summary_rows.append(
        {
            "ID":         r["id"],
            "Priority":   r["priority"],
            "Rule Name":  r["name"],
            "Action":     ACTION_LABELS.get(r["action"], r["action"]),
            "Status":     "✅ Active" if r["is_active"] else "⏸️ Disabled",
            "Conditions": _cond_summary(r["conditions"]) or "—",
        }
    )

st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)
st.divider()

# ── Per-rule management cards ──────────────────────────────────────────────
st.markdown("#### Rule Management")

for rule in rules:
    status_icon = "✅" if rule["is_active"] else "⏸️"
    with st.expander(
        f"{status_icon} **{rule['name']}** — Priority {rule['priority']} — "
        f"{ACTION_LABELS.get(rule['action'], rule['action'])}",
        expanded=False,
    ):
        # Conditions summary
        if rule["conditions"]:
            st.markdown("**Conditions (AND)**")
            for c in rule["conditions"]:
                st.markdown(
                    f"- `{FIELD_LABELS.get(c['field_name'], c['field_name'])}`"
                    f" **{c['operator']}** `{c['value']}`"
                )
        else:
            st.warning("No conditions defined for this rule.")

        if rule["description"]:
            st.caption(f"📝 {rule['description']}")

        st.caption(
            f"Created by {rule['created_by']} on "
            f"{rule['created_at'].strftime('%Y-%m-%d') if rule['created_at'] else '—'}"
        )

        st.markdown("---")
        act1, act2, act3, act4 = st.columns(4)

        rid = rule["id"]

        # Toggle
        with act1:
            toggle_label = "⏸️ Disable" if rule["is_active"] else "▶️ Enable"
            if st.button(toggle_label, key=f"toggle_{rid}", use_container_width=True):
                res = rule_service.toggle_rule(rid)
                if res["success"]:
                    st.rerun()
                else:
                    st.error(res["error"])

        # Duplicate
        with act2:
            if st.button("📋 Duplicate", key=f"dup_open_{rid}", use_container_width=True):
                st.session_state[f"dup_open_{rid}"] = True

        # Edit
        with act3:
            if st.button("✏️ Edit", key=f"edit_open_{rid}", use_container_width=True):
                # Pre-populate edit session state
                st.session_state[f"edit_open_{rid}"] = True
                st.session_state[f"edit_conds_{rid}"] = [
                    {"id": _new_id(), **{k: c[k] for k in ("field_name", "operator", "value")}}
                    for c in rule["conditions"]
                ] or [{"id": _new_id(), "field_name": "vendor", "operator": "=", "value": ""}]

        # Delete
        with act4:
            if st.button("🗑️ Delete", key=f"del_open_{rid}", use_container_width=True, type="primary"):
                st.session_state[f"del_open_{rid}"] = True

        # ── Duplicate sub-form ─────────────────────────────────────────────
        if st.session_state.get(f"dup_open_{rid}"):
            with st.form(key=f"dup_form_{rid}"):
                new_name = st.text_input(
                    "New rule name",
                    value=f"Copy of {rule['name']}",
                    key=f"dup_name_{rid}",
                )
                c1, c2 = st.columns(2)
                if c1.form_submit_button("📋 Confirm Duplicate", type="primary"):
                    res = rule_service.duplicate_rule(rid, new_name)
                    if res["success"]:
                        st.session_state.pop(f"dup_open_{rid}", None)
                        st.success(f"Rule duplicated as '{new_name}'.")
                        st.rerun()
                    else:
                        st.error(res["error"])
                if c2.form_submit_button("Cancel"):
                    st.session_state.pop(f"dup_open_{rid}", None)
                    st.rerun()

        # ── Delete confirmation ────────────────────────────────────────────
        if st.session_state.get(f"del_open_{rid}"):
            st.warning(f"⚠️ Delete rule **{rule['name']}**? This cannot be undone.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Confirm Delete", key=f"del_confirm_{rid}", type="primary"):
                    res = rule_service.delete_rule(rid)
                    if res["success"]:
                        st.session_state.pop(f"del_open_{rid}", None)
                        st.success("Rule deleted.")
                        st.rerun()
                    else:
                        st.error(res["error"])
            with c2:
                if st.button("❌ Cancel", key=f"del_cancel_{rid}"):
                    st.session_state.pop(f"del_open_{rid}", None)
                    st.rerun()

        # ── Inline edit form ───────────────────────────────────────────────
        if st.session_state.get(f"edit_open_{rid}"):
            st.markdown("---")
            st.markdown("**✏️ Edit Rule**")

            edit_conds_key = f"edit_conds_{rid}"
            if edit_conds_key not in st.session_state:
                st.session_state[edit_conds_key] = [
                    {"id": _new_id(), **{k: c[k] for k in ("field_name", "operator", "value")}}
                    for c in rule["conditions"]
                ] or [{"id": _new_id(), "field_name": "vendor", "operator": "=", "value": ""}]

            e_col1, e_col2, e_col3 = st.columns([3, 1, 2])
            with e_col1:
                e_name = st.text_input("Rule Name", value=rule["name"], key=f"e_name_{rid}")
            with e_col2:
                e_priority = st.number_input(
                    "Priority", value=rule["priority"], min_value=1, max_value=9999,
                    step=10, key=f"e_prio_{rid}"
                )
            with e_col3:
                e_action = st.selectbox(
                    "Action",
                    options=ACTION_KEYS,
                    format_func=lambda k: RULE_ACTIONS[k],
                    index=ACTION_KEYS.index(rule["action"]) if rule["action"] in ACTION_KEYS else 0,
                    key=f"e_action_{rid}",
                )
            e_desc = st.text_area(
                "Description", value=rule["description"] or "",
                height=70, key=f"e_desc_{rid}"
            )

            st.markdown("**Conditions**")
            edit_conds = st.session_state[edit_conds_key]

            for j, ec in enumerate(list(edit_conds)):
                ecid = ec["id"]
                if j > 0:
                    st.markdown(
                        "<div style='text-align:center;color:#6b7280;font-weight:600;"
                        "margin:0.1rem 0;'>AND</div>",
                        unsafe_allow_html=True,
                    )
                ec1, ec2, ec3, ec4 = st.columns([3, 2, 3, 1])
                with ec1:
                    fi = FIELD_KEYS.index(ec.get("field_name", "vendor"))
                    sf = st.selectbox(
                        "Field", FIELD_KEYS, format_func=lambda k: FIELD_LABELS[k],
                        index=fi, key=f"e_field_{rid}_{ecid}", label_visibility="collapsed"
                    )
                    edit_conds[j]["field_name"] = sf
                ftype = SUPPORTED_FIELDS[sf]["type"]
                avail_ops = OPERATORS_BY_TYPE.get(ftype, ["="])
                with ec2:
                    cur_op = ec.get("operator", "=")
                    oi = avail_ops.index(cur_op) if cur_op in avail_ops else 0
                    so = st.selectbox(
                        "Op", avail_ops, index=oi,
                        key=f"e_op_{rid}_{ecid}", label_visibility="collapsed"
                    )
                    edit_conds[j]["operator"] = so
                with ec3:
                    if ftype == "boolean":
                        bv = st.selectbox(
                            "Val", ["True", "False"],
                            index=0 if ec.get("value", "True").lower() != "false" else 1,
                            key=f"e_val_{rid}_{ecid}", label_visibility="collapsed"
                        )
                        edit_conds[j]["value"] = bv
                    else:
                        tv = st.text_input(
                            "Val", value=ec.get("value", ""),
                            key=f"e_val_{rid}_{ecid}", label_visibility="collapsed"
                        )
                        edit_conds[j]["value"] = tv
                with ec4:
                    if len(edit_conds) > 1:
                        if st.button("🗑️", key=f"e_del_{rid}_{ecid}"):
                            st.session_state[edit_conds_key] = [
                                c for c in edit_conds if c["id"] != ecid
                            ]
                            st.rerun()

            if st.button("➕ Add Condition", key=f"e_addcond_{rid}"):
                st.session_state[edit_conds_key].append(
                    {"id": _new_id(), "field_name": "vendor", "operator": "=", "value": ""}
                )
                st.rerun()

            save_c, cancel_c = st.columns(2)
            with save_c:
                if st.button("💾 Save Changes", key=f"e_save_{rid}", type="primary"):
                    payload = [
                        {"field_name": c["field_name"], "operator": c["operator"], "value": c["value"]}
                        for c in st.session_state[edit_conds_key]
                    ]
                    res = rule_service.update_rule(
                        rule_id=rid,
                        name=e_name,
                        action=e_action,
                        conditions=payload,
                        description=e_desc or None,
                        priority=int(e_priority),
                    )
                    if res["success"]:
                        st.session_state.pop(f"edit_open_{rid}", None)
                        st.session_state.pop(edit_conds_key, None)
                        st.success("Rule updated.")
                        st.rerun()
                    else:
                        st.error(res["error"])
            with cancel_c:
                if st.button("❌ Cancel Edit", key=f"e_cancel_{rid}"):
                    st.session_state.pop(f"edit_open_{rid}", None)
                    st.session_state.pop(edit_conds_key, None)
                    st.rerun()
