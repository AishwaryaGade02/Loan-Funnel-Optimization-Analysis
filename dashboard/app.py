import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
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
    risk_metric,
    interaction_analysis
)

from src.two_way_analysis import (
    two_interaction,
    get_all_key_interactions,
    visualize_interaction
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

from src.predictive_analysis import run_predictive_analysis
from src.economic_impact import (
    run_economic_impact_analysis, 
    get_priority_cohorts, 
    create_cohort_labels
)

st.set_page_config(page_title="Loan Funnel Analytics", layout="wide")

# ========================= Row 1: Centered Title =========================
st.title("📊 Loan Funnel Analysis")
st.markdown("---")

DB_PATH = "data/loan_funnel.db"
ALERT_LOG_PATH = "data/alerts_log.txt"

if os.path.exists(DB_PATH):

    # ========================= Row 2: Key Metrics =========================
    st.header("📈 Key Metrics Overview")
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

    # ========================= Funnel Analysis Section =========================
    st.header("🔄 Funnel Stage Analysis")
    
    # Applicants at each stage
    st.subheader("Number of Applicants at Each Stage")
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

    # ========================= Timing Analysis =========================
    st.header("⏱️ Process Timing Analysis")
    col1, col2 = st.columns(2)

    with col1:
        avg_time_df = average_time_for_loan_approval(DB_PATH)
        st.metric("Average Approval Time", f"{int(avg_time_df.iloc[0, 0])} days")

    with col2:
        result = get_decision_to_close_time(DB_PATH)
        st.metric("Average Decision to Close Time", f"{int(result.iloc[0, 0])} days" if result is not None else "N/A")

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

    # ========================= Approval Analysis =========================
    st.header("🔍 Approval Analysis")
    
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
    st.subheader("👥 Approval Rate by Each Features")
    
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

    # ========================= Advanced Analysis =========================
    # ========================= Multi-Factor Analysis Explorer =========================
# New section that provides more flexible analysis
    st.subheader("🧩 Multi-Factor Loan Approval Explorer")

# Interactive feature selection
    #st.subheader("Loan Approval Rate by Multiple Factors")
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

    

    # ======================================================================
    # PREDICTIVE ANALYSIS SECTION (Keep as is)
    st.header("🤖 Dropout Analysis")
    st.markdown("---")
    loan_data = pd.read_csv('./data/loan_funnel_data.csv')
    results = run_predictive_analysis(loan_data)

    cohort_analysis = results['cohort_analysis']
    feature_importance = results['feature_importance']
    analyzed_df = results['dataframe']

    # Title
    #st.title("🎯 Predictive Drop-off Analysis")
    

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

    # Visualization Section
    # In the Multi-Factor Analysis Explorer section
    # In the Multi-Factor Analysis Explorer section
    #st.header("🧩 Risk Analysis Explorer")

# Interactive feature selection for Abandonment Risk
    st.subheader("🧩 Explore Abandonment Risk Relationships")

    col1, col2 = st.columns(2)
    with col1:
        primary_factor_risk = st.selectbox(
        "Primary Factor",
        options=["Age", "DTI", "Credit Score", "Income", "Loan Amount", "Employment"],
        index=2,  # Default to Credit Score
        key="primary_risk_factor"
    )

    with col2:
        secondary_factor_risk = st.selectbox(
        "Secondary Factor",
        options=["Age", "DTI", "Credit Score", "Income", "Loan Amount", "Employment"],
        index=1,  # Default to DTI
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
            colorscale='RdYlGn_r',  # Red for high risk, green for low risk
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

    

    # ========================= Economic Impact Analysis =========================
    st.header("💰 Economic Impact Analysis")
    st.markdown("---")
    
    # Run economic impact analysis
    economic_impact_df = run_economic_impact_analysis(loan_data)
    top_10_cohorts = get_priority_cohorts(economic_impact_df, top_n=10)
    top_10_cohorts = create_cohort_labels(top_10_cohorts)
    
    # Display key economic metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_lost_revenue = economic_impact_df['total_lost_revenue'].sum()
        st.metric("Total Lost Revenue", f"${total_lost_revenue:,.0f}")
    
    with col2:
        total_improvement_potential = economic_impact_df['improvement_potential'].sum()
        st.metric("Improvement Potential", f"${total_improvement_potential:,.0f}")
    
    with col3:
        avg_roi = economic_impact_df['roi_ratio'].mean()
        st.metric("Average ROI Ratio", f"{avg_roi:.2f}")
    
    with col4:
        total_conversion_value = economic_impact_df['conversion_improvement_value'].sum()
        st.metric("Conversion Improvement Value", f"${total_conversion_value:,.0f}")
    
    # Top 10 Priority Cohorts
    st.subheader("Top 10 Priority Cohorts by Economic Impact")
    
    # Display table
    display_columns = ['cohort', 'total_applications', 'total_lost_revenue', 
                      'improvement_potential', 'roi_ratio', 'priority_score']
    
    formatted_top_10 = top_10_cohorts[display_columns].copy()
    formatted_top_10.columns = ['Cohort', 'Total Applications', 'Lost Revenue', 
                               'Improvement Potential', 'ROI Ratio', 'Priority Score']
    
    st.dataframe(
        formatted_top_10.style.format({
            'Lost Revenue': '${:,.0f}',
            'Improvement Potential': '${:,.0f}',
            'Total Applications': '{:,.0f}',
            'ROI Ratio': '{:.2f}',
            'Priority Score': '{:.2f}'
        }).background_gradient(subset=['Priority Score'], cmap='Greens')
    )
    
    # Visualizations
    st.subheader("Economic Impact Visualizations")
    
    tab1, tab2, tab3 = st.tabs(["Lost Revenue by Cohort", "ROI Analysis", "Stage-wise Losses"])
    
    with tab1:
        # Lost Revenue Chart
        fig = px.bar(
            top_10_cohorts, 
            y='cohort', 
            x='total_lost_revenue',
            orientation='h',
            title='Total Lost Revenue by Cohort',
            color='total_lost_revenue',
            color_continuous_scale='Reds'
        )
        fig.update_layout(
            xaxis_title='Total Lost Revenue ($)',
            yaxis_title='Cohort',
            showlegend=False,
            yaxis={'categoryorder':'total ascending'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # ROI Scatter Plot
        fig = px.scatter(
            top_10_cohorts, 
            x='total_applications', 
            y='roi_ratio',
            size='improvement_potential',
            color='priority_score',
            text='cohort',
            title='ROI Analysis by Cohort (bubble size = improvement potential)',
            color_continuous_scale='Viridis'
        )
        fig.update_traces(textposition='top center')
        fig.update_layout(
            xaxis_title='Total Applications',
            yaxis_title='ROI Ratio'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Stage-wise losses for top cohorts
        st.subheader("Stage-wise Lost Revenue")
        
        # Prepare data for stage-wise visualization
        stage_columns = [col for col in top_10_cohorts.columns if col.startswith('lost_revenue_') and col != 'lost_revenue_funded']
        stage_data = []
        
        for idx, row in top_10_cohorts.head(5).iterrows():
            for col in stage_columns:
                stage_name = col.replace('lost_revenue_', '').replace('_', ' ').title()
                stage_data.append({
                    'cohort': row['cohort'],
                    'stage': stage_name,
                    'lost_revenue': row[col]
                })
        
        stage_df = pd.DataFrame(stage_data)
        
        fig = px.bar(
            stage_df,
            x='cohort',
            y='lost_revenue',
            color='stage',
            title='Lost Revenue by Stage for Top 5 Priority Cohorts',
            barmode='group'
        )
        fig.update_layout(
            xaxis_title='Cohort',
            yaxis_title='Lost Revenue ($)',
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Economic Insights
    st.subheader("📊 Economic Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Highest Economic Impact Cohorts:**")
        for idx, row in top_10_cohorts.head(3).iterrows():
            st.write(f"- **{row['cohort']}**: ${row['total_lost_revenue']:,.0f} lost revenue")
    
    with col2:
        st.markdown("**Best ROI Opportunities:**")
        best_roi = top_10_cohorts.nlargest(3, 'roi_ratio')
        for idx, row in best_roi.iterrows():
            st.write(f"- **{row['cohort']}**: {row['roi_ratio']:.2f} ROI ratio")
    
    # Recommendations
    st.subheader("💡 Strategic Recommendations")
    
    # Find cohorts with highest improvement potential
    high_potential = top_10_cohorts.nlargest(3, 'improvement_potential')
    
    st.markdown("""
    Based on the economic impact analysis, here are the key recommendations:
    
    1. **Focus on High-Priority Cohorts**: The analysis identifies specific customer segments with the highest economic impact potential.
    
    2. **Stage-Specific Interventions**: Different cohorts show different drop-off patterns across funnel stages. Tailor interventions accordingly.
    
    3. **ROI-Driven Resource Allocation**: Prioritize resources to cohorts with the highest ROI ratios for maximum efficiency.
    
    4. **Quick Wins**: Target cohorts with both high improvement potential and high ROI for immediate impact.
    """)
    
    # Display high potential cohorts
    st.markdown("**Cohorts with Highest Improvement Potential:**")
    for idx, row in high_potential.iterrows():
        st.write(f"- **{row['cohort']}**: ${row['improvement_potential']:,.0f} potential improvement")

    # ========================= A/B Testing Section =========================
    st.header("🧪 Policy Comparision")
    
    st.subheader("Approval Strategy Comparison")
    exp_df = load_experiment_data(DB_PATH)
    st.dataframe(
        exp_df.style.format({
            'approvals': '{:,}',
            'fundings': '{:,}',
            'defaults': '{:,}',
            'total_applicants': '{:,}'
        })
    )

    # Test Results
    st.subheader("Statistical Test Results")
    z_stat1, p_val1 = run_ab_test_approval(exp_df)
    z_stat2, p_val2 = run_ab_test_default(exp_df)

    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Approval Test p-value", f"{p_val1:.4f}")
        if p_val1 < 0.05:
            st.success("✅ Significant difference in approval rates")
        else:
            st.info("ℹ️ No significant difference in approval rates")

    with col2:
        st.metric("Default Test p-value", f"{p_val2:.4f}")
        if p_val2 < 0.05:
            st.error("❌ Significant difference in default rates")
        else:
            st.success("✅ No significant difference in default rates")

    # ========================= System Alerts =========================
    st.header("🚨 System Monitoring")

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

# ========================= Footer =========================
st.markdown("---")
st.caption("Built by Aishwarya Gade | Data Analytics Project Demo")