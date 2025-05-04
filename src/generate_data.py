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

# Step 1: Base applicant data with more realistic distribution
# Credit score with more spread and lower average
credit_scores = np.random.normal(loc=650, scale=120, size=n)  # Lower mean, higher variance
credit_scores = np.clip(credit_scores, 300, 850).astype(int)

# Income with more realistic distribution
base_income = 15000 + (credit_scores - 300) * 100  # Less strong correlation
income = base_income + np.random.normal(0, 20000, n)
income = np.clip(income, 15000, 200000).astype(int)

# Age 
age = np.random.normal(loc=44, scale=12, size=n)
age = np.clip(age, 18, 70).astype(int)

# Loan amount with more variation
loan_amount = income * np.random.uniform(0.15, 0.6, n)  # Higher loan-to-income ratios
loan_amount = np.clip(loan_amount, 1000, 100000).astype(int)

# DTI with more realistic, problematic patterns
base_dti = 0.6 - (credit_scores - 300) / 800  # Higher base DTI
existing_debt = income * (base_dti + np.random.normal(0, 0.15, n))
existing_debt = np.clip(existing_debt, 0, income * 0.9)
dti_ratio = existing_debt / income
dti_ratio = np.clip(dti_ratio, 0.05, 0.9)  # Allow higher DTI ratios

# Base data dictionary
data = {
    "applicant_id": [f"APP-{i:05d}" for i in range(1, n+1)],
    "application_date": [fake.date_between(start_date='-180d', end_date=date.today()) for _ in range(n)],
    "credit_score": credit_scores,
    "income": income,
    "age": age,
    "employment_status": np.random.choice(["Employed", "Self-employed", "Unemployed"], size=n, p=[0.65, 0.25, 0.10]),
    "loan_amount": loan_amount,
    "dti_ratio": dti_ratio,
    "experiment_group": np.random.choice(["A", "B"], size=n)
}

# Step 2: Funnel stage simulation with more realistic rejection patterns
funnel_stage_list = []
decision_outcome_list = []
funding_status_list = []
defaulted_list = []
approved_date_list = []
funded_date_list = []
funded_amount_list = []

for i in range(n):
    app_date = data["application_date"][i]
    credit_score = data["credit_score"][i]
    income_val = data["income"][i]
    employment = data["employment_status"][i]
    loan_amt = data["loan_amount"][i]
    dti = data["dti_ratio"][i]
    exp_group = data["experiment_group"][i]
    
    # Stricter approval scoring
    approval_score = (
        (credit_score - 300) / 550 * 0.45 +  # Credit score weight: 45%
        (income_val / 200000) * 0.15 +       # Income weight: 15%
        (1 - dti) * 0.3 +                    # DTI weight: 30% (more important)
        (employment == "Employed") * 0.1     # Employment weight: 10%
    )
    
    # Penalties for high-risk factors
    if dti > 0.43:  # DTI above 43% (regulatory threshold)
        approval_score -= 0.15
    if credit_score < 620:  # Subprime credit
        approval_score -= 0.2
    if employment == "Unemployed":
        approval_score -= 0.25
    if loan_amt > 50000:  # Large loans
        approval_score -= 0.1
    
    # Add some random noise
    approval_score += np.random.normal(0, 0.05)
    
    approved_date = None
    funded_date = None
    funded_amount = None
    
    # Higher dropout rates at each stage
    completion_prob = np.random.random()
    
    if completion_prob < 0.08:  # 8% don't complete application
        funnel_stage = "Application Started"
        decision_outcome = "N/A"
        funding_status = "Not Funded"
        defaulted = 0
    else:
        # Document upload stage with more dropouts
        doc_prob = np.random.random()
        doc_threshold = 0.88 if employment == "Employed" else 0.75
        
        if doc_prob > doc_threshold:  # More dropouts at document stage
            funnel_stage = "Documents Uploaded"
            decision_outcome = "N/A" 
            funding_status = "Not Funded"
            defaulted = 0
        else:
            # Stricter approval thresholds
            if exp_group == "B":
                approval_threshold = 0.55  # Test group still stricter
            else:
                approval_threshold = 0.65  # Control group very strict
            
            if approval_score > approval_threshold:
                funnel_stage = "Approved"
                decision_outcome = "Approved"
                
                # More funding dropouts
                funding_prob = 0.7 + approval_score * 0.2  # Lower base probability
                
                if random.random() < funding_prob:
                    funnel_stage = "Funded"
                    funding_status = "Funded"
                    
                    # Time calculations remain the same
                    base_approval_days = 5 - approval_score * 3
                    approval_delay_days = int(np.clip(np.random.normal(loc=base_approval_days, scale=1), 1, 10))
                    approved_date = app_date + timedelta(days=approval_delay_days)
                    
                    funding_delay_days = int(np.clip(np.random.normal(loc=2, scale=1), 1, 5))
                    funded_date = approved_date + timedelta(days=funding_delay_days)
                    
                    # Funded amount
                    mean_funding = loan_amt * 0.95
                    std_funding = loan_amt * 0.05
                    funded_amount = np.random.normal(loc=mean_funding, scale=std_funding)
                    funded_amount = int(np.clip(funded_amount, loan_amt * 0.7, loan_amt))
                    
                    # Higher default risks
                    if credit_score < 580:
                        base_default_prob = 0.4
                    elif credit_score < 650:
                        base_default_prob = 0.25
                    elif credit_score < 720:
                        base_default_prob = 0.12
                    else:
                        base_default_prob = 0.05
                    
                    # DTI impact on default
                    default_prob = base_default_prob * (1 + dti * 1.5)
                    default_prob = min(default_prob, 0.6)
                    
                    defaulted = 1 if random.random() < default_prob else 0
                else:
                    funding_status = "Not Funded"
                    defaulted = 0
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
