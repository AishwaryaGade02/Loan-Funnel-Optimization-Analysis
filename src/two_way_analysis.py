import sqlite3
import pandas as pd


def two_interaction(db_path="data/loan_funnel.db", group1=None, group2=None):
    """
    Perform two-way interaction analysis between any two grouping variables
    
    Parameters:
    - db_path: path to the database
    - group1: first grouping variable (e.g., 'age_group')
    - group2: second grouping variable (e.g., 'dti_group')
    
    If group1 and group2 are None, returns all possible two-way interactions
    """
    conn = sqlite3.connect(db_path)
    
    # Base query that creates all cohort data
    base_query = """
    WITH cohort_data AS (
        SELECT 
            applicant_id,
            CASE 
                when age between 18 and 25 then '18-25'
                when age between 26 and 35 then '26-35'
                when age between 36 and 45 then '36-45'
                when age between 46 and 55 then '46-55'
                when age between 56 and 65 then '56-65'
                else '65+'
            END as age_group,
            CASE 
                WHEN dti_ratio < 0.36 THEN 'Low DTI'
                WHEN dti_ratio BETWEEN 0.36 AND 0.50 THEN 'Medium DTI'
                ELSE 'High DTI'
            END as dti_group,
            CASE 
                when credit_score < 580 then 'Poor (<580)'
                when credit_score between 580 and 669 then 'Fair (580-669)'
                when credit_score between 670 and 739 then 'Good (670-739)'
                when credit_score between 740 and 799 then 'Very Good (740-799)'
                else 'Excellent (800+)'
            END as credit_group,
            CASE 
                when loan_amount < 5000 then 'Very Small Loan'
                when loan_amount between 5000 and 10000 then 'Small Loan'
                when loan_amount between 10001 and 15000 then 'Medium Loan'
                when loan_amount between 15001 and 25000 then 'Large Loan'
                when loan_amount between 25001 and 35000 then 'Very Large Loan'
                else 'High-End Loan'
            END as loan_amount_group,
            CASE 
                when income < 40000 then 'Low (<40k)'
                when income between 40000 and 80000 then 'Mid (40k-80k)'
                else 'High (80k+)'
            END as income_band,
            employment_status,
            CASE WHEN decision_outcome = 'Approved' THEN 1 ELSE 0 END as approved,
            CASE WHEN funding_status = 'Funded' THEN 1 ELSE 0 END as funded
        FROM loan_applications
    )
    """
    
    # If specific groups are provided, analyze just that pair
    if group1 and group2:
        query = base_query + f"""
        SELECT 
            {group1} as {group1},
            {group2} as {group2},
            COUNT(*) as total_applications,
            ROUND(AVG(approved) * 100, 2) as approval_rate,
            ROUND(AVG(funded) * 100, 2) as funding_rate,
            SUM(CASE WHEN approved = 1 THEN 1 ELSE 0 END) as approved_count,
            SUM(CASE WHEN funded = 1 THEN 1 ELSE 0 END) as funded_count
        FROM cohort_data
        GROUP BY {group1}, {group2}
        ORDER BY approval_rate DESC;
        """
        result = pd.read_sql(query, conn)
        conn.close()
        return result
    
    # If no specific groups provided, return all key two-way interactions
    else:
        interactions = {
            'age_group_vs_dti_group': ('age_group', 'dti_group'),
            'age_group_vs_credit_group': ('age_group', 'credit_group'),
            'age_group_vs_income_band':('age_group','income_band'),
            'age_group_vs_loan_amount_group':('age_group','loan_amount_group'),
            'age_group_vs_employment':('age_group','employment_status'),
            'dti_group_vs_credit_group': ('dti_group', 'credit_group'),
            'dti_group_vs_loan_amount_band':('dti_group','loan_amount_band'),
            'dti_group_vs_employment':('dti_group','employment_status'),
            'credit_group_vs_loan_amount_group': ('credit_group', 'loan_amount_group'),
            'credit_group_vs_emplyment_status':('credit_group','employment_status'),
            'income_band_vs_dti_group': ('income_band', 'dti_group'),
            'income_band_vs_credit_group': ('income_band', 'credit_group'),
            'income_band_vs_employment':('income_band','employment_status')
        }
        
        results = {}
        for interaction_name, (var1, var2) in interactions.items():
            query = base_query + f"""
            SELECT 
                {var1} as {var1},
                {var2} as {var2},
                COUNT(*) as total_applications,
                ROUND(AVG(approved) * 100, 2) as approval_rate,
                ROUND(AVG(funded) * 100, 2) as funding_rate,
                SUM(CASE WHEN approved = 1 THEN 1 ELSE 0 END) as approved_count,
                SUM(CASE WHEN funded = 1 THEN 1 ELSE 0 END) as funded_count
            FROM cohort_data
            GROUP BY {var1}, {var2}
            ORDER BY approval_rate DESC;
            """
            results[interaction_name] = pd.read_sql(query, conn)
        
        conn.close()
        return results

def visualize_interaction(interaction_df, var1_name, var2_name):
    """
    Create a heatmap visualization for two-way interaction
    Returns a plotly figure
    """
    import plotly.graph_objects as go
    
    # Pivot the data for heatmap
    pivot_data = interaction_df.pivot(
        index=var1_name, 
        columns=var2_name, 
        values='approval_rate'
    )
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='RdYlGn',
        text=[[f'{val:.1f}%' for val in row] for row in pivot_data.values],
        texttemplate='%{text}',
        textfont={"size": 12},
    ))
    
    fig.update_layout(
        title=f'Approval Rate: {var1_name.replace("_", " ").title()} vs {var2_name.replace("_", " ").title()}',
        xaxis_title=var2_name.replace("_", " ").title(),
        yaxis_title=var1_name.replace("_", " ").title()
    )
    
    return fig

def get_all_key_interactions(db_path="data/loan_funnel.db"):
    """
    Get all key two-way interactions in a formatted structure
    """
    # Define the key interactions you want to analyze
    interactions_to_analyze = [
        ('age_group', 'dti_group'),
        ('age_group','loan_amount_group'),
        ('age_group', 'credit_group'),
        ('age_group','income_band'),
        ('age_group','employment_status'),
        ('dti_group', 'credit_group'),
        ('dti_group','loan_amount_group'),
        ('dti_group','employment_status'),
        ('credit_group','income_band'),
        ('credit_group','employment_status'),
        ('credit_group', 'loan_amount_group'),
        ('income_band','employment_status'),
        ('loan_amount_group','income_band'),
        ('income_band', 'credit_group'),
        ('income_band', 'dti_group')
    ]
    
    results = {}
    
    for var1, var2 in interactions_to_analyze:
        interaction_df = two_interaction(db_path, var1, var2)
        results[f'{var1}_vs_{var2}'] = interaction_df
    
    return results

def create_interaction_summary(interaction_df, var1_name, var2_name):
    """
    Create a summary of key insights from the interaction data
    """
    # Find best and worst combinations
    best_combination = interaction_df.nlargest(1, 'approval_rate').iloc[0]
    worst_combination = interaction_df.nsmallest(1, 'approval_rate').iloc[0]
    
    # Find combinations with highest volume
    highest_volume = interaction_df.nlargest(1, 'total_applications').iloc[0]
    
    summary = {
        'best_combination': {
            f'{var1_name}': best_combination[var1_name],
            f'{var2_name}': best_combination[var2_name],
            'approval_rate': best_combination['approval_rate'],
            'total_applications': best_combination['total_applications']
        },
        'worst_combination': {
            f'{var1_name}': worst_combination[var1_name],
            f'{var2_name}': worst_combination[var2_name],
            'approval_rate': worst_combination['approval_rate'],
            'total_applications': worst_combination['total_applications']
        },
        'highest_volume': {
            f'{var1_name}': highest_volume[var1_name],
            f'{var2_name}': highest_volume[var2_name],
            'approval_rate': highest_volume['approval_rate'],
            'total_applications': highest_volume['total_applications']
        }
    }
    
    return summary