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
        
    def create_dropoff_model(self, stage_col, condition=None):
        """Create a logistic regression model to predict drop-off at a specific stage"""
        if condition is not None:
            data = self.df[condition].copy()
        else:
            data = self.df.copy()
        
        features = ['credit_score', 'income', 'age', 'dti_ratio', 'loan_amount']
        X = data[features]
        y = data[stage_col]
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = LogisticRegression()
        model.fit(X_scaled, y)
        
        probabilities = model.predict_proba(X_scaled)[:, 1]
        
        return model, scaler, probabilities
    
    def train_all_models(self):
        """Train models for all stages"""
        # Stage 1: Application completion
        self.models['app_completion'], self.scalers['app_completion'], self.probabilities['app_completion'] = \
            self.create_dropoff_model('completed_app')
        
        # Stage 2: Document upload (only for those who completed app)
        completed_app_mask = self.df['completed_app'] == 1
        self.models['doc_upload'], self.scalers['doc_upload'], self.probabilities['doc_upload'] = \
            self.create_dropoff_model('uploaded_docs', completed_app_mask)
        
        # Add probabilities to dataframe
        self.df['prob_complete_app'] = self.probabilities['app_completion']
        self.df.loc[completed_app_mask, 'prob_upload_docs'] = self.probabilities['doc_upload']
    
    def calculate_abandonment_risk(self, row):
        """Calculate overall risk of abandonment"""
        risk_score = 0
        
        if row['credit_score'] < 650:
            risk_score += 0.3
        if row['dti_ratio'] > 0.43:
            risk_score += 0.2
        if row['loan_amount'] > 50000:
            risk_score += 0.1
        if row['employment_status'] == 'Unemployed':
            risk_score += 0.3
        
        if 'prob_complete_app' in row and pd.notna(row['prob_complete_app']):
            risk_score += (1 - row['prob_complete_app']) * 0.2
        
        return min(risk_score, 1.0)
    
    def create_risk_scores(self):
        """Create abandonment risk scores"""
        self.df['abandonment_risk'] = self.df.apply(self.calculate_abandonment_risk, axis=1)
    
    def create_cohort_groups(self):
        """Create cohort groupings"""
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
    
    def get_cohort_analysis(self):
        """Get cohort analysis results"""
        return self.df.groupby(['age_group', 'dti_group', 'credit_group']).agg({
            'abandonment_risk': 'mean',
            'completed_app': 'mean',
            'uploaded_docs': 'mean',
            'passed_underwriting': 'mean',
            'funded': 'mean',
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