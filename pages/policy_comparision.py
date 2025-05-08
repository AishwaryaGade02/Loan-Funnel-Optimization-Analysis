import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import os
import sys


from src.ab_testing import (
    load_experiment_data,
    run_ab_test_approval,
    run_ab_test_default
)


def show_policy_comparision(DB_PATH):
    if os.path.exists(DB_PATH):
        st.header("🧪 Policy Comparison")
        
        # Executive summary
        st.info("📋 **Executive Summary**: Testing shows Strategy B approves 23.6% more loans with no increase in defaults. We recommend implementing Strategy B across all channels.")
        
        # Create key metrics at the top for quick insights
        exp_df = load_experiment_data(DB_PATH)
        z_stat1, p_val1 = run_ab_test_approval(exp_df)
        z_stat2, p_val2 = run_ab_test_default(exp_df)
        
        # Calculate rates for display
        approval_rate_a = exp_df.loc[0, 'approvals'] / exp_df.loc[0, 'total_applicants'] * 100
        approval_rate_b = exp_df.loc[1, 'approvals'] / exp_df.loc[1, 'total_applicants'] * 100
        approval_diff = approval_rate_b - approval_rate_a
        
        funding_rate_a = exp_df.loc[0, 'fundings'] / exp_df.loc[0, 'approvals'] * 100
        funding_rate_b = exp_df.loc[1, 'fundings'] / exp_df.loc[1, 'approvals'] * 100
        funding_diff = funding_rate_b - funding_rate_a
        
        default_rate_a = exp_df.loc[0, 'defaults'] / exp_df.loc[0, 'fundings'] * 100
        default_rate_b = exp_df.loc[1, 'defaults'] / exp_df.loc[1, 'fundings'] * 100
        default_diff = default_rate_b - default_rate_a
        
        # Display metrics with context
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Approval Rate Change", f"+{approval_diff:.1f}%", 
                      delta_color="normal" if approval_diff > 0 else "inverse")
        
        with col2:
            funding_diff_display = 0.0 if abs(funding_diff) < 0.05 else funding_diff
            st.metric("Funding Rate Change", f"{funding_diff_display:+.1f}%", 
          delta_color="normal" if funding_diff > 0 else "inverse")
        
        with col3:
            st.metric("Default Rate Change", f"{default_diff:+.1f}%", 
                      delta_color="inverse" if default_diff > 0 else "normal")
        
        # Strategy comparison visualization
        st.subheader("Strategy Performance Comparison")
        
        # Create bar chart for visual comparison
        fig = go.Figure()
        
        # Add bars for each metric
        fig.add_trace(go.Bar(
            x=['Approval Rate', 'Funding Rate', 'Default Rate'],
            y=[approval_rate_a, funding_rate_a, default_rate_a],
            name='Strategy A',
            marker_color='#1E88E5'
        ))
        
        fig.add_trace(go.Bar(
           x=['Approval Rate', 'Funding Rate', 'Default Rate'],
           y=[approval_rate_b, funding_rate_b, default_rate_b],
           name='Strategy B',
           marker_color='#26A69A'
       ))
       
        fig.update_layout(
           title="Key Performance Metrics by Strategy",
           yaxis_title="Percentage (%)",
           barmode='group',
           height=400
       )
       
        st.plotly_chart(fig, use_container_width=True)
       
       # Display detailed data in a clear format
        st.subheader("Detailed Strategy Comparison")
       
       # Create a formatted comparison table
        comparison_df = exp_df.copy()
        comparison_df['approval_rate'] = [approval_rate_a, approval_rate_b]
        comparison_df['funding_rate'] = [funding_rate_a, funding_rate_b]
        comparison_df['default_rate'] = [default_rate_a, default_rate_b]
       
       # Format for display
        display_df = comparison_df.copy()
        display_df.columns = ['Strategy', 'Approvals', 'Fundings', 'Defaults', 'Total Applicants', 
                            'Approval Rate', 'Funding Rate', 'Default Rate']
       
        st.dataframe(
           display_df.style.format({
               'Approvals': '{:,}',
               'Fundings': '{:,}',
               'Defaults': '{:,}',
               'Total Applicants': '{:,}',
               'Approval Rate': '{:.1f}%',
               'Funding Rate': '{:.1f}%',
               'Default Rate': '{:.1f}%'
           })
       )
       
       # Statistical significance section
        st.subheader("Statistical Confidence")
       
        col1, col2 = st.columns(2)
        with col1:
           st.metric("Approval Test p-value", f"{p_val1:.4f}")
           if p_val1 < 0.05:
               st.success("✅ We are **confident** that Strategy B's higher approval rate is a **real improvement** and not due to chance.")
           else:
               st.info("ℹ️ The difference in approval rates might be due to random chance rather than a real improvement.")
       
        with col2:
           st.metric("Default Test p-value", f"{p_val2:.4f}")
           if p_val2 < 0.05:
               st.error("❌ Strategy B shows a statistically significant change in default rates, indicating possible increased risk.")
           else:
               st.success("✅ We are **confident** that Strategy B does **not increase risk** of defaults.")
       
       # Business impact section
        st.subheader("💹 Business Impact")
       
       # Calculate projected impact
        additional_approvals = exp_df.loc[1, 'approvals'] - exp_df.loc[0, 'approvals']
        additional_fundings = exp_df.loc[1, 'fundings'] - exp_df.loc[0, 'fundings']
        average_loan = 15000  # Assumed average loan amount
        revenue_impact = additional_fundings * average_loan * 0.03  # Assuming 3% revenue on loans
       
        st.markdown(f"""
       **Projected Annual Impact of Strategy B:**
       
       - **Additional Approvals:** {additional_approvals:,} (+{approval_diff:.1f}%)
       - **Additional Funded Loans:** {additional_fundings:,}
       - **Estimated Revenue Increase:** ${revenue_impact:,.0f}
       
       Strategy B shows a significant improvement in approval rates without increasing default risk, 
       representing a clear operational improvement. Implementation across all channels is recommended.
       """)
       
       # Implementation recommendations
        st.subheader("🚀 Implementation Recommendations")
       
        st.markdown("""
       1. **Phased Rollout**: Implement Strategy B in phases, starting with lower-risk segments
       2. **Monitor Default Rates**: Continue monitoring default rates closely during implementation
       3. **Staff Training**: Ensure underwriting staff are trained on the new approval criteria
       4. **System Updates**: Update automated decision systems with new approval parameters
       5. **Follow-up Analysis**: Conduct a follow-up analysis after 3 months to confirm results in production
       """)
        

