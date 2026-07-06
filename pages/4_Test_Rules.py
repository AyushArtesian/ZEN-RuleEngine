"""
Test Rules page — paste an invoice JSON and evaluate it against active rules.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from database.db import init_db
from engine.evaluator import evaluate_invoice

st.set_page_config(
    page_title="Test Rules | Invoice Rule Engine",
    page_icon="🧪",
    layout="wide",
)

if "db_initialized" not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

# ── Sample invoices ────────────────────────────────────────────────────────
SAMPLES = {
    "Vendor A — Validation Failed": json.dumps(
        {
            "invoiceId":       "INV-001",
            "vendor":          "Vendor A",
            "amount":          5000.00,
            "currency":        "USD",
            "country":         "USA",
            "store":           "Store-01",
            "validationPassed": False,
            "missingFields":   ["InvoiceNumber"],
        },
        indent=2,
    ),
    "Vendor B — High Value": json.dumps(
        {
            "invoiceId":       "INV-002",
            "vendor":          "Vendor B",
            "amount":          45000.00,
            "currency":        "EUR",
            "country":         "Germany",
            "store":           "Store-02",
            "validationPassed": True,
            "missingFields":   [],
        },
        indent=2,
    ),
    "Vendor C — Blocked": json.dumps(
        {
            "invoiceId":       "INV-003",
            "vendor":          "Vendor C",
            "amount":          200.00,
            "currency":        "GBP",
            "country":         "UK",
            "store":           "Store-03",
            "validationPassed": False,
            "missingFields":   ["PurchaseOrder", "TaxId"],
        },
        indent=2,
    ),
}

ACTION_COLORS = {
    "BYPASS_HUMAN_QUEUE":  "success",
    "SEND_TO_HUMAN_QUEUE": "warning",
    "BLOCK_POSTING":       "error",
}
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

# ── Page ───────────────────────────────────────────────────────────────────
st.title("🧪 Test Rules")
st.caption("Paste an invoice JSON and evaluate it against all active rules.")
st.divider()

left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown("#### Invoice JSON Input")

    # Sample selector
    sample_choice = st.selectbox(
        "Load a sample invoice:",
        options=["(blank)"] + list(SAMPLES.keys()),
        key="tr_sample",
    )

    default_json = SAMPLES.get(sample_choice, "") if sample_choice != "(blank)" else ""

    invoice_text = st.text_area(
        "Paste invoice JSON",
        value=default_json,
        height=350,
        key="tr_invoice_input",
        placeholder='{\n  "vendor": "Vendor A",\n  "amount": 5000,\n  "validationPassed": false\n}',
        label_visibility="collapsed",
    )

    invoice_id = st.text_input(
        "Invoice ID (optional)",
        key="tr_invoice_id",
        placeholder="INV-001",
        help="Used for audit logging only.",
    )

    evaluate_btn = st.button("▶️ Evaluate", type="primary", use_container_width=True)

with right:
    st.markdown("#### Evaluation Result")

    if evaluate_btn:
        if not invoice_text.strip():
            st.error("Please enter invoice JSON.")
        else:
            # Validate JSON
            try:
                invoice_data = json.loads(invoice_text)
            except json.JSONDecodeError as exc:
                st.error(f"❌ Invalid JSON: {exc}")
                st.stop()

            if not isinstance(invoice_data, dict):
                st.error("Invoice JSON must be a JSON object (dict), not a list or scalar.")
                st.stop()

            with st.spinner("Evaluating…"):
                result = evaluate_invoice(
                    invoice_data=invoice_data,
                    invoice_id=invoice_id.strip() or None,
                )

            # Display result
            color_fn = getattr(st, ACTION_COLORS.get(result.action, "info"))
            icon  = ACTION_ICONS.get(result.action, "•")
            label = ACTION_LABELS.get(result.action, result.action)

            color_fn(f"### {icon} {label}")

            st.markdown("---")
            col_a, col_b = st.columns(2)
            col_a.metric("Action",      label)
            col_b.metric("Time (ms)",   f"{result.execution_time_ms:.2f}")

            st.markdown("**Matched Rule**")
            if result.matched_rule:
                st.success(f"🔍 {result.matched_rule}")
            else:
                st.info("No rule matched — default action applied.")

            st.markdown("**Decision Path**")
            for step in result.decision_path:
                st.markdown(f"- {step}")

            if result.error:
                st.markdown("**Engine Error**")
                st.error(result.error)

            st.markdown("**Invoice Data (parsed)**")
            st.json(invoice_data)

    else:
        st.info(
            "Enter an invoice JSON on the left and click **Evaluate** to see the "
            "routing decision."
        )

        st.markdown("---")
        st.markdown("**Invoice fields supported:**")
        from engine.rule_builder import SUPPORTED_FIELDS

        for field, info in SUPPORTED_FIELDS.items():
            st.markdown(f"- `{field}` — {info['label']} *(type: {info['type']})*")
