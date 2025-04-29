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

def get_stage_conversion_rates(db_path="data/loan_funnel.db"):
    conn = sqlite3.connect(db_path)
    query = """
        Select funnel_stage,
        COUNT(*) as applicants
        From loan_applications
        Group By funnel_stage
        Order By applicants DESC
    """
    df = pd.read_sql(query,conn)
    conn.close()

    total_applicants = df['applicants'].sum()
    df['conversion_rate'] = df['applicants']/total_applicants * 100
    print("🔹 Funnel Stage Conversion Rates:")
    print(df)
    return df

def get_approval_funding_rates(db_path="data/loan_funnel.db"):
    conn = sqlite3.connect(db_path)
    query = """
    Select
     sum(case when decision_outcome = 'Approved' then 1 else 0 end)*1.0/count(*) as approval_rate,
     sum(case when funding_status = 'Funded' then 1 else 0 end) * 1.0/ count(*) as funding_rate
    from loan_applications
    
    """

    df = pd.read_sql(query, conn)
    conn.close()

    print("🔹 Approval and Funding Rates:")
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
    get_stage_conversion_rates()
    get_approval_funding_rates()
    get_weekly_trend()