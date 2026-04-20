
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration
NUM_BATCHES = 45  # Meeting the 30-50 requirement
TIME_POINTS = [0, 3, 6, 9, 12, 18]
PRODUCT_NAME = "Tablet_A"
STUDY_ID = "ST001"
START_DATE = datetime(2023, 1, 1)

# Specification Limits
SPECS = {
    "Potency_Lower": 95.0,
    "Potency_Upper": 105.0,
    "Impurity_Upper": 1.0,
    "Dissolution_Lower": 80.0
}

# Parameters Initial Values (Mean, Std Dev)
PARAMS = {
    "Potency_%": {"start_mean": 100.0, "start_std": 0.5, "deg_rate_mean": -0.15, "deg_rate_std": 0.05, "noise": 0.2},
    "Impurity_%": {"start_mean": 0.1, "start_std": 0.02, "deg_rate_mean": 0.03, "deg_rate_std": 0.01, "noise": 0.02},
    "Moisture_%": {"start_mean": 1.5, "start_std": 0.2, "deg_rate_mean": 0.05, "deg_rate_std": 0.02, "noise": 0.1},
    "Dissolution_%": {"start_mean": 95.0, "start_std": 1.0, "deg_rate_mean": -0.2, "deg_rate_std": 0.1, "noise": 0.5}
}

data = []

for batch_num in range(1, NUM_BATCHES + 1):
    batch_id = f"B2023_{batch_num:03d}"
    
    # Assign specific degradation rates for this batch
    batch_rates = {}
    batch_starts = {}
    for param, config in PARAMS.items():
        batch_rates[param] = np.random.normal(config["deg_rate_mean"], config["deg_rate_std"])
        batch_starts[param] = np.random.normal(config["start_mean"], config["start_std"])

    # Simulate OOT (Out of Trend) for a few batches
    is_oot_batch = np.random.random() < 0.1 # 10% chance of being an OOT batch
    if is_oot_batch:
        # Example: Potency degrades much faster
        batch_rates["Potency_%"] *= 2.0 
    
    for month in TIME_POINTS:
        row = {
            "Study_ID": STUDY_ID,
            "Product_Name": PRODUCT_NAME,
            "Batch_ID": batch_id,
            "Time_Point_Month": month,
            "Test_Date": (START_DATE + timedelta(days=month*30)).strftime("%Y-%m-%d"),
            "Study_Type": "Long-term",
            "Storage_Temperature": 25,
            "Storage_Humidity": 60,
            "Packaging_Type": "Blister",
        }
        
        # Calculate parameter values
        for param, config in PARAMS.items():
            base_value = batch_starts[param] + (batch_rates[param] * month)
            noise = np.random.normal(0, config["noise"])
            final_value = base_value + noise
            
            # Ensure logical bounds (e.g., >= 0)
            if final_value < 0: final_value = 0
            if param == "Potency_%" and final_value > 105: final_value = 105
            
            row[param] = round(final_value, 2)

        # Add Specification Limits
        row["Potency_Lower"] = SPECS["Potency_Lower"]
        row["Potency_Upper"] = SPECS["Potency_Upper"]
        row["Impurity_Upper"] = SPECS["Impurity_Upper"]
        row["Dissolution_Lower"] = SPECS["Dissolution_Lower"]

        data.append(row)

# Create DataFrame
df = pd.DataFrame(data)

# Save to CSV
output_file = "c:/Users/Naveen S/Downloads/Medical/stability_data.csv"
df.to_csv(output_file, index=False)

print(f"Successfully regenerated clean stability data in {output_file}")
