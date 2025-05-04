import pandas as pd
import sqlite3
import os

def get_features_vs_approval(db_path="data/loan_funnel.db"):
    conn = sqlite3.connect(db_path)

    query = """
    Select 
        avg(income) as avg_income,
        cast(avg(age) as int) as avg_age,
        cast(avg(credit_score) as int) as avg_credit_score

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
    round(avg(Case when decision_outcome = 'Rejected' Then 1 else 0 end)*100,2) As rejection_rate,
    count(*) as applicant_count
    From loan_applications
    Where funnel_stage = "Underwriting Review" or funnel_stage = "Funded"
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
    round(avg(case when decision_outcome = 'Rejected' then 1 else 0 end) * 100,2) as rejection_rate,
    Count(*) as applicant_count
    From loan_applications
    Where funnel_stage = "Underwriting Review" or funnel_stage = "Funded"
    Group by income_band
    Order by income_band    
    """
    query_emp = """
    Select employment_status,
    round(avg(case when decision_outcome = 'Rejected' then 1 else 0 end) * 100,2) as rejection_rate,
    count(*) as applicant_count
    From loan_applications
    Where funnel_stage = "Underwriting Review" or funnel_stage = "Funded"
    Group by employment_status
    """

    query_loan_amo = """
    Select
    Case
        when loan_amount < 5000 then 'Very Small Loan'
        when loan_amount between 5000 and 10000 then 'Small Loan'
        when loan_amount between 10001 and 15000 then 'Medium Loan'
        when loan_amount between 15001 and 25000 then 'Large Loan'
        when loan_amount between 25001 and 35000 then 'Very Large Loan'
        else 'High-End Loan'
    End as loan_amount_band,
    round(avg(case when decision_outcome = 'Rejected' then 1 else 0 end) * 100,2) as rejection_rate,
    count(*) as applicant_count
    From loan_applications
    Where funnel_stage = "Underwriting Review" or funnel_stage = "Funded"
    Group by loan_amount_band
    
    """

    credit_df = pd.read_sql(query_credit,conn)
    income_df = pd.read_sql(query_income, conn)
    emp_df = pd.read_sql(query_emp, conn)
    loan_amo_df = pd.read_sql(query_loan_amo, conn)
    conn.close()

    print("\n🔹 Cohort Analysis by Credit Band:")
    print(credit_df)
    print("\n🔹 Cohort Analysis by Income Band:")
    print(income_df)
    print("\n Cohort Analysis by Employement Status:")
    print(emp_df)
    print("\n Cohort Analysis by Loan Amount:")
    print(loan_amo_df)
    return credit_df, income_df, emp_df



if __name__ == "__main__":
    get_features_vs_approval()
    cohort_analysis()
    