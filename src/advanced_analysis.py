import pandas as pd
import sqlite3
import os

def get_features_vs_approval(db_path="data/loan_funnel.db"):
    conn = sqlite3.connect(db_path)

    query = """
    Select 
        avg(income) as avg_income,
        avg(age) as avg_age,
        avg(credit_score) as avg_credit_score,
        sum(case when decision_outcome='Approved' Then 1 else 0 end) * 1.0/ Count(*) as approval_rate

    From loan_applications
    Where funnel_stage In('Approved','Funded')

    """
    df = pd.read_sql(query,conn)
    conn.close()

    print("🔹 Feature Averages and Overall Approval Rate:")
    print(df)
    return df

def cohort_analysis(db_path="data/loan_funnel.db"):
    conn = sqlite3.connect(db_path)

    query_credit = """
    Select 
    Case
        when credit_score < 580 then 'Poor (<580)'
        when credit_score between 580 and 669 then 'Fair (580-669)'
        when credit_score between 670 and 739 then 'Good (670-739)'
        when credit_score between 740 and 799 then 'Very Good (740-799)'
        Else 'Excellent (800+)'
    End As credit_band,
    Sum(Case when decision_outcome = 'Approved' Then 1 else 0 end)*1.0/count(*) As approval_rate,
    count(*) as applicant_count
    From loan_applications
    Group By credit_band
    Order By credit_band
    """
    query_income = """
    Select 
    Case 
        when income < 40000 then 'Low (<40k)'
        when income between 40000 and 80000 then 'Mid (40k-80k)'
        else 'High (80k+)'
    End as income_band,
    Sum(case when decision_outcome = 'Approved' then 1 else 0 end) * 1.0/count(*) as approval_rate,
    Count(*) as applicant_count
    From loan_applications
    Group by income_band
    Order by income_band    
    """

    credit_df = pd.read_sql(query_credit,conn)
    income_df = pd.read_sql(query_income, conn)

    conn.close()

    print("\n🔹 Cohort Analysis by Credit Band:")
    print(credit_df)
    print("\n🔹 Cohort Analysis by Income Band:")
    print(income_df)

    return credit_df, income_df

def dropoff_analysis(db_path="data/loan_funnel.db"):
    conn = sqlite3.connect(db_path)

    query = """Select funnel_stage,
    count(*) as count_stage
    From loan_applications
    Group By funnel_stage
    Order By count_stage DESC"""

    df = pd.read_sql(query,conn)
    conn.close()

    total = df['count_stage'].sum()
    df['percentage'] = df['count_stage']/total * 100

    print("\n🔹 Drop-off Analysis by Funnel Stage:")
    print(df)
    return df

if __name__ == "__main__":
    get_features_vs_approval()
    cohort_analysis()
    dropoff_analysis()