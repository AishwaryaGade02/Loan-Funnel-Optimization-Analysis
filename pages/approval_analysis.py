import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import os
import sys

from src.advanced_analysis import (
    cohort_analysis,
    get_features_vs_approval,
    risk_metric,
    interaction_analysis
)

from src.two_way_analysis import (
    two_interaction,
    get_all_key_interactions,
    visualize_interaction
)

def show_approval_analysis(DB_PATH):
    if os.path.exists(DB_PATH):
        st.header("✅ Approval Analysis")
        
        st.subheader("Average Values for Approvals")
        feat_df = get_features_vs_approval(DB_PATH)
        st.dataframe(
            feat_df.style.format({
                'avg_income': '${:,.0f}',
                'avg_age': '{:.0f}',
                'avg_credit_score': '{:.0f}'
            })
        )

        # ========================= Cohort Analysis =========================
        st.subheader("👥 Approval Rate by Feature")
        
        credit_df, income_df, emp_df, loan_amo_df, age_df = cohort_analysis(DB_PATH)

        # Create tabs for different cohort analyses
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Income", "Credit Score", "Employment", "Loan Amount", "Age"])
        
        with tab1:
            st.markdown("##### By Income Band")
            st.dataframe(
                income_df.style.background_gradient(
                    subset=['approval_rate'],
                    cmap='RdYlGn'
                ).format({'approval_rate': '{:.1f}%'})
            )

        with tab2:
            st.markdown("##### By Credit Score Band")
            st.dataframe(
                credit_df.style.background_gradient(
                    subset=['approval_rate'],
                    cmap='RdYlGn'
                ).format({'approval_rate': '{:.1f}%'})
            )

        with tab3:
            st.markdown("##### By Employment Status")
            st.dataframe(
                emp_df.style.background_gradient(
                    subset=['approval_rate'],
                    cmap='RdYlGn'
                ).format({'approval_rate': '{:.1f}%'})
            )

        with tab4:
            st.markdown("##### By Loan Amount")
            st.dataframe(
                loan_amo_df.style.background_gradient(
                    subset=['approval_rate'],
                    cmap='RdYlGn'
                ).format({'approval_rate': '{:.1f}%'})
            )

        with tab5:
            st.markdown("##### By Age Group")
            st.dataframe(
                age_df.style.background_gradient(
                    subset=['approval_rate'],
                    cmap='RdYlGn'
                ).format({'approval_rate': '{:.1f}%'})
            )

        # ========================= Multi-Factor Analysis Explorer =========================
        st.subheader("🧩 Multi-Factor Loan Approval Explorer")

        # Interactive feature selection
        all_interactions = get_all_key_interactions(DB_PATH)
        col1, col2 = st.columns(2)
        with col1:
            primary_factor = st.selectbox(
                "Primary Factor",
                options=["Age", "DTI", "Credit Score", "Income", "Loan Amount", "Employment"],
                index=2,
                key="primary_approval_factor"
            )

        with col2:
            secondary_factor = st.selectbox(
                "Secondary Factor",
                options=["Age", "DTI", "Credit Score", "Income", "Loan Amount", "Employment"],
                index=1,
                key="secondary_approval_factor"
            )

        # Factor mapping dictionary
        factor_map = {
            "Age": "age_group",
            "DTI": "dti_group",
            "Credit Score": "credit_group",
            "Income": "income_band",
            "Loan Amount": "loan_amount_group",
            "Employment": "employment_status"
        }

        # Get the interaction key based on selected factors
        interaction_keys = {
            ('Age', 'DTI'): 'age_group_vs_dti_group',
            ('Age', 'Credit Score'): 'age_group_vs_credit_group',
            ('DTI', 'Credit Score'): 'dti_group_vs_credit_group',
            ('Credit Score', 'Loan Amount'): 'credit_group_vs_loan_amount_group',
            ('Income', 'Credit Score'): 'income_band_vs_credit_group',
            ('Income', 'DTI'): 'income_band_vs_dti_group'
        }

        # Try both combinations of factors to handle order differences
        interaction_key = interaction_keys.get((primary_factor, secondary_factor)) or interaction_keys.get((secondary_factor, primary_factor))

        if interaction_key and interaction_key in all_interactions:
            interaction_df = all_interactions[interaction_key]
            var1 = factor_map[primary_factor]
            var2 = factor_map[secondary_factor]
        
            # Create heatmap
            if var1 in interaction_df.columns and var2 in interaction_df.columns:
                fig = visualize_interaction(interaction_df, var1, var2)
                st.plotly_chart(fig, use_container_width=True)
            
                # Key insights
                st.markdown("**Key Insights:**")
            
                # Find highest and lowest approval rates
                highest = interaction_df.nlargest(3, 'approval_rate')
                lowest = interaction_df.nsmallest(3, 'approval_rate')
            
                col1, col2 = st.columns(2)
            
                with col1:
                    st.markdown("**Highest Approval Rates:**")
                    for _, row in highest.iterrows():
                        st.write(f"- {row[var1]} × {row[var2]}: {row['approval_rate']:.1f}%")
            
                with col2:
                    st.markdown("**Lowest Approval Rates:**")
                    for _, row in lowest.iterrows():
                        st.write(f"- {row[var1]} × {row[var2]}: {row['approval_rate']:.1f}%")
            else:
                st.warning(f"Data not available for {primary_factor} vs {secondary_factor}. Try another combination.")
        else:
            st.warning(f"Interaction data not available for {primary_factor} vs {secondary_factor}. Try another combination.")

