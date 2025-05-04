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
from src.economic_impact import run_economic_impact_analysis, get_priority_cohorts, create_cohort_labels

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

    # ========================= Feature Analysis =========================
    st.header("🔍 Feature-Based Analysis")
    
    st.subheader("Approval Rates by Key Features")
    feat_df = get_features_vs_approval(DB_PATH)
    st.dataframe(
        feat_df.style.format({
            'avg_income': '${:,.0f}',
            'avg_age': '{:.0f}',
            'avg_credit_score': '{:.0f}'
        })
    )

    # ========================= Cohort Analysis =========================
    st.header("👥 Cohort Analysis")
    
    credit_df, income_df, emp_df, loan_amo_df, age_df = cohort_analysis(DB_PATH)

    # Create tabs for different cohort analyses
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Income", "Credit Score", "Employment", "Loan Amount", "Age"])
    
    with tab1:
        st.subheader("By Income Band")
        st.dataframe(
            income_df.style.background_gradient(
                subset=['approval_rate'],
                cmap='RdYlGn'
            ).format({'approval_rate': '{:.1f}%'})
        )

    with tab2:
        st.subheader("By Credit Score Band")
        st.dataframe(
            credit_df.style.background_gradient(
                subset=['approval_rate'],
                cmap='RdYlGn'
            ).format({'approval_rate': '{:.1f}%'})
        )

    with tab3:
        st.subheader("By Employment Status")
        st.dataframe(
            emp_df.style.background_gradient(
                subset=['approval_rate'],
                cmap='RdYlGn'
            ).format({'approval_rate': '{:.1f}%'})
        )

    with tab4:
        st.subheader("By Loan Amount")
        st.dataframe(
            loan_amo_df.style.background_gradient(
                subset=['approval_rate'],
                cmap='RdYlGn'
            ).format({'approval_rate': '{:.1f}%'})
        )

    with tab5:
        st.subheader("By Age Group")
        st.dataframe(
            age_df.style.background_gradient(
                subset=['approval_rate'],
                cmap='RdYlGn'
            ).format({'approval_rate': '{:.1f}%'})
        )

    # ========================= Advanced Analysis =========================
    st.header("🔬 Advanced Analytics")
    
    # Two-way Interaction Analysis
    st.subheader("Two-way Interaction Analysis")
    
    # Get all key interactions
    all_interactions = get_all_key_interactions(DB_PATH)
    
    # Create tabs for different interactions
    interaction_tabs = st.tabs([
        "Age vs DTI",
        "DTI vs Credit Score",
        "Credit Score vs Loan Amount",
        "Age vs Credit Score",
        "Income vs Credit Score",
        "Income vs DTI"
    ])
    
    tab_data = [
        ('age_group_vs_dti_group', 'age_group', 'dti_group'),
        ('dti_group_vs_credit_group', 'dti_group', 'credit_group'),
        ('credit_group_vs_loan_amount_group', 'credit_group', 'loan_amount_group'),
        ('age_group_vs_credit_group', 'age_group', 'credit_group'),
        ('income_band_vs_credit_group', 'income_band', 'credit_group'),
        ('income_band_vs_dti_group', 'income_band', 'dti_group')
    ]
    
    for tab, (interaction_key, var1_col, var2_col) in zip(interaction_tabs, tab_data):
        with tab:
            interaction_df = all_interactions[interaction_key]
            
            # Display the data table
            st.dataframe(
                interaction_df.style.background_gradient(
                    subset=['approval_rate'],
                    cmap='RdYlGn'
                ).format({
                    'approval_rate': '{:.1f}%',
                    'funding_rate': '{:.1f}%',
                    'total_applications': '{:,}',
                    'approved_count': '{:,}',
                    'funded_count': '{:,}'
                })
            )
            
            # Create and display heatmap
            fig = visualize_interaction(interaction_df, var1_col, var2_col)
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
                    st.write(f"- {row[var1_col]} × {row[var2_col]}: {row['approval_rate']:.1f}%")
            
            with col2:
                st.markdown("**Lowest Approval Rates:**")
                for _, row in lowest.iterrows():
                    st.write(f"- {row[var1_col]} × {row[var2_col]}: {row['approval_rate']:.1f}%")

    # Complex Interaction Analysis
    st.subheader("Complex Interaction Analysis")
    df = interaction_analysis(DB_PATH)
    st.dataframe(df)

    # Risk Analysis
    st.subheader("Risk Metrics Analysis")
    risk_df = risk_metric(DB_PATH)
    st.dataframe(
    risk_df.style.background_gradient(
        subset=['approval_rate'],  # Changed from 'risk_score' to 'approval_rate'
        cmap='RdYlGn'  # Changed to RdYlGn for approval rates (green=good, red=bad)
    ).format({'approval_rate': '{:.1f}%'})  # Added formatting for approval rate
)

    # ======================================================================
    # PREDICTIVE ANALYSIS SECTION (Keep as is)
    st.header("🤖 Predictive Analytics")
    loan_data = pd.read_csv('./data/loan_funnel_data.csv')
    results = run_predictive_analysis(loan_data)

    cohort_analysis = results['cohort_analysis']
    feature_importance = results['feature_importance']
    analyzed_df = results['dataframe']

    # Title
    st.title("🎯 Predictive Drop-off Analysis")
    st.markdown("---")

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
    st.header("📊 Cohort Analysis")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_age = st.multiselect(
            "Select Age Groups",
            options=cohort_analysis['age_group'].unique(),
            default=cohort_analysis['age_group'].unique()
        )
    with col2:
        selected_dti = st.multiselect(
            "Select DTI Groups",
            options=cohort_analysis['dti_group'].unique(),
            default=cohort_analysis['dti_group'].unique()
        )
    with col3:
        selected_credit = st.multiselect(
            "Select Credit Groups",
            options=cohort_analysis['credit_group'].unique(),
            default=cohort_analysis['credit_group'].unique()
        )

    # Filter cohort data
    filtered_cohort = cohort_analysis[
        (cohort_analysis['age_group'].isin(selected_age)) &
        (cohort_analysis['dti_group'].isin(selected_dti)) &
        (cohort_analysis['credit_group'].isin(selected_credit))
    ]

    # Display cohort table
    st.subheader("Cohort Performance Metrics")
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
    st.header("📈 Visualizations")

    tab1, tab2, tab3, tab4 = st.tabs(["Risk Heatmap", "Funnel Performance", "Feature Importance", "Risk Distribution"])

    with tab1:
        # Risk Heatmap
        st.subheader("Abandonment Risk Heatmap")
        
        pivot_data = filtered_cohort.pivot_table(
            values='abandonment_risk',
            index='credit_group',
            columns='dti_group',
            aggfunc='mean'
        )
        
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
            title='Abandonment Risk by Credit Score and DTI',
            xaxis_title='DTI Group',
            yaxis_title='Credit Score Group'
        )
        
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        # Funnel Performance
        st.subheader("Funnel Stage Performance")
        
        funnel_metrics = filtered_cohort[['age_group', 'completed_app', 'uploaded_docs', 
                                        'passed_underwriting', 'funded']].melt(
            id_vars=['age_group'],
            var_name='Stage',
            value_name='Rate'
        )
        
        fig = px.bar(
            funnel_metrics,
            x='age_group',
            y='Rate',
            color='Stage',
            barmode='group',
            title='Conversion Rates by Age Group'
        )
        
        fig.update_layout(yaxis_tickformat='.0%')
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        # Feature Importance
        st.subheader("Feature Importance by Stage")
        
        fig = px.bar(
            feature_importance,
            x='feature',
            y='importance',
            color='stage',
            barmode='group',
            title='Model Feature Importance'
        )
        
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        # Risk Distribution
        st.subheader("Abandonment Risk Distribution")
        
        fig = px.histogram(
            analyzed_df,
            x='abandonment_risk',
            nbins=30,
            title='Distribution of Abandonment Risk Scores'
        )
        
        fig.update_layout(
            xaxis_title='Abandonment Risk Score',
            yaxis_title='Count',
            bargap=0.1
        )
        
        st.plotly_chart(fig, use_container_width=True)

    # High Risk Segments
    st.header("🚨 High Risk Segments")

    high_risk_cohorts = cohort_analysis[cohort_analysis['abandonment_risk'] > 0.5].sort_values(
        'abandonment_risk', ascending=False
    ).head(10)

    st.dataframe(
        high_risk_cohorts.style.background_gradient(
            subset=['abandonment_risk'],
            cmap='Reds'
        ).format({
            'abandonment_risk': '{:.1%}',
            'completed_app': '{:.1%}',
            'uploaded_docs': '{:.1%}',
            'passed_underwriting': '{:.1%}',
            'funded': '{:.1%}'
        })
    )

    # Insights
    st.header("💡 Key Insights")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Highest Risk Groups")
        highest_risk = cohort_analysis.nlargest(3, 'abandonment_risk')
        for _, row in highest_risk.iterrows():
            st.write(f"- **{row['age_group']} | {row['dti_group']} | {row['credit_group']}**: {row['abandonment_risk']:.1%} risk")

    with col2:
        st.subheader("Best Performing Groups")
        best_performing = cohort_analysis.nlargest(3, 'funded')
        for _, row in best_performing.iterrows():
            st.write(f"- **{row['age_group']} | {row['dti_group']} | {row['credit_group']}**: {row['funded']:.1%} funding rate")

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
    st.header("🧪 A/B Testing Results")
    
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