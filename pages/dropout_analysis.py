import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import os
import sys

from src.predictive_analysis import run_predictive_analysis

def show_dropout_analysis(DB_PATH):
    if os.path.exists(DB_PATH):
        st.header("❌ Dropout Analysis")
        
        loan_data = pd.read_csv('./data/loan_funnel_data.csv')
        results = run_predictive_analysis(loan_data)

        cohort_analysis = results['cohort_analysis']
        feature_importance = results['feature_importance']
        analyzed_df = results['dataframe']

        # Key Metrics
        col2, col3, col4 = st.columns(3)
        
        with col2:
            st.metric("Average Abandonment Risk", f"{analyzed_df['abandonment_risk'].mean():.2%}")
        with col3:
            st.metric("Funding Rate", f"{analyzed_df['funded'].mean():.2%}")
        with col4:
            high_risk = (analyzed_df['abandonment_risk'] > 0.7).sum()
            st.metric("High Risk Applications", high_risk)

        # Cohort Analysis Section
        st.subheader("📊 Dropout Analysis Explorer")

        # Filters - Add new filters for income, loan amount, and employment
        col1, col2 = st.columns(2)
        with col1:
            selected_age = st.multiselect(
                "Select Age Groups",
                options=cohort_analysis['age_group'].unique(),
                default=cohort_analysis['age_group'].unique()[0]
            )
            
            selected_income = st.multiselect(
                "Select Income Bands",
                options=cohort_analysis['income_band'].unique(),
                default=cohort_analysis['income_band'].unique()[0]
            )
            
            selected_employment = st.multiselect(
                "Select Employment Status",
                options=cohort_analysis['employment_status'].unique(),
                default=cohort_analysis['employment_status'].unique()[0]
            )

        with col2:
            selected_dti = st.multiselect(
                "Select DTI Groups",
                options=cohort_analysis['dti_group'].unique(),
                default=cohort_analysis['dti_group'].unique()[0]
            )
            
            selected_credit = st.multiselect(
                "Select Credit Groups",
                options=cohort_analysis['credit_group'].unique(),
                default=cohort_analysis['credit_group'].unique()[0]
            )
            
            selected_loan_amount = st.multiselect(
                "Select Loan Amount Groups",
                options=cohort_analysis['loan_amount_group'].unique(),
                default=cohort_analysis['loan_amount_group'].unique()[0]
            )

        # Filter cohort data - update to include new filters
        filtered_cohort = cohort_analysis[
            (cohort_analysis['age_group'].isin(selected_age)) &
            (cohort_analysis['dti_group'].isin(selected_dti)) &
            (cohort_analysis['credit_group'].isin(selected_credit)) &
            (cohort_analysis['income_band'].isin(selected_income)) &
            (cohort_analysis['loan_amount_group'].isin(selected_loan_amount)) &
            (cohort_analysis['employment_status'].isin(selected_employment))
        ]

        # Display cohort table
        st.markdown("#### Dropout Performance Metrics")
        st.dataframe(
            filtered_cohort.style.background_gradient(
                subset=['abandonment_risk', 'funded'],
                cmap='RdYlGn_r'
            ).format({
                'abandonment_risk': '{:.1%}',
                'completed_app': '{:.1%}',
                'uploaded_docs': '{:.1%}',
                'passed_underwriting': '{:.1%}',
                'funded': '{:.1%}'
            })
        )

        # Interactive feature selection for Abandonment Risk
        st.subheader("🧩 Explore Abandonment Risk Relationships")

        col1, col2 = st.columns(2)
        with col1:
            primary_factor_risk = st.selectbox(
                "Primary Factor",
                options=["Age", "DTI", "Credit Score", "Income", "Loan Amount", "Employment"],
                index=2,
                key="primary_risk_factor"
            )

        with col2:
            secondary_factor_risk = st.selectbox(
                "Secondary Factor",
                options=["Age", "DTI", "Credit Score", "Income", "Loan Amount", "Employment"],
                index=1,
                key="secondary_risk_factor"
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
        # Create the pivot table for the selected factors
        if primary_factor_risk in factor_map and secondary_factor_risk in factor_map:
            primary_col = factor_map[primary_factor_risk]
            secondary_col = factor_map[secondary_factor_risk]
            
            # Create pivot table for the heatmap
            if primary_col in filtered_cohort.columns and secondary_col in filtered_cohort.columns:
                pivot_data = cohort_analysis.pivot_table(
                    values='abandonment_risk',
                    index=primary_col,
                    columns=secondary_col,
                    aggfunc='mean'
                )
                
                # Create heatmap
                fig = go.Figure(data=go.Heatmap(
                    z=pivot_data.values,
                    x=pivot_data.columns,
                    y=pivot_data.index,
                    colorscale='RdYlGn_r',
                    text=[[f'{val:.1%}' for val in row] for row in pivot_data.values],
                    texttemplate='%{text}',
                    textfont={"size": 12},
                    hoverongaps=False
                ))
                
                fig.update_layout(
                    title=f'Abandonment Risk by {primary_factor_risk} and {secondary_factor_risk}',
                    xaxis_title=f'{secondary_factor_risk} Group',
                    yaxis_title=f'{primary_factor_risk} Group'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Key insights
                st.markdown("**Key Insights:**")
                
                # Find highest and lowest risk segments
                flattened = pivot_data.stack().reset_index()
                flattened.columns = [primary_col, secondary_col, 'abandonment_risk']
                
                highest_risk = flattened.nlargest(3, 'abandonment_risk')
                lowest_risk = flattened.nsmallest(3, 'abandonment_risk')
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Highest Abandonment Risk Segments:**")
                    for _, row in highest_risk.iterrows():
                        st.write(f"- {row[primary_col]} × {row[secondary_col]}: {row['abandonment_risk']:.1%}")
                    
                    # Calculate average risk
                    avg_risk = filtered_cohort['abandonment_risk'].mean()
                    st.write(f"*Average abandonment risk: {avg_risk:.1%}*")
                
                with col2:
                    st.markdown("**Lowest Abandonment Risk Segments:**")
                    for _, row in lowest_risk.iterrows():
                        st.write(f"- {row[primary_col]} × {row[secondary_col]}: {row['abandonment_risk']:.1%}")
                    
                    # Risk differential
                    risk_diff = highest_risk.iloc[0]['abandonment_risk'] - lowest_risk.iloc[0]['abandonment_risk']
                    st.write(f"*Risk differential: {risk_diff:.1%}*")
            
            else:
                st.warning(f"Data not available for {primary_factor_risk} vs {secondary_factor_risk}. Try another combination.")
        else:
            st.warning(f"Interaction data not available for {primary_factor_risk} vs {secondary_factor_risk}.")

