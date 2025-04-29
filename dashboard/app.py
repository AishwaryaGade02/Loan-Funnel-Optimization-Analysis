import streamlit as st
import pandas as pd
import sqlite3
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.compute_metrics import(
    get_approval_funding_rates,
    get_stage_conversion_rates,
    get_weekly_trend
)

from src.advanced_analysis import(
    cohort_analysis,
    get_features_vs_approval,
    dropoff_analysis
)

from src.ab_testing import(
    load_experiment_data,
    run_ab_test_approval,
    run_ab_test_default
)
from src.report_alerts import(
    get_current_metrics,
    check_alerts
)

st.set_page_config(page_title="Loan Funnel Analytics", layout="wide")
st.title("📊 Loan Funnel Optimization Dashboard")

DB_PATH = "data/loan_funnel.db"
ALERT_LOG_PATH = "data/alerts_log.txt"

st.header("📈 Funnel Metrics Overview")
if os.path.exists(DB_PATH):
    col1,col2 = st.columns(2)
    with col1:
        st.subheader("Stage-wise Conversion Rates")
        conv_df = get_stage_conversion_rates(DB_PATH)
        st.dataframe(conv_df)
    with col2:
        st.header("Approval & Funding Rates")
        kpi_df = get_approval_funding_rates(DB_PATH)
        st.dataframe(kpi_df)
    
    st.subheader("Weekly Application Trend")
    trend_df = get_weekly_trend(DB_PATH)
    st.line_chart(trend_df.set_index("week")["applications"])

st.header("🧪 A/B Testing Analysis")

exp_df = load_experiment_data(DB_PATH)
st.dataframe(exp_df)

st.subheader("Z-Test: Approval Rate Difference")
z_stat1, p_val1 = run_ab_test_approval(exp_df)
st.write(f"Z-statistic: {z_stat1: .4f}")
st.write(f"P-value: {p_val1: .4f}")
if p_val1 < 0.05:
    st.success("✅ Statistically Significant Difference in Approval Rates")
else: 
    st.warning("❌ No Significant Difference in Approval Rates")

st.subheader("Z-Test: Default Rate Difference")
z_stat2, p_val2 = run_ab_test_default(exp_df)
st.write(f"Z-statistic: {z_stat2: .4f}")
st.write(f"P-value: {p_val2: .4f}")
if p_val2 < 0.05:
    st.success("✅ Statistically Significant Difference in Default Rates")
else:
    st.warning("❌ No Significant Difference in Default Rates")

st.header("📊 Advanced Feature Analysis")

st.subheader("Approval vs. Income, Age, Credit Score")
feat_df = get_features_vs_approval(DB_PATH)
st.dataframe(feat_df)

st.subheader("Cohort: Credit Band vs Approval")
credit_df, income_df = cohort_analysis(DB_PATH)
st.dataframe(credit_df)

st.subheader("Cohort: Income Band vs Approval")
st.dataframe(income_df)

st.subheader("Drop-Off by Funnel Stage")
drop_df = dropoff_analysis(DB_PATH)
st.bar_chart(drop_df.set_index("funnel_stage")["count_stage"])

st.header("🚨 KPI Alerts")

metrics = get_current_metrics(DB_PATH)
alerts = check_alerts(metrics)

if alerts:
    st.error("🚨 Recent Alerts Triggered:")
    for alert in alerts:
        st.write(alert)
else:
    st.success("✅ All metrics are currently healthy.")

if os.path.exists(ALERT_LOG_PATH):
    with open(ALERT_LOG_PATH, "r",encoding='utf-8') as file:
        logs = file.readlines()
        if logs:
            st.subheader("📜 Alert History Log")
            st.text("".join(logs[-10:]))

st.markdown("---")
st.caption("Built by Aishwarya Gade | Data Analysis Project Demo")
