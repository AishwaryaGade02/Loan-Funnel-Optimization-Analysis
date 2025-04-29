import pandas as pd
import sqlite3
import os
from statsmodels.stats.proportion import proportions_ztest

def load_experiment_data(db_path="data/loan_funnel.db"):
    conn = sqlite3.connect(db_path)
    query = """
        Select
        experiment_group,
        Sum(Case when decision_outcome = 'Approved' Then 1 else 0 end) as approvals,
        Sum(Case when funding_status = 'Funded' Then 1 else 0 end) as fundings,
        Sum(Case when defaulted = 1 Then 1 else 0 end) as defaults,
        Count(*) as total_applicants
        From loan_applications
        Where funnel_stage In ('Approved','Funded','Underwriting Review')
        Group By experiment_group
    """

    df = pd.read_sql(query,conn)
    conn.close()

    print("🔹 Experiment Group Summary:")
    print(df)
    return df

def run_ab_test_approval(df):
    successes = df["approvals"].values
    nobs = df["total_applicants"].values

    stat, pval = proportions_ztest(count=successes, nobs=nobs)
    print("\n🔹 A/B Test on Approval Rates:")
    print(f"Z-Statistic = {stat:.4f}, p-value = {pval:.4f}")

    if pval < 0.05:
        print("✅ Result: Statistically Significant Difference in Approval Rates")
    else:
        print("❌ Result: No Significant Difference in Approval Rates")

    return stat, pval 

def run_ab_test_default(df):
    successes =df["defaults"].values
    nobs = df["fundings"].values

    stat, pval = proportions_ztest(count=successes, nobs=nobs)
    print("\n🔹 A/B Test on Default Rates (Funded Loans Only):")
    print(f"Z-Statistic = {stat:.4f}, p-value = {pval:.4f}")
    if pval < 0.05:
        print("✅ Result: Statistically Significant Difference in Default Rates")

    else:
        print("❌ Result: No Significant Difference in Default Rates")

    return stat, pval
if __name__ == "__main__":
    df_experiment = load_experiment_data()
    run_ab_test_approval(df_experiment)
    run_ab_test_default(df_experiment)