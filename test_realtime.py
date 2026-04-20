
from old_ml_engine import StabilityModel
import pandas as pd

# Initialize
model = StabilityModel()
print("--- Initial Data ---")
print(model.data[['Time_Point_Month', 'Potency_%']].tail(5))

# Simulate User Entering Data for Month 12
print("\n--- 1. User Enters New Data (Month 12) ---")
new_data = {
    'Study_ID': 'ST001',
    'Time_Point_Month': 12,
    'Potency_%': 98.2,  # Let's say actual result is 98.2
    'Impurity_%': 0.22,
    'Moisture_%': 1.5,
    'Dissolution_%': 93.0
}

# Process (Add + OOT + Predict Next)
print("Processing...")
result = model.add_data(new_data)

print("\n--- 2. System Response ---")

# OOT Check
oot = result['oot_report']
potency_info = oot.get('potency', {})
print(f"OOT Check for Month 12: {'⚠️ ALERT' if oot['is_oot'] else '✅ OK'}")
print(f"  - Expected Potency: {potency_info.get('expected')}%")
print(f"  - Actual Input:     {potency_info.get('actual')}%")

# Future Prediction
pred = result['next_prediction']
print(f"\n--- 3. Real-Time Future Prediction ---")
print(f"System automatically retrained and predicted for Month {pred['month']}:")
print(f"  - Predicted Potency:   {pred['potency']}%")
print(f"  - Predicted Impurity:  {pred['impurity']}%")

print("\n(This is exactly what happens when you click 'Analyze & Save' on the website)")
