import pandas as pd
import numpy as np
import random
from faker import Faker
import os
from datetime import date, timedelta

# Setup
fake = Faker()
np.random.seed(42)
random.seed(42)

n = 10000

# Step 1: Base applicant data
data = {
    "applicant_id": [f"APP-{i:05d}" for i in range(1,n+1)],
    "application_date": [fake.date_between(start_date='-180d', end_date=date.today()) for _ in range(n)],
    "credit_score": np.clip(np.random.normal(loc=680, scale=50, size=n), 300, 850).astype(int),
    "income": np.clip(np.random.normal(loc=60000, scale=20000, size=n), 20000, 150000).astype(int),
    "age": np.clip(np.random.normal(loc=45, scale=10, size=n), 18, 70).astype(int),
    "employment_status": np.random.choice(["Employed", "Self-employed", "Unemployed"], size=n, p=[0.7, 0.2, 0.1]),
    "loan_amount": np.clip(np.random.normal(loc=15000, scale=7500, size=n), 1000, 50000).astype(int),
    "experiment_group": np.random.choice(["A", "B"], size=n)
}

# Step 2: Funnel stage simulation
funnel_stage_list = []
decision_outcome_list = []
funding_status_list = []
defaulted_list = []

approved_date_list = []
funded_date_list = []
funded_amount_list = []

for i in range(n):
    app_date = data["application_date"][i]
    stage_prob = random.random()

    approved_date = None
    funded_date = None
    funded_amount = None

    if stage_prob < 0.10:
        funnel_stage = "Application Started"
        decision_outcome = "N/A"
        funding_status = "Not Funded"
        defaulted = 0
    elif stage_prob < 0.30:
        funnel_stage = "Documents Uploaded"
        decision_outcome = "N/A"
        funding_status = "Not Funded"
        defaulted = 0
    elif stage_prob < 0.60:
        funnel_stage = "Underwriting Review"
        decision_outcome = "Rejected"
        funding_status = "Not Funded"
        defaulted = 0
    else:
        funnel_stage = "Approved"

        # A/B test logic for approval
        if data["experiment_group"][i] == "B":
            approved = np.random.choice([True, False], p=[0.85, 0.15])
        else:
            approved = np.random.choice([True, False], p=[0.75, 0.25])

        if approved:
            funnel_stage = "Funded"
            decision_outcome = "Approved"
            funding_status = "Funded"

            # Approved date: 1 to 5 days after application
            approval_delay_days = int(np.clip(np.random.normal(loc=6, scale=1), 1, 10))
            approved_date = app_date + timedelta(days=approval_delay_days)

            # Funded date: 1 to 3 days after approval
            
            funding_delay_days = int(np.clip(np.random.normal(loc=2, scale=1), 1, 5))
            funded_date = approved_date + timedelta(days=funding_delay_days)

            # Funded amount: up to the full loan amount
            # funded_amount = np.random.randint(int(data["loan_amount"][i] * 0.7), data["loan_amount"][i] + 1)
            mean_funding = data["loan_amount"][i] * 0.95
            std_funding = data["loan_amount"][i] * 0.05

            funded_amount = np.random.normal(loc=mean_funding, scale=std_funding)
            funded_amount = int(np.clip(funded_amount, data["loan_amount"][i] * 0.7, data["loan_amount"][i]))
            # Default risk
            if data["credit_score"][i] < 600:
                defaulted = np.random.choice([0, 1], p=[0.7, 0.3])
            else:
                defaulted = np.random.choice([0, 1], p=[0.9, 0.1])
        else:
            funnel_stage = "Underwriting Review"
            decision_outcome = "Rejected"
            funding_status = "Not Funded"
            defaulted = 0

    # Add to lists
    funnel_stage_list.append(funnel_stage)
    decision_outcome_list.append(decision_outcome)
    funding_status_list.append(funding_status)
    defaulted_list.append(defaulted)

    approved_date_list.append(approved_date)
    funded_date_list.append(funded_date)
    funded_amount_list.append(funded_amount)

# Step 3: Add generated fields to data
data["funnel_stage"] = funnel_stage_list
data["decision_outcome"] = decision_outcome_list
data["funding_status"] = funding_status_list
data["defaulted"] = defaulted_list

data["approved_date"] = approved_date_list
data["funded_date"] = funded_date_list
data["funded_amount"] = funded_amount_list

# Step 4: Save as DataFrame
df = pd.DataFrame(data)
os.makedirs("data", exist_ok=True)
df.to_csv("./data/loan_funnel_data.csv", index=False)

print("✅ Enhanced data generation complete! 'loan_funnel_data.csv' created.")
