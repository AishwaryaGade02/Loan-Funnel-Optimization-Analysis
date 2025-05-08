import pandas as pd
import numpy as np

def prepare_data(df):
    """Prepare data by creating cohort groups"""
    # Create cohort groups
    df['age_group'] = pd.cut(
        df['age'],
        bins=[17, 25, 35, 45, 55, 65, float('inf')],
        labels=['18-25', '26-35', '36-45', '46-55', '56-65', '65+']
    )

    df['dti_group'] = pd.cut(
        df['dti_ratio'],
        bins=[-float('inf'), 0.36, 0.50, float('inf')],
        labels=['Low DTI', 'Medium DTI', 'High DTI']
    )

    df['credit_group'] = pd.cut(
        df['credit_score'],
        bins=[-float('inf'), 580, 669, 739, 799, float('inf')],
        labels=['Poor (<580)', 'Fair (580-669)', 'Good (670-739)', 'Very Good (740-799)', 'Excellent (800+)']
    )
    
    return df

def calculate_conversion_improvement(row):
    """Calculate the value of improving conversion rates"""
    # Assume different improvement rates for different stages
    improvements = {
        'application_started': 0.1,  # 10% improvement possible
        'documents_uploaded': 0.15,   # 15% improvement possible
        'underwriting_review': 0.2,   # 20% improvement possible
        'approved': 0.25              # 25% improvement possible
    }
    
    total_value = 0
    for stage, improvement in improvements.items():
        lost_key = f'lost_at_{stage}'
        if lost_key in row:
            total_value += row[lost_key] * improvement * 0.05  # 5% profit margin
    
    return total_value

def calculate_economic_impact(df, profit_margin=0.05):
    """Calculate economic impact by cohort and stage"""
    
    # Group by cohort and funnel stage
    cohort_stage = df.groupby(['age_group', 'dti_group', 'credit_group', 'funnel_stage']).agg({
        'loan_amount': ['count', 'sum', 'mean'],
        'funded_amount': 'sum'
    }).reset_index()
    
    # Flatten column names
    cohort_stage.columns = ['age_group', 'dti_group', 'credit_group', 'funnel_stage', 
                           'count', 'total_loan_amount', 'avg_loan_amount', 'total_funded_amount']
    
    # Calculate lost revenue at each stage
    economic_impact = []
    
    for (age, dti, credit), group in cohort_stage.groupby(['age_group', 'dti_group', 'credit_group']):
        cohort_data = {
            'age_group': age,
            'dti_group': dti,
            'credit_group': credit,
            'total_applications': group['count'].sum()
        }
        
        # Calculate losses at each stage
        stages = ['Application Started', 'Documents Uploaded', 'Underwriting Review', 'Approved']
        
        for stage in stages:
            stage_data = group[group['funnel_stage'] == stage]
            if not stage_data.empty:
                lost_amount = stage_data['total_loan_amount'].iloc[0]
                lost_revenue = lost_amount * profit_margin
                cohort_data[f'lost_at_{stage.lower().replace(" ", "_")}'] = lost_amount
                cohort_data[f'lost_revenue_{stage.lower().replace(" ", "_")}'] = lost_revenue
            else:
                cohort_data[f'lost_at_{stage.lower().replace(" ", "_")}'] = 0
                cohort_data[f'lost_revenue_{stage.lower().replace(" ", "_")}'] = 0
        
        # Calculate total losses and potential improvements
        total_lost = sum(cohort_data[f'lost_at_{stage.lower().replace(" ", "_")}'] 
                        for stage in stages)
        total_lost_revenue = total_lost * profit_margin
        
        cohort_data['total_lost_revenue'] = total_lost_revenue
        cohort_data['improvement_potential'] = total_lost_revenue * 0.2  # Assume 20% improvement possible
        
        # Calculate ROI (potential gain / cost)
        cost_per_application = 50  # Example cost
        total_cost = cohort_data['total_applications'] * cost_per_application
        cohort_data['roi_ratio'] = cohort_data['improvement_potential'] / total_cost if total_cost > 0 else 0
        
        # Priority score (combines potential value and volume)
        cohort_data['priority_score'] = (cohort_data['improvement_potential'] * 
                                       cohort_data['total_applications'] / 1000)
        
        economic_impact.append(cohort_data)
    
    impact_df = pd.DataFrame(economic_impact)
    
    # Add conversion improvement analysis
    impact_df['conversion_improvement_value'] = impact_df.apply(
        lambda row: calculate_conversion_improvement(row), axis=1
    )
    
    return impact_df.sort_values('priority_score', ascending=False)

def run_economic_impact_analysis(df):
    """Main function to run economic impact analysis"""
    # Prepare the data
    df_prepared = prepare_data(df.copy())
    
    # Calculate economic impact
    economic_impact_df = calculate_economic_impact(df_prepared)
    
    # Return results
    return economic_impact_df

def get_priority_cohorts(impact_df, top_n=10):
    """Get top N priority cohorts"""
    return impact_df.head(top_n).copy()

def create_cohort_labels(impact_df):
    """Create readable cohort labels"""
    impact_df['cohort'] = impact_df['age_group'] + ' | ' + impact_df['dti_group'] + ' | ' + impact_df['credit_group']
    return impact_df