
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# Load the generated stability data
df = pd.read_csv("c:/Users/Naveen S/Downloads/Medical/stability_data.csv")

# Simulated Machine Learning Logic
def test_ml_prediction(scenario_name, batch_id):
    print(f"\n--- {scenario_name} ({batch_id}) ---")
    
    # Filter data for the specific batch
    batch_data = df[df['Batch_ID'] == batch_id].sort_values('Time_Point_Month')
    
    if batch_data.empty:
        print(f"No data found for Batch ID: {batch_id}")
        return

    past_months = batch_data['Time_Point_Month'].values
    past_potency = batch_data['Potency_%'].values

    # 1. Train Model
    X = np.array(past_months).reshape(-1, 1)
    y = np.array(past_potency)
    model = LinearRegression()
    model.fit(X, y)
    
    # 2. Predict Future (Month 24)
    future_month = [[24]]
    prediction = model.predict(future_month)[0]
    
    # 3. Calculate Shelf Life (When will it hit 95%?)
    slope = model.coef_[0]
    intercept = model.intercept_
    
    # Formula: 95 = intercept + slope * time  =>  time = (95 - intercept) / slope
    if slope < 0:
        shelf_life = (95.0 - intercept) / slope
    else:
        shelf_life = 999 # Stable forever
        
    print(f"History (Months): {past_months}")
    print(f"History (Potency): {past_potency}")
    print(f"ML Slope: {slope:.4f} (Degradation Rate)")
    print(f"Predicted Potency at Month 24: {prediction:.2f}%")
    print(f"Estimated Shelf Life: {int(shelf_life)} Months")

# Scenario 1: Test with the first generated batch
first_batch = df['Batch_ID'].unique()[0]
test_ml_prediction("SCENARIO 1: Generated Batch", first_batch)

# Scenario 2: Test with a random other batch
import random
random_batch = random.choice(df['Batch_ID'].unique())
test_ml_prediction("SCENARIO 2: Random Batch", random_batch)
