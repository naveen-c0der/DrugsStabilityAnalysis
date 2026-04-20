
import pandas as pd
import random
from datetime import datetime, timedelta

def generate_clean_data(file_name='stability_data.csv'):
    # Define a clean, linear degradation trend for a "Normal" batch
    # Starting Potency: 100%, Start Date: 12 months ago
    # Limit: 95.0%
    # Measurements: 0, 3, 6, 9, 12 months

    start_date = datetime.now() - timedelta(days=365)
    
    data = []
    
    # Study 1: ST-NORMAL-001 (Perfect Linear Trend - Good for Demo)
    # Potency drops 0.5% every 3 months.
    # 0M: 100.0, 3M: 99.5, 6M: 99.0, 9M: 98.5, 12M: 98.0
    study_id = "ST-NORMAL-001"
    
    time_points = [0, 3, 6, 9, 12]
    potencies = [100.0, 99.5, 99.0, 98.5, 98.0]
    impurities = [0.1, 0.15, 0.2, 0.25, 0.3] # Rising slightly
    
    for i, t in enumerate(time_points):
        row = {
            'Study_ID': study_id,
            'Product_Name': 'DemoFast-500',
            'Batch_ID': 'B2024-001',
            'Time_Point_Month': t,
            'Test_Date': (start_date + timedelta(days=t*30)).strftime('%Y-%m-%d'),
            'Study_Type': 'Long-term',
            'Storage_Temperature': 25.0,
            'Storage_Humidity': 60.0,
            'Packaging_Type': 'Blister',
            'Potency_%': potencies[i],
            'Impurity_%': impurities[i],
            'Moisture_%': round(1.5 + (t * 0.05), 2),
            'Dissolution_%': round(95.0 - (t * 0.1), 2),
            'Potency_Lower': 95.0, # Limit
            'Potency_Upper': 105.0,
            'Impurity_Upper': 1.0,
            'Dissolution_Lower': 80.0
        }
        data.append(row)

    # Save
    df = pd.DataFrame(data)
    df.to_csv(file_name, index=False)
    print(f"✅ Generated Clean Demo Data: {file_name}")
    print(f"   Study ID: {study_id}")
    print("   Trend: Linear Degradation (Safe)")

if __name__ == "__main__":
    generate_clean_data()
