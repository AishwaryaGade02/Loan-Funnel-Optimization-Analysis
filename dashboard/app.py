import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import sqlite3
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.compute_metrics import (
    get_total_applications,
    get_approval_denial_dropout_rates,
    get_total_applicants_passing_each_stage,
    conversion_rate_at_each_stage,
    dropout_rate_at_each_stage,
    get_pull_through_ratio,
    average_time_for_loan_approval,
    get_decision_to_close_time,
    get_weekly_trend
)

from src.advanced_analysis import (
    cohort_analysis,
    get_features_vs_approval,
    
)

from src.ab_testing import (
    load_experiment_data,
    run_ab_test_approval,
    run_ab_test_default
)

from src.report_alerts import (
    get_current_metrics,
    check_alerts
)

st.set_page_config(page_title="Loan Funnel Analytics", layout="wide")

# ========================= Row 1: Centered Title =========================
st.markdown("<h1 style='text-align: center;'>📊 Loan Funnel Analysis</h1>", unsafe_allow_html=True)

DB_PATH = "data/loan_funnel.db"
ALERT_LOG_PATH = "data/alerts_log.txt"

if os.path.exists(DB_PATH):

    # ========================= Row 2: Center - Total Applications =========================
    col1, col2, col3 = st.columns([1, 2, 1])
    total = get_total_applications(DB_PATH)
    st.markdown("""
    <div style="text-align: center;">
        <h3>📝 Total Applications</h3>
        <h1 style="font-size: 45px; ">{:,}</h1>
    </div>
""".format(total.iloc[0, 0]), unsafe_allow_html=True)


    # ========================= Row 3: Center - Approval, Denial, Dropout Rates =========================
    st.markdown("### ✅ Approval / ❌ Denial / 🚪 Dropout Rates")
    kpi_df = get_approval_denial_dropout_rates(DB_PATH)
    st.dataframe(kpi_df)
    # ========================= Row 8: Applicants at each stage =========================

    st.markdown("### 🚪 No of Applicants at each stage")
    funnel_order = ["Application Started", "Documents Uploaded", "Underwriting Review", "Funded"]
    conversion_df = get_total_applicants_passing_each_stage(DB_PATH)
    conversion_df['funnel_stage'] = pd.Categorical(conversion_df['funnel_stage'], categories=funnel_order, ordered=True)
    conversion_df = conversion_df.sort_values('funnel_stage')
    fig, ax = plt.subplots(figsize=(10,4))
    ax.bar(conversion_df['funnel_stage'], conversion_df['Applicants_passing'], color='royalblue')
    ax.set_ylabel("No of Applicants")

    plt.xticks(rotation=0)  # 👈 Horizontal labels
    st.pyplot(fig)
    # ========================= Row 9: Conversion & Drop-off Rate =========================
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Conversion rate at each stage")
        conversion_df = conversion_rate_at_each_stage()
        st.dataframe(conversion_df)

    with col2:
        st.subheader("Dropout rate at each stage")
        dropout_df = dropout_rate_at_each_stage()
        st.dataframe(dropout_df)
    # ========================= Row 4: Pull-through, Approval Time, Close Time =========================
    st.markdown("### ⏱️ Funnel Timing & Efficiency")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Time from Open to Approval")
        avg_time_df = average_time_for_loan_approval(DB_PATH)
        st.metric(label="Avg Approval Time (days)", value=int(avg_time_df.iloc[0, 0]))

    with col2:
        st.subheader("Time from Approval to Close")
        result = get_decision_to_close_time(DB_PATH)
        st.metric("Avg. Close Time (days)", f"{int(result.iloc[0, 0])}" if result is not None else "N/A")

    # ========================= Row 5: Full-width Weekly Trend Chart =========================
    st.markdown("### 📆 Weekly Loan Applications Trend")
    trend_df = get_weekly_trend(DB_PATH)
    st.line_chart(trend_df.set_index("week")["applications"])

    # ========================= Row 6: Left - Features vs Approval =========================
    st.markdown("### 🧮 Approval Based on Features")
    st.subheader("Approval vs. Income, Age, Credit Score")
    feat_df = get_features_vs_approval(DB_PATH)
    st.dataframe(feat_df)

    # ========================= Row 7: Cohort Analysis - Income & Credit =========================
    st.markdown("### 👥 Cohort Approval Analysis")
    col1, col2 = st.columns(2)
    credit_df, income_df = cohort_analysis(DB_PATH)

    with col1:
        st.subheader("By Income Band")
        st.dataframe(income_df)

    with col2:
        st.subheader("By Credit Score Band")
        st.dataframe(credit_df)

    
    

    


    # ========================= Row 10: A/B Testing =========================
    st.markdown("### 🧪 Approval Strategy Comparison (A/B Testing)")
    exp_df = load_experiment_data(DB_PATH)
    st.dataframe(exp_df)

    st.subheader("Impact Summary:")
    z_stat1, p_val1 = run_ab_test_approval(exp_df)
    z_stat2, p_val2 = run_ab_test_default(exp_df)

    if p_val1 < 0.05:
        st.success("✅ The new strategy significantly increased approval rates.")
    else:
        st.warning("ℹ️ No significant difference in approval rates found.")

    if p_val2 < 0.05:
        st.error("❌ The new strategy resulted in significantly higher default rates.")
    else:
        st.success("✅ The default rates remained consistent across groups.")

    # ========================= Row 11: Alerts =========================
    st.markdown("### 🚨 System Alerts")

    metrics = get_current_metrics(DB_PATH)
    alerts = check_alerts(metrics)

    if alerts:
        st.error("🚨 Recent Alerts Triggered:")
        for alert in alerts:
            st.write(alert)
    else:
        st.success("✅ All metrics are currently healthy.")

    if os.path.exists(ALERT_LOG_PATH):
        with open(ALERT_LOG_PATH, "r", encoding='utf-8') as file:
            logs = file.readlines()
            if logs:
                st.subheader("📜 Alert History Log")
                st.text("".join(logs[-10:]))

# ========================= Footer =========================
st.markdown("---")
st.caption("Built by Aishwarya Gade | Data Analytics Project Demo")
