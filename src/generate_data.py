import pandas as pd
import numpy as np
import random
from faker import Faker
import os
from datetime import date


fake = Faker()

np.random.seed(42)
random.seed(42)

n = 10000

data = {
    "applicant_id": [f"APP-{i:05d}" for i in range(1,n+1)],
    "application_date" : [fake.date_between(start_date='-180d', end_date=date.today()) for _ in range(n)],
    "credit_score" : np.random.randint(300, 851, size=n),
    "income" : np.random.randint(20000, 150001, size=n),
    "age" : np.random.randint(18,71,size=n),
    "employment_status" : np.random.choice(["Employed","Self-employed","Unemployed"],size=n,p=[0.7,0.2,0.1]),
    "loan_amount" : np.random.randint(1000,50001,size=n),
}

data["experiment_group"] = np.random.choice(["A","B"],size=n)

funnel_stages = ["Application Started","Documents Uploaded","Underwriting Review","Approved","Funded"]

funnel_stage_list = []
decision_outcome_list = []
funding_status_list = []
defaulted_list = []

for i in range(n):
    stage_prob = random.random()

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

        if data["experiment_group"][i] == "B":
            approved = np.random.choice([True,False],p=[0.85,0.15])
        else:
            approved = np.random.choice([True, False], p=[0.75,0.25])

        if approved:
            funnel_stage="Funded"
            decision_outcome="Approved"
            funding_status="Funded"

            if data["credit_score"][i]<600:
                defaulted = np.random.choice([0,1],p=[0.7,0.3])
            else:
                defaulted = np.random.choice([0,1],p=[0.9,0.1])
        else:
            funnel_stage = "Underwriting Review"
            decision_outcome = "Rejected"
            funding_status = "Not Funded"
            defaulted = 0
    funnel_stage_list.append(funnel_stage)
    decision_outcome_list.append(decision_outcome)
    funding_status_list.append(funding_status)
    defaulted_list.append(defaulted)

data["funnel_stage"] = funnel_stage_list
data["decision_outcome"] = decision_outcome_list
data["funding_status"] = funding_status_list
data["defaulted"] = defaulted_list

df = pd.DataFrame(data)
df.to_csv("./data/loan_funnel_data.csv",index=False)

print("✅ Data generation complete! 'loan_funnel_data.csv' created.")