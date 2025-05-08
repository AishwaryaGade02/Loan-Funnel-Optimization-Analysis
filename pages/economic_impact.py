import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import os
import sys

from src.economic_impact import (
    run_economic_impact_analysis, 
    get_priority_cohorts, 
    create_cohort_labels
)

def show_economic_impact(DB_PATH):
    if os.path.exists(DB_PATH):
        st.header("💰 Economic Impact Analysis")
        
        # Run economic impact analysis
        loan_data = pd.read_csv('./data/loan_funnel_data.csv')
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
        #st.subheader("Economic Impact Visualizations")
        
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
            #st.subheader("Stage-wise Lost Revenue")
            
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
                xaxis_tickangle=0
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

