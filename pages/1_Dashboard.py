"""
Dashboard — overview of rules and evaluation activity.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from database.db import init_db
from services import audit_service, rule_service

st.set_page_config(
    page_title="Dashboard | Invoice Rule Engine",
    page_icon="📊",
    layout="wide",
)

if "db_initialized" not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

# ── Header ─────────────────────────────────────────────────────────────────
st.title("📊 Dashboard")
st.caption("Real-time overview of rules and invoice routing activity")
st.divider()

# ── KPI cards ──────────────────────────────────────────────────────────────
rule_stats  = rule_service.get_stats()
audit_stats = audit_service.get_audit_stats()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("📋 Total Rules",      rule_stats["total"])
kpi2.metric("✅ Active Rules",     rule_stats["active"])
kpi3.metric("⏸️ Disabled Rules",   rule_stats["inactive"])
kpi4.metric("🔁 Total Evaluations", audit_stats["total"])

st.divider()

# ── Two-column section ─────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 2], gap="large")

with col_left:
    st.markdown("#### Decision Breakdown")
    by_decision = audit_stats.get("by_decision", {})

    ACTION_ICONS = {
        "BYPASS_HUMAN_QUEUE":  "✅",
        "SEND_TO_HUMAN_QUEUE": "⏳",
        "BLOCK_POSTING":       "🚫",
    }
    ACTION_LABELS = {
        "BYPASS_HUMAN_QUEUE":  "Bypass Human Queue",
        "SEND_TO_HUMAN_QUEUE": "Send to Human Queue",
        "BLOCK_POSTING":       "Block Posting",
    }

    if by_decision:
        for decision, count in by_decision.items():
            icon  = ACTION_ICONS.get(decision, "•")
            label = ACTION_LABELS.get(decision, decision)
            st.metric(f"{icon} {label}", count)
    else:
        st.info("No evaluations recorded yet.")

with col_right:
    st.markdown("#### Recent Evaluations (last 10)")
    logs = audit_service.get_audit_logs(limit=10)

    if logs:
        rows = []
        for log in logs:
            rows.append(
                {
                    "Timestamp":    log["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                                    if log["timestamp"] else "—",
                    "Invoice ID":   log["invoice_id"] or "—",
                    "Matched Rule": log["matched_rule"] or "No match",
                    "Decision":     ACTION_LABELS.get(log["decision"], log["decision"]),
                    "Time (ms)":    f"{log['execution_time_ms']:.1f}",
                }
            )
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No evaluations yet. Go to **Test Rules** to evaluate an invoice.")

st.divider()

# ── Active rules summary ───────────────────────────────────────────────────
st.markdown("#### Active Rules (by Priority)")
rules = rule_service.get_all_rules(active_only=True)

if rules:
    rows = []
    for r in rules:
        cond_summary = " AND ".join(
            f"{c['field_name']} {c['operator']} {c['value']}"
            for c in r["conditions"]
        )
        rows.append(
            {
                "Priority":   r["priority"],
                "Rule Name":  r["name"],
                "Action":     ACTION_LABELS.get(r["action"], r["action"]),
                "Conditions": cond_summary or "—",
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.warning("No active rules. Click **Create Rule** in the sidebar to add one.")

st.divider()

# ── Quick-action buttons ───────────────────────────────────────────────────
st.markdown("#### Quick Actions")
qa1, qa2, qa3, qa4 = st.columns(4)
with qa1:
    if st.button("➕ Create Rule", use_container_width=True, type="primary"):
        st.switch_page("pages/2_Create_Rule.py")
with qa2:
    if st.button("⚙️ Manage Rules", use_container_width=True):
        st.switch_page("pages/3_Manage_Rules.py")
with qa3:
    if st.button("🧪 Test Rules", use_container_width=True):
        st.switch_page("pages/4_Test_Rules.py")
with qa4:
    if st.button("📜 Audit Logs", use_container_width=True):
        st.switch_page("pages/5_Audit.py")
