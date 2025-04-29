# 📊 Loan Funnel Optimization & A/B Testing Dashboard

This is a full end-to-end data analytics project simulating a **loan application funnel** at a fintech or lending company. It includes:

✅ Funnel performance monitoring  
✅ Automated KPI reporting and alerting  
✅ Advanced data insights and cohort analysis  
✅ A/B testing to evaluate underwriting strategy changes  
✅ A deployed interactive dashboard (via Streamlit)

---

## 🚀 Project Overview

### 🎯 Objective
To simulate, analyze, and optimize the loan funnel journey — from application to funding — and identify areas of improvement using metrics, insights, and A/B experimentation.

---

## 📦 Features

| Category | Description |
|:--|:--|
| 🔁 **Synthetic Data Generation** | Realistic data for 10,000 applicants with credit score, income, loan amounts, funnel stages, approval, and default outcomes |
| 📊 **Funnel Analysis** | Stage-wise conversion rates, approval and funding rates, weekly application trends |
| 📈 **Advanced Insights** | Analyze how age, income, and credit score influence approvals. Cohort analysis by credit bands and income brackets |
| 🧪 **A/B Testing** | Compare approval and default rates for different underwriting strategies. Perform Z-tests for statistical significance |
| 🚨 **Automated Reporting** | Scheduled KPI monitoring and alerting if metrics fall below defined thresholds |
| 📊 **Interactive Dashboard** | Deployed with Streamlit to visualize KPIs, test results, cohort breakdowns, and alerts |

---

## 🧰 Tools & Technologies

- **Python**, **Pandas**, **SQLite**
- **Faker** for synthetic data generation  
- **Statsmodels** for A/B testing (Z-test for proportions)  
- **Streamlit** for dashboard deployment  
- **SQL** for query-based analysis (via SQLite)

---


---

## ✅ How to Run Locally

1. Clone the repo  
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Generate data and SQLite DB:
```bash
python src/generate_data.py
```

4. Launch the dashboard:
```bash
streamlit run dashboard/app.py
```
