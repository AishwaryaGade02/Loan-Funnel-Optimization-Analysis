import pandas as pd
import sqlite3
import os

def load_data_to_sqlite(csv_path="data/loan_funnel_data.csv",db_path="data/loan_funnel.db"):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"{csv_path} not found. Please generate the data first.")
    
    df = pd.read_csv(csv_path)
    os.makedirs(os.path.dirname(db_path),exist_ok=True)

    conn = sqlite3.connect(db_path)
    df.to_sql('loan_applications', conn, if_exists='replace',index=False)
    conn.close()
    print(f"✅ Data loaded into {db_path}")

def get_total_applications(db_path="data/loan_funnel.db"):
    conn = sqlite3.connect(db_path)
    query = """
    Select count(*) as total_applications
    From loan_applications

    """
    df = pd.read_sql(query,conn)
    conn.close()
    print("Total Applications: ")
    print(df)
    return df

def get_total_applicants_passing_each_stage(db_path="data/loan_funnel.db"):
    conn = sqlite3.connect(db_path)
    query = """
    with cte as(
        Select funnel_stage,
        COUNT(*) as applicants
        From loan_applications
        Group By funnel_stage)
    Select funnel_stage, sum(applicants) over
        (Order By Case when funnel_stage is "Application Started" then 1
                    when funnel_stage is "Documents Uploaded" then 2
                    when funnel_stage is "Underwriting Review" then 3
                    when funnel_stage is "Approved" then 4
                    when funnel_stage is "Funded" then 5
                    end
                    rows between current row and unbounded following) as Applicants_passing
    From cte
    """
    df = pd.read_sql(query,conn)
    conn.close()

    # total_applicants = df['applicants'].sum()
    # df['conversion_rate'] = df['applicants']/total_applicants * 100
    print("🔹 Funnel Stage Conversion Rates:")
    print(df)
    return df

def conversion_rate_at_each_stage():
    stage_counts = get_total_applicants_passing_each_stage().reset_index(drop=True)
    total_applicants = stage_counts[stage_counts['funnel_stage'] == 'Application Started']["Applicants_passing"].iloc[0]
    coversion_row = []
    for i in range(len(stage_counts)-1):
        from_stage = stage_counts.loc[i, "funnel_stage"]
        to_stage = stage_counts.loc[i + 1, "funnel_stage"]
        from_count = stage_counts.loc[i, "Applicants_passing"]
        to_count = stage_counts.loc[i + 1, "Applicants_passing"]
        conversion_rate = round(((to_count) / from_count) * 100, 2)

        coversion_row.append({
        "From Stage": from_stage,
        "To Stage": to_stage,
        "Conversion Rate (%)": conversion_rate
    })
    conversion_df = pd.DataFrame(coversion_row)
    print(conversion_df)
    return conversion_df

def dropout_rate_at_each_stage():
    
    stage_counts = get_total_applicants_passing_each_stage().reset_index(drop=True)
    dropout_rows = []


    for i in range(len(stage_counts ) - 1):
        from_stage = stage_counts.loc[i, "funnel_stage"]
        to_stage = stage_counts.loc[i + 1, "funnel_stage"]
        from_count = stage_counts.loc[i, "Applicants_passing"]
        to_count = stage_counts.loc[i + 1, "Applicants_passing"]

        dropout_rate = round(((from_count - to_count) / from_count) * 100, 2)

        dropout_rows.append({
        "From Stage": from_stage,
        "To Stage": to_stage,
        "Dropout Rate (%)": dropout_rate
    })


    dropout_df = pd.DataFrame(dropout_rows)
    print(dropout_df)
    return dropout_df


def get_approval_denial_dropout_rates(db_path="data/loan_funnel.db"):
    conn = sqlite3.connect(db_path)
    query = """
    Select
     
     avg(case when decision_outcome = 'Approved' then 1 else 0 end)*100 as Approval_rate,
     avg(case when decision_outcome = 'Rejected' then 1 else 0 end)*100 as Rejection_rate,
     avg(case when decision_outcome is null then 1 else 0 end)*100 as Dropout_rate
     
    from loan_applications
    
    """

    df = pd.read_sql(query, conn)
    conn.close()

    print("🔹 Approval, Rejected and Dropout Rates:")
    print(df)
    return df

def average_time_for_loan_approval(db_path="data/loan_funnel.db"):
    conn = sqlite3.connect(db_path)
    query = """
    Select round(avg(julianday(approved_date)-julianday(application_date))) as Average_approval_time
    From loan_applications
    Where decision_outcome = 'Approved'

    """
    df = pd.read_sql(query, conn)
    conn.close()
    print(df)
    return df

def get_pull_through_ratio(db_path="data/loan_funnel.db"):
    conn=sqlite3.connect(db_path)
    query="""
    Select strftime('%Y-%m',application_date) as application_month,
    round(avg(case when funding_status='Funded' then 1.0 else 0.0 end)*100) as Pull_through_rate
    From loan_applications
    Group by application_month
    Order by application_month
    """
    df = pd.read_sql(query,conn)
    conn.close()
    print(df)
    return df

def get_decision_to_close_time(db_path="data/loan_funnel.db"):
    conn=sqlite3.connect(db_path)
    query="""
    Select round(avg(julianday(funded_date)-julianday(approved_date))) as Average_decision_close_date
    From loan_applications
    Where decision_outcome = 'Approved'
    """
    df=pd.read_sql(query,conn)
    conn.close()
    print(df)
    return df

def get_weekly_trend(db_path="data/loan_funnel.db"):
    conn = sqlite3.connect(db_path)
    query = """
    Select 
        strftime('%Y-%W', application_date) As week,
        count(*) As applications
    From loan_applications
    Group By week
    Order By week
    """ 
    df = pd.read_sql(query,conn)
    conn.close()

    print("🔹 Weekly Application Volume Trend:")
    print(df)
    return df

if __name__ == "__main__":
    load_data_to_sqlite()
    get_total_applications()
    get_total_applicants_passing_each_stage()
    get_approval_denial_dropout_rates()
    average_time_for_loan_approval()
    get_pull_through_ratio()
    get_decision_to_close_time()
    get_weekly_trend()
    conversion_rate_at_each_stage()
    dropout_rate_at_each_stage()