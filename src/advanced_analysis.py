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
    round(avg(Case when decision_outcome = 'Approved' Then 1 else 0 end)*100,2) As approval_rate,
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
    round(avg(case when decision_outcome = 'Approved' then 1 else 0 end) * 100,2) as approval_rate,
    Count(*) as applicant_count
    From loan_applications
    Where funnel_stage = "Underwriting Review" or funnel_stage = "Funded"
    Group by income_band
    Order by income_band    
    """
    query_emp = """
    Select employment_status,
    round(avg(case when decision_outcome = 'Approved' then 1 else 0 end) * 100,2) as approval_rate,
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
    round(avg(case when decision_outcome = 'Approved' then 1 else 0 end) * 100,2) as approval_rate,
    count(*) as applicant_count
    From loan_applications
    Where funnel_stage = "Underwriting Review" or funnel_stage = "Funded"
    Group by loan_amount_band
    
    """
    query_age="""
    Select 
    Case
        when age between 18 and 25 then "18-25"
        when age between 26 and 35 then "26-35"
        when age between 36 and 45 then "36-45"
        when age between 46 and 55 then "46-55"
        when age between 56 and 65 then "56-65"
        else "65+"
    End as Age_band,
    round(avg(case when decision_outcome = 'Approved' then 1 else 0 end) * 100,2) as approval_rate,
    count(*) as applicant_count
    From loan_applications
    Where funnel_stage = "Underwriting Review" or funnel_stage = "Funded"
    Group by Age_band
    """


    credit_df = pd.read_sql(query_credit,conn)
    income_df = pd.read_sql(query_income, conn)
    emp_df = pd.read_sql(query_emp, conn)
    loan_amo_df = pd.read_sql(query_loan_amo, conn)
    age_df = pd.read_sql(query_age, conn)
    conn.close()

    print("\n🔹 Cohort Analysis by Credit Band:")
    print(credit_df)
    print("\n🔹 Cohort Analysis by Income Band:")
    print(income_df)
    print("\n Cohort Analysis by Employement Status:")
    print(emp_df)
    print("\n Cohort Analysis by Loan Amount:")
    print(loan_amo_df)
    print("\n Cohort Analysis by Age:")
    print(age_df)
    return credit_df, income_df, emp_df, loan_amo_df, age_df

def two_interaction(db_path="data/loan_funnel.db"):
    conn = sqlite3.connect(db_path)
    query = """-- Create cohorts with multiple dimensions
        WITH cohort_data AS (
        SELECT 
            applicant_id,
            CASE 
                when age between 18 and 25 then "18-25"
                when age between 26 and 35 then "26-35"
                when age between 36 and 45 then "36-45"
                when age between 46 and 55 then "46-55"
                when age between 56 and 65 then "56-65"
                else "65+"
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
            Case 
                when income < 40000 then 'Low (<40k)'
                when income between 40000 and 80000 then 'Mid (40k-80k)'
                else 'High (80k+)'
            End as income_band
            CASE WHEN decision_outcome = 'Approved' THEN 1 ELSE 0 END as approved,
            CASE WHEN funding_status = 'Funded' THEN 1 ELSE 0 END as funded
        FROM loan_applications
        )

        SELECT age_group, dti_group,
        COUNT(*) as total_applications,
        round(AVG(approved),2) as approval_rate,
        round(AVG(funded),2) as funding_rate,
        SUM(CASE WHEN approved = 1 THEN 1 ELSE 0 END) as approved_count,
        SUM(CASE WHEN funded = 1 THEN 1 ELSE 0 END) as funded_count
        FROM cohort_data
        GROUP BY age_group, dti_group
        ORDER BY approval_rate DESC;"""
    
    two_interaction = pd.read_sql(query,conn)
    print(two_interaction)
    return two_interaction


def risk_metric(db_path="data/loan_funnel.db"):
    conn = sqlite3.connect(db_path)
    query="""
    
    WITH risk_segments AS (
    SELECT 
    CASE 
      WHEN credit_score < 620 THEN 'Poor Credit'
      WHEN credit_score < 680 THEN 'Fair Credit'
      WHEN credit_score < 740 THEN 'Good Credit'
      ELSE 'Excellent Credit'
    END as credit_tier,
    CASE 
      WHEN dti_ratio < 0.30 THEN 'Low DTI'
      WHEN dti_ratio < 0.40 THEN 'Medium DTI'
      WHEN dti_ratio < 0.50 THEN 'High DTI'
      ELSE '4_Very High DTI'
    END as dti_tier,
    CASE WHEN decision_outcome = 'Approved' THEN 1 ELSE 0 END as approved
    FROM loan_applications
    )
    SELECT credit_tier, dti_tier,
    COUNT(*) as applications, round(AVG(approved)*100,2) as approval_rate,
    CASE 
        WHEN AVG(approved) >= 0.7 THEN 'Low Risk'
        WHEN AVG(approved) >= 0.4 THEN 'Medium Risk'
        WHEN AVG(approved) >= 0.2 THEN 'High Risk'
        ELSE 'Very High Risk'
    END as risk_category
    FROM risk_segments
    GROUP BY credit_tier, dti_tier
    ORDER BY credit_tier, dti_tier;
    """
    risk_metric_df = pd.read_sql(query,conn)
    print(risk_metric_df)
    return risk_metric_df

def interaction_analysis(db_path="data/loan_funnel.db"):
    conn = sqlite3.connect(db_path)
    query="""
    -- Analyze complex interactions with statistical significance (SQLite compatible)
WITH cohort_data AS (
  SELECT 
    *,
    CASE 
                when age between 18 and 25 then "18-25"
                when age between 26 and 35 then "26-35"
                when age between 36 and 45 then "36-45"
                when age between 46 and 55 then "46-55"
                when age between 56 and 65 then "56-65"
                else "65+"
            END as age_group,
    CASE 
      WHEN dti_ratio < 0.30 THEN 'Low DTI'
      WHEN dti_ratio < 0.40 THEN 'Medium DTI'
      WHEN dti_ratio < 0.50 THEN 'High DTI'
      ELSE 'Very High DTI'
    END as dti_group,
    CASE 
      WHEN credit_score < 620 THEN 'Poor Credit'
      WHEN credit_score < 680 THEN 'Fair Credit'
      WHEN credit_score < 740 THEN 'Good Credit'
      ELSE 'Excellent Credit'
    END as credit_group,
    CASE 
        WHEN employment_status = 'Employed' THEN 'Employed'
        When employment_status = 'Self-employed' Then 'Self-employed'
        ELSE 'Not_Employed' END as emp_group,
    CASE WHEN decision_outcome = 'Approved' THEN 1 ELSE 0 END as approved
  FROM loan_applications
),
interaction_analysis AS (
  SELECT 
    age_group,
    dti_group,
    credit_group,
    emp_group,
    COUNT(*) as n,
    AVG(approved) as approval_rate,
    -- Calculate standard deviation manually for SQLite
    SQRT(AVG(approved * approved) - AVG(approved) * AVG(approved)) as approval_stddev,
    -- Calculate confidence intervals
    AVG(approved) - 1.96 * SQRT(AVG(approved * approved) - AVG(approved) * AVG(approved)) / SQRT(COUNT(*)) as lower_ci,
    AVG(approved) + 1.96 * SQRT(AVG(approved * approved) - AVG(approved) * AVG(approved)) / SQRT(COUNT(*)) as upper_ci
  FROM cohort_data
  GROUP BY age_group, dti_group, credit_group, emp_group
  HAVING COUNT(*) >= 20
)
SELECT 
  *,
  CASE 
    WHEN approval_rate > 0.5 AND lower_ci > 0.4 THEN 'High Approval'
    WHEN approval_rate < 0.2 AND upper_ci < 0.3 THEN 'High Risk'
    ELSE 'Normal'
  END as segment_classification
FROM interaction_analysis
ORDER BY approval_rate DESC;"""

    interaction_analysis_df = pd.read_sql(query,conn)
    print(interaction_analysis_df)
    return interaction_analysis_df



if __name__ == "__main__":
    get_features_vs_approval()
    cohort_analysis()
    two_interaction()
    risk_metric()
    interaction_analysis()