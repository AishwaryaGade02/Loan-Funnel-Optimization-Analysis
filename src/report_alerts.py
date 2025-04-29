import sqlite3
import pandas as pd
import datetime

APPROVAL_RATE_THRESHOLD = 0.70
FUNDING_RATE_THRESHOLD = 0.60

def get_current_metrics(db_path="data/loan_funnel.db"):
    conn = sqlite3.connect(db_path)

    query = """Select
        strftime('%Y-%m-%d', application_date) as date,
        Sum(Case when decision_outcome = 'Approved' Then 1 else 0 end) * 1.0/count(*) as approval_rate,
        Sum(Case when funding_status = 'Funded' Then 1 else 0 end)*1.0/count(*) As funding_rate
        From loan_applications
        Where funnel_stage In ('Approved','Funded','Underwriting Review')
        Group By date
        Order By Date DESC
        Limit 1"""
    
    df = pd.read_sql(query, conn)
    conn.close()

    if df.empty:
        print("⚠️ No recent application data found.")
        return None
    
    print("🔹 Latest Daily Metrics:")
    print(df)
    return df.iloc[0]

def check_alerts(metrics):
    alerts = []

    if metrics['approval_rate']<APPROVAL_RATE_THRESHOLD:
        alerts.append(f"⚠️ ALERT: Approval rate dropped to {metrics['approval_rate']:.2%}")
    if metrics['funding_rate']<FUNDING_RATE_THRESHOLD:
        alerts.append(f"⚠️ ALERT: Funding rate dropped to {metrics['funding_rate']:.2%}")

    if not alerts:
        print("✅ All funnel metrics are within acceptable thresholds.")

    else:
        print("\n🚨 ALERTS:")
        for alert in alerts:
            print(alert)

    return alerts

def save_alerts(alerts, output_path="data/alerts_log.txt"):
    if not alerts:
        return 
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(output_path, "a", encoding="utf-8") as f:
        for alert in alerts:
            f.write(f"[{timestamp}] {alert}\n")
    print(f"✅ Alerts logged to {output_path}")

if __name__ == "__main__":
    metrics = get_current_metrics()
    if metrics is not None:
        alerts = check_alerts(metrics)
        save_alerts(alerts)    