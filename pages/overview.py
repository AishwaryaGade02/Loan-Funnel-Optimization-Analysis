import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import os
import sys

from src.compute_metrics import (
        get_total_applications,
        get_approval_denial_dropout_rates,
        get_total_applicants_passing_each_stage,
        conversion_rate_at_each_stage,
        dropout_rate_at_each_stage,
        average_time_for_loan_approval,
        get_decision_to_close_time,
        get_weekly_trend
    )

from src.report_alerts import (
        get_current_metrics,
        check_alerts
    )

def show_overview(DB_PATH, ALERT_LOG_PATH):
    if os.path.exists(DB_PATH):
        col1, col2, col3, col4 = st.columns(4)
        
        total = get_total_applications(DB_PATH)
        kpi_df = get_approval_denial_dropout_rates(DB_PATH)
        
        with col1:
            st.metric("Total Applications", f"{total.iloc[0, 0]:,}")
        with col2:
            st.metric("Approval Rate", f"{kpi_df.iloc[0, 0]:.1f}%")
        with col3:
            st.metric("Denial Rate", f"{kpi_df.iloc[0, 1]:.1f}%")
        with col4:
            st.metric("Dropout Rate", f"{kpi_df.iloc[0, 2]:.1f}%")

        # Weekly Trend
        st.subheader("Weekly Application Volume Trend")
        trend_df = get_weekly_trend(DB_PATH)
        fig = px.line(
            trend_df, 
            x='week', 
            y='applications',
            title='Weekly Loan Applications',
            line_shape='spline'
        )
        fig.update_traces(line_color='#1f77b4', line_width=3)
        st.plotly_chart(fig, use_container_width=True)

        # Funnel Analysis Section
        st.subheader("🔄 Funnel Stage Analysis")
        
        # Applicants at each stage
        #st.subheader("Number of Applicants at Each Stage")
        funnel_order = ["Application Started", "Documents Uploaded", "Underwriting Review", "Approved", "Funded"]
        conversion_df = get_total_applicants_passing_each_stage(DB_PATH)
        conversion_df['funnel_stage'] = pd.Categorical(conversion_df['funnel_stage'], categories=funnel_order, ordered=True)
        conversion_df = conversion_df.sort_values('funnel_stage')
        
        fig = px.bar(
            conversion_df, 
            x='funnel_stage', 
            y='Applicants_passing',
            title='Applicants at Each Stage',
            color='Applicants_passing',
            color_continuous_scale='Blues'
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        # Conversion and Dropout Rates
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Conversion Rate at Each Stage")
            conversion_df = conversion_rate_at_each_stage()
            st.dataframe(
                conversion_df.style.background_gradient(
                    subset=['Conversion Rate (%)'],
                    cmap='Greens'
                ).format({'Conversion Rate (%)': '{:.1f}%'})
            )

        with col2:
            st.subheader("Dropout Rate at Each Stage")
            dropout_df = dropout_rate_at_each_stage()
            st.dataframe(
                dropout_df.style.background_gradient(
                    subset=['Dropout Rate (%)'],
                    cmap='Reds'
                ).format({'Dropout Rate (%)': '{:.1f}%'})
            )

        # Timing Analysis
        st.subheader("⏱️ Process Timing Analysis")
        st.markdown("""
        <style>
            [data-testid="stMetricValue"] {
            font-size: 1.8rem !important;
        }
        [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        font-weight: 400 !important;
        }
        [data-testid="stMetricDelta"] {
        font-size: 0.8rem !important;
        }
        </style>
        """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            avg_time_df = average_time_for_loan_approval(DB_PATH)
            st.metric("Average Approval Time", f"{int(avg_time_df.iloc[0, 0])} days")

        with col2:
            result = get_decision_to_close_time(DB_PATH)
            st.metric("Average Decision to Close Time", f"{int(result.iloc[0, 0])} days" if result is not None else "N/A")

        

        # System Monitoring
        st.subheader("🚨 System Monitoring")
        metrics = get_current_metrics(DB_PATH)
        alerts = check_alerts(metrics)

        if alerts:
            st.error("Recent Alerts Triggered:")
            for alert in alerts:
                st.warning(alert)
        else:
            st.success("✅ All metrics are currently within normal ranges")

        if os.path.exists(ALERT_LOG_PATH):
            with open(ALERT_LOG_PATH, "r", encoding='utf-8') as file:
                logs = file.readlines()
                if logs:
                    st.subheader("Alert History")
                    st.text("".join(logs[-10:]))
    else:
        st.error("Database not found. Please check the path.")

