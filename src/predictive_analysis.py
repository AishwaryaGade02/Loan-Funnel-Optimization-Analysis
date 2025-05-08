import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

class PredictiveDropoffAnalysis:
    def __init__(self, df):
        self.df = df.copy()
        self.models = {}
        self.scalers = {}
        self.probabilities = {}
        
    def create_stage_indicators(self):
        """Create stage progression indicators"""
        self.df['completed_app'] = self.df['funnel_stage'].isin(['Documents Uploaded', 'Underwriting Review', 'Approved', 'Funded']).astype(int)
        self.df['uploaded_docs'] = self.df['funnel_stage'].isin(['Underwriting Review', 'Approved', 'Funded']).astype(int)
        self.df['passed_underwriting'] = self.df['funnel_stage'].isin(['Approved', 'Funded']).astype(int)
        self.df['funded'] = (self.df['funnel_stage'] == 'Funded').astype(int)
        print(self.df)
        
    def create_dropoff_model(self, stage_col, condition=None):
        """Create a logistic regression model to predict drop-off at a specific stage"""
        if condition is not None:
            data = self.df[condition].copy()
        else:
            data = self.df.copy()
        
        features = ['credit_score', 'income', 'age', 'dti_ratio', 'loan_amount','employment_status']
        X = data[features]
        y = data[stage_col]

        X = pd.get_dummies(X,columns=["employment_status"])
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = LogisticRegression()
        model.fit(X_scaled, y)
        
        probabilities = model.predict_proba(X_scaled)[:, 1]
        print(f"The model is: {model}")
        print(f"The scaler is: {scaler}")
        print(f"The probabilities: {probabilities}")
        
        return model, scaler, probabilities
    
    def train_all_models(self):
        """Train models for all stages in the funnel"""
        # Stage 1: Application completion
        self.models['app_completion'], self.scalers['app_completion'], self.probabilities['app_completion'] = \
        self.create_dropoff_model('completed_app')
    
        # Stage 2: Document upload (only for those who completed app)
        completed_app_mask = self.df['completed_app'] == 1
        self.models['doc_upload'], self.scalers['doc_upload'], self.probabilities['doc_upload'] = \
        self.create_dropoff_model('uploaded_docs', completed_app_mask)
    
        # Stage 3: Underwriting passage (only for those who uploaded docs)
        uploaded_docs_mask = self.df['uploaded_docs'] == 1
        self.models['underwriting'], self.scalers['underwriting'], self.probabilities['underwriting'] = \
        self.create_dropoff_model('passed_underwriting', uploaded_docs_mask)
    
        # Stage 4: Funding (only for those who passed underwriting)
        passed_uw_mask = self.df['passed_underwriting'] == 1
        self.models['funding'], self.scalers['funding'], self.probabilities['funding'] = \
        self.create_dropoff_model('funded', passed_uw_mask)
    
    # Add all probabilities to dataframe
        self.df['prob_complete_app'] = self.probabilities['app_completion']
        self.df.loc[completed_app_mask, 'prob_upload_docs'] = self.probabilities['doc_upload']
        self.df.loc[uploaded_docs_mask, 'prob_underwriting'] = self.probabilities['underwriting']
        self.df.loc[passed_uw_mask, 'prob_funding'] = self.probabilities['funding']
    
    def calculate_abandonment_risk(self,row):
    # Get dropout probabilities at each stage (prob of NOT continuing)
        
        p_app = row.get('prob_complete_app', None)
        p_doc = row.get('prob_upload_docs', None)
        p_under = row.get('prob_underwriting', None)
        p_fund = row.get('prob_funding', None)

    # If any stage's probability is missing, assume zero dropout for conservative estimate
        survival_probs = [
            p for p in [p_app, p_doc, p_under, p_fund] if p is not None
        ]

        # Multiply all survival probabilities
        survival = 1.0
        for s in survival_probs:
            survival *= s

        # Abandonment risk is 1 - cumulative survival
        abandonment_risk = 1 - survival

        return round(abandonment_risk, 4)

    
    def create_risk_scores(self):
        """Create abandonment risk scores"""
        self.df['abandonment_risk'] = self.df.apply(self.calculate_abandonment_risk, axis=1)
    
    def create_cohort_groups(self):
        """Create cohort groupings"""
    # Existing code
        self.df['age_group'] = pd.cut(
            self.df['age'],
        bins=[17, 25, 35, 45, 55, 65, float('inf')],
        labels=['18-25', '26-35', '36-45', '46-55', '56-65', '65+']
    )
    
        self.df['dti_group'] = pd.cut(
        self.df['dti_ratio'],
        bins=[-float('inf'), 0.36, 0.50, float('inf')],
        labels=['Low DTI', 'Medium DTI', 'High DTI']
    )
    
        self.df['credit_group'] = pd.cut(
        self.df['credit_score'],
        bins=[-float('inf'), 580, 669, 739, 799, float('inf')],
        labels=['Poor (<580)', 'Fair (580-669)', 'Good (670-739)', 'Very Good (740-799)', 'Excellent (800+)']
    )
    
    # Add income band categorization
        self.df['income_band'] = pd.cut(
        self.df['income'],
        bins=[-float('inf'), 40000, 80000, float('inf')],
        labels=['Low (<40K)', 'Mid (40K-80K)', 'High (80K+)']
    )
    
    # Add loan amount categorization
        conditions = [
        self.df['loan_amount'] < 5000,
        (self.df['loan_amount'] >= 5000) & (self.df['loan_amount'] <= 10000),
        (self.df['loan_amount'] > 10000) & (self.df['loan_amount'] <= 15000),
        (self.df['loan_amount'] > 15000) & (self.df['loan_amount'] <= 25000),
        (self.df['loan_amount'] > 25000) & (self.df['loan_amount'] <= 35000),
        self.df['loan_amount'] > 35000
    ]
        choices = [
        'Very Small Loan', 
        'Small Loan', 
        'Medium Loan', 
        'Large Loan', 
        'Very Large Loan', 
        'High-End Loan'
    ]
        self.df['loan_amount_group'] = np.select(conditions, choices, default='Unknown')
    
    # Employment status is already a category, just ensure it's formatted consistently
        self.df['employment_status'] = self.df['employment_status'].apply(
        lambda x: 'Employed' if x.lower() == 'employed' else 
                 'Unemployed' if x.lower() == 'unemployed' else 
                 'Self-Employed' if x.lower() in ['self-employed', 'self employed'] else x
    )
    
    def get_cohort_analysis(self):
        """Get cohort analysis results"""
        return self.df.groupby(['age_group', 'dti_group', 'credit_group', 'income_band', 'loan_amount_group', 'employment_status']).agg({
        
        'completed_app': 'mean',
        'uploaded_docs': 'mean',
        'passed_underwriting': 'mean',
        'funded': 'mean',
        'abandonment_risk': 'mean',
        'applicant_id': 'count'

    }).round(3).reset_index()
    
    def get_feature_importance(self):
        """Get feature importance from models"""
        feature_names = ['credit_score', 'income', 'age', 'dti_ratio', 'loan_amount']
        importance_data = []
        
        for stage, model in self.models.items():
            for feature, coef in zip(feature_names, model.coef_[0]):
                importance_data.append({
                    'stage': stage,
                    'feature': feature,
                    'importance': abs(coef)
                })
        print(f"pd.DataFrame(importance_data) : {pd.DataFrame(importance_data)}")
        return pd.DataFrame(importance_data)
    
    def run_analysis(self):
        """Run the complete analysis pipeline"""
        self.create_stage_indicators()
        self.train_all_models()
        self.create_risk_scores()
        self.create_cohort_groups()
        
        return {
            'cohort_analysis': self.get_cohort_analysis(),
            'feature_importance': self.get_feature_importance(),
            'dataframe': self.df
        }

def run_predictive_analysis(df):
    """Main function to run the analysis"""
    analyzer = PredictiveDropoffAnalysis(df)
    return analyzer.run_analysis()

if __name__=="__main__":
    df = pd.read_csv('./data/loan_funnel_data.csv')
    results = run_predictive_analysis(df)
    print(results)