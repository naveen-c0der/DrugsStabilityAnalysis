
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import warnings

warnings.filterwarnings("ignore")

class StabilityModel:
    def __init__(self, data_file='stability_data_v2.csv'):
        self.data_file = data_file
        # Initial load
        try:
            self.data = pd.read_csv(self.data_file)
        except Exception as e:
            print(f"Error loading initial data: {e}")
            self.data = pd.DataFrame() 

    def _get_study_data(self, study_id):
        # Filter data for specific study
        return self.data[self.data['Study_ID'] == study_id].copy()

    def train_and_predict(self, study_id, target_col='Potency_%', steps=1):
        """
        Uses Linear Regression to learn the trend and predict future values.
        Returns (model, forecast_result)
        """
        df = self._get_study_data(study_id)
        
        # Clean data: Remove rows with missing Time or Target values
        df = df.dropna(subset=['Time_Point_Month', target_col])
        
        if df.empty or len(df) < 2:
            return None, None # Not enough data

        # Prepare X (Time) and y (Target)
        X = df[['Time_Point_Month']].values
        y = df[target_col].values

        # --- START MACHINE LEARNING SECTION ---
        
        # 1. Initialize ML Model (Linear Regression)
        model = LinearRegression()
        
        # 2. Train the Model (The "Learning" Phase)
        model.fit(X, y)
        
        # 3. Predict Future
        # Calculate next time point (e.g., last month + 3)
        last_month = df['Time_Point_Month'].max()
        next_month = last_month + (3 * steps) # Assuming 3-month intervals
        
        forecast_value = model.predict([[next_month]])
        
        # --- END ML SECTION ---
        
        return model, forecast_value

    def add_data(self, new_row):
        """
        Real-time update logic:
        1. Predict Expected using OLD data
        2. Check OOT
        3. Add New Data
        4. Retrain and Predict NEXT
        """
        study_id = new_row['Study_ID']
        
        # --- Step 1: Predict Expected (Pre-Update) ---
        current_data = self._get_study_data(study_id)
        oot_report = {}
        
        if not current_data.empty and len(current_data) >= 2:
            # Train on existing
            _, forecast = self.train_and_predict(study_id, 'Potency_%')
            if forecast is not None:
                # Note: This forecast is for the "next" month relative to old data
                # We need to predict specifically for the entered time point
                X = current_data[['Time_Point_Month']].values
                y = current_data['Potency_%'].values
                model = LinearRegression()
                model.fit(X, y)
                
                expected_potency = float(model.predict([[float(new_row['Time_Point_Month'])]])[0])
                actual_potency = float(new_row['Potency_%'])
                
                # OOT Check (Potency)
                # Relaxed threshold to avoid false alarms (was 1.0, now 1.5)
                threshold_pot = 1.5 
                diff_pot = actual_potency - expected_potency
                is_pot_oot = bool(abs(diff_pot) > threshold_pot)
                
                # OOT Check (Impurity)
                # Predict expected Impurity
                X_imp = current_data[['Time_Point_Month']].values
                y_imp = current_data['Impurity_%'].values
                model_imp = LinearRegression()
                model_imp.fit(X_imp, y_imp)
                
                expected_imp = float(model_imp.predict([[float(new_row['Time_Point_Month'])]])[0])
                actual_imp = float(new_row['Impurity_%'])
                
                # Threshold for impurity (was 0.2, now 0.5)
                threshold_imp = 0.5
                diff_imp = actual_imp - expected_imp
                is_imp_oot = bool(abs(diff_imp) > threshold_imp)
                
                # Combined OOT
                is_oot = is_pot_oot or is_imp_oot
                
                oot_report = {
                    'is_oot': is_oot,
                    'potency': {
                        'is_oot': is_pot_oot,
                        'expected': round(expected_potency, 2),
                        'actual': actual_potency,
                        'threshold': threshold_pot
                    },
                    'impurity': {
                        'is_oot': is_imp_oot,
                        'expected': round(expected_imp, 2),
                        'actual': actual_imp,
                        'threshold': threshold_imp
                    }
                }

            else:
                 oot_report = {'is_oot': False, 'message': 'Not enough data'}
        else:
            oot_report = {'is_oot': False, 'message': 'Baseline data'}

        # --- Step 2: Append New Data ---
        try:
            self.data = pd.read_csv(self.data_file)
            new_df = pd.DataFrame([new_row])
            self.data = pd.concat([self.data, new_df], ignore_index=True)
            self.data.to_csv(self.data_file, index=False)
        except Exception as e:
            return {'error': str(e)}

        # --- Step 3: Retrain & Predict NEXT Future Point ---
        self.data = pd.read_csv(self.data_file) # Reload with new data
        
        # Predict next Potency
        _, next_pot_forecast = self.train_and_predict(study_id, 'Potency_%')
        next_potency = round(next_pot_forecast[0], 2) if next_pot_forecast is not None else "N/A"
        
        # Predict next Impurity
        _, next_imp_forecast = self.train_and_predict(study_id, 'Impurity_%')
        next_impurity = round(next_imp_forecast[0], 2) if next_imp_forecast is not None else "N/A"

        # Determine next month label
        last_month = self.data[self.data['Study_ID'] == study_id]['Time_Point_Month'].max()
        next_month = last_month + 3
            
        return {
            'oot_report': oot_report,
            'next_prediction': {
                'month': int(next_month),
                'potency': next_potency,
                'impurity': next_impurity
            }
        }

    def predict_shelf_life(self, study_id):
        """
        Predicts when the product will fail based on current trends.
        Limits: Potency < 95.0, Impurity > 1.0
        Returns: Estimated Month of Failure (or 'Stable' if no failure predicted soon)
        """
        df = self._get_study_data(study_id)
        if df.empty or len(df) < 2:
            return "Insufficient Data"

        X = df[['Time_Point_Month']].values
        
        # 1. Check Potency Failure
        y_pot = df['Potency_%'].values
        model_pot = LinearRegression()
        model_pot.fit(X, y_pot)
        
        m_pot = model_pot.coef_[0]
        c_pot = model_pot.intercept_
        
        # If slope is negative (degrading), calculate when it hits 90.0
        potency_fail_month = 999
        if m_pot < 0:
            # 90 = mx + c  ->  mx = 90 - c  ->  x = (90 - c) / m
            potency_fail_month = (90.0 - c_pot) / m_pot
            
        # 2. Check Impurity Failure
        y_imp = df['Impurity_%'].values
        model_imp = LinearRegression()
        model_imp.fit(X, y_imp)
        
        m_imp = model_imp.coef_[0]
        c_imp = model_imp.intercept_
        
        # If slope is positive (increasing), calculate when it hits 1.0
        impurity_fail_month = 999
        if m_imp > 0:
            # 1.0 = mx + c -> x = (1.0 - c) / m
            impurity_fail_month = (1.0 - c_imp) / m_imp
            
        # 3. Determine Earliest Failure
        earliest_fail = min(potency_fail_month, impurity_fail_month)
        
        last_month = df['Time_Point_Month'].max()

        if earliest_fail > 120: # If failure is > 10 years away
            return {"total": "> 120 Months (Stable)", "remaining": "N/A"}
        elif earliest_fail < last_month:
             return {"total": "Already Failed", "remaining": "0 Months"}
        else:
            remaining = int(earliest_fail - last_month)
            return {"total": f"{int(earliest_fail)} Months", "remaining": f"{remaining} Months"}

    def get_study_data(self, study_id):
        df = self._get_study_data(study_id)
        return df.to_dict(orient='records')

    def get_all_studies(self):
        if 'Study_ID' in self.data.columns:
            return self.data['Study_ID'].unique().tolist()
        return []
