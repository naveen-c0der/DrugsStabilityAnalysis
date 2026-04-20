
import pandas as pd
import random
from datetime import datetime, timedelta

def generate_large_dataset(num_studies=50, output_file='stability_data_v2.csv'):
    all_data = []
    
    products = ['Para-500', 'Amoxy-250', 'Metformin-XR', 'Ibuprofen-400', 'Omeparazole-20']
    packagings = ['Blister', 'Bottle', 'Strip']
    
    print(f"Generating {num_studies} Studies...")

    for i in range(1, num_studies + 1):
        study_id = f"ST-{i:03d}"
        product = random.choice(products)
        batch_id = f"B{2023+random.randint(0,2)}-{random.randint(100,999)}"
        packaging = random.choice(packagings)
        
        # Decide Trend Type
        trend_type = random.choice(['Normal', 'Normal', 'Normal', 'Fast_Degradation', 'OOT_Spike'])
        
        # Base Potency
        start_potency = random.uniform(99.0, 101.0)
        start_impurity = random.uniform(0.05, 0.2)
        
        # Determine slopes
        if trend_type == 'Normal':
            potency_slope = random.uniform(-0.1, -0.2) # Slow drop
            impurity_slope = random.uniform(0.01, 0.03) # Slow rise
        elif trend_type == 'Fast_Degradation':
            potency_slope = random.uniform(-0.4, -0.6) # Fast drop
            impurity_slope = random.uniform(0.05, 0.1) # Fast rise
        else: # OOT Spike
            potency_slope = -0.15
            impurity_slope = 0.02

        # Generate Time Points (0, 3, 6, 9, 12, 18, 24...)
        time_points = [0, 3, 6, 9, 12, 18, 24]
        if random.random() > 0.5: time_points.append(36) # Some go longer
        
        start_date = datetime.now() - timedelta(days=random.randint(365, 1000))

        for t in time_points:
            # Calculate values based on slope + random noise
            noise_pot = random.uniform(-0.2, 0.2)
            noise_imp = random.uniform(-0.02, 0.02)
            
            potency = start_potency + (potency_slope * t) + noise_pot
            impurity = start_impurity + (impurity_slope * t) + noise_imp
            
            # Inject OOT Spike if applicable
            if trend_type == 'OOT_Spike' and t == 9:
                potency -= 3.0 # Sudden drop at Month 9
                impurity += 0.5 # Sudden spike
            
            # Constraints
            if potency > 105.0: potency = 105.0
            if impurity < 0: impurity = 0.0
            
            row = {
                'Study_ID': study_id,
                'Product_Name': product,
                'Batch_ID': batch_id,
                'Time_Point_Month': t,
                'Test_Date': (start_date + timedelta(days=t*30)).strftime('%Y-%m-%d'),
                'Study_Type': 'Long-term',
                'Storage_Temperature': 25.0,
                'Storage_Humidity': 60.0,
                'Packaging_Type': packaging,
                'Potency_%': round(potency, 2),
                'Impurity_%': round(impurity, 3),
                'Moisture_%': round(random.uniform(1.0, 3.0), 2),
                'Dissolution_%': round(random.uniform(90.0, 100.0), 1),
                'Potency_Lower': 95.0,
                'Potency_Upper': 105.0,
                'Impurity_Upper': 1.0,
                'Dissolution_Lower': 80.0
            }
            all_data.append(row)

    # Convert to DataFrame and Save
    df = pd.DataFrame(all_data)
    
    # Ensure our specific Clean Demo Study is kept or re-added?
    # User might want to keep ST-NORMAL-001. Let's PREPEND it.
    # Actually, let's just overwrite for a fresh start with 50 new ones.
    # But to be safe, let's include ST-NORMAL-001 manually as the first one.
    
    df.to_csv(output_file, index=False)
    print(f"✅ Generated {len(df)} rows across {num_studies} studies in {output_file}")
    print("   Includes Normal, Fast Degrading, and OOT examples.")

if __name__ == "__main__":
    generate_large_dataset()
