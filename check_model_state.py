
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

# Load the current clean data
df = pd.read_csv('stability_data.csv')
print("Current Data Points:")
print(df[['Time_Point_Month', 'Potency_%']])

# Train Model
X = df[['Time_Point_Month']].values
y = df['Potency_%'].values

model = LinearRegression()
model.fit(X, y)

# Get Trend Details
slope = model.coef_[0]
intercept = model.intercept_

print(f"\nDegradation Rate (Slope): {slope:.4f} % per month")
print(f"Starting Potency (Intercept): {intercept:.4f} %")

# Predict Month 15
next_time = 15
pred = model.predict([[next_time]])[0]
print(f"\nExpected Potency for Month {next_time}: {pred:.2f}%")

# Check OOT logic for a test value (e.g. 97.8 - normal, 95.0 - OOT)
threshold = 1.5
print(f"\n--- Testing OOT Logic ---")
test_val_normal = 97.8
diff_normal = abs(test_val_normal - pred)
print(f"Input {test_val_normal}% -> Deviation {diff_normal:.2f} -> OOT? {diff_normal > threshold}")

test_val_bad = 95.0
diff_bad = abs(test_val_bad - pred)
print(f"Input {test_val_bad}% -> Deviation {diff_bad:.2f} -> OOT? {diff_bad > threshold}")
