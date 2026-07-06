"""
Audit Logs page — browse, filter and export evaluation history.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from database.db import init_db
from services import audit_service

st.set_page_config(
    page_title="Audit Logs | Invoice Rule Engine",
    page_icon="📜",
    layout="wide",
)

if "db_initialized" not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

ACTION_LABELS = {
    "BYPASS_HUMAN_QUEUE":  "Bypass Human Queue",
    "SEND_TO_HUMAN_QUEUE": "Send to Human Queue",
    "BLOCK_POSTING":       "Block Posting",
}

# ── Page ───────────────────────────────────────────────────────────────────
st.title("📜 Audit Logs")
st.caption("Full history of every invoice evaluation decision.")
st.divider()

# ── Stats strip ────────────────────────────────────────────────────────────
stats = audit_service.get_audit_stats()
by_dec = stats.get("by_decision", {})

s1, s2, s3, s4 = st.columns(4)
s1.metric("Total Evaluations",   stats["total"])
s2.metric("✅ Bypassed",          by_dec.get("BYPASS_HUMAN_QUEUE", 0))
s3.metric("⏳ Queued",            by_dec.get("SEND_TO_HUMAN_QUEUE", 0))
s4.metric("🚫 Blocked",           by_dec.get("BLOCK_POSTING", 0))

st.divider()

# ── Filters (sidebar) ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Filters")

    decision_filter = st.selectbox(
        "Decision",
        options=["All"] + list(ACTION_LABELS.keys()),
        format_func=lambda k: "All" if k == "All" else ACTION_LABELS.get(k, k),
        key="audit_decision_filter",
    )

    page_size = st.selectbox(
        "Rows per page",
        options=[25, 50, 100, 250],
        index=1,
        key="audit_page_size",
    )

    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

# ── Fetch logs ─────────────────────────────────────────────────────────────
filter_arg = decision_filter if decision_filter != "All" else None
logs = audit_service.get_audit_logs(
    limit=int(page_size),
    decision_filter=filter_arg,
)

# ── Table ──────────────────────────────────────────────────────────────────
if not logs:
    st.info("No audit logs found. Evaluate an invoice on the **Test Rules** page.")
else:
    st.markdown(f"Showing **{len(logs)}** record(s) (most recent first)")

    rows = []
    for log in logs:
        rows.append(
            {
                "ID":           log["id"],
                "Timestamp":    log["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                                if log["timestamp"] else "—",
                "Invoice ID":   log["invoice_id"] or "—",
                "Matched Rule": log["matched_rule"] or "No match",
                "Decision":     ACTION_LABELS.get(log["decision"], log["decision"]),
                "Time (ms)":    f"{log['execution_time_ms']:.2f}",
                "Error":        "⚠️" if log["error_message"] else "",
            }
        )

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()

    # ── Export ─────────────────────────────────────────────────────────────
    st.markdown("#### Export")
    csv_data = audit_service.export_to_csv(logs)
    st.download_button(
        label="⬇️ Download as CSV",
        data=csv_data,
        file_name="audit_logs.csv",
        mime="text/csv",
        type="primary",
    )

    # ── Detail view ────────────────────────────────────────────────────────
    st.divider()
    st.markdown("#### Log Detail")

    if logs:
        log_ids = [str(log["id"]) for log in logs]
        selected_id = st.selectbox("Select a log entry to inspect:", options=log_ids, key="audit_detail_id")

        selected_log = next((log for log in logs if str(log["id"]) == selected_id), None)
        if selected_log:
            import json as _json

            d1, d2, d3 = st.columns(3)
            d1.metric("Decision",   ACTION_LABELS.get(selected_log["decision"], selected_log["decision"]))
            d2.metric("Time (ms)",  f"{selected_log['execution_time_ms']:.2f}")
            d3.metric("Invoice ID", selected_log["invoice_id"] or "—")

            if selected_log["matched_rule"]:
                st.success(f"🔍 Matched Rule: **{selected_log['matched_rule']}**")
            else:
                st.info("No rule matched — default action was applied.")

            if selected_log["error_message"]:
                st.error(f"⚠️ Error: {selected_log['error_message']}")

            if selected_log["invoice_data"]:
                st.markdown("**Invoice Snapshot**")
                try:
                    st.json(_json.loads(selected_log["invoice_data"]))
                except Exception:
                    st.code(selected_log["invoice_data"])
