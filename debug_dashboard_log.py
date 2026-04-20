
import requests
import pandas as pd
import os
import sys

BASE_URL = "http://127.0.0.1:5000"

with open("debug_log.txt", "w") as f:
    orig_stdout = sys.stdout
    sys.stdout = f
    
    try:
        if os.path.exists("stability_data.csv"):
            print("CHECK 1: stability_data.csv found.")
            df = pd.read_csv("stability_data.csv")
            print(f"   Rows: {len(df)}")
            if not df.empty and 'Study_ID' in df.columns:
                studies = df['Study_ID'].unique().tolist()
                print(f"   Sample Study IDs: {studies}")
            else:
                print("   File empty or missing Study_ID column.")
        else:
            print("CHECK 1: stability_data.csv NOT FOUND!")

        print("-" * 20)
        
        try:
            from old_ml_engine import StabilityModel
            model = StabilityModel()
            studies = model.get_all_studies()
            print(f"CHECK 2: Model initialized. Studies found internally: {studies}")
        except Exception as e:
            print(f"CHECK 2: Model init failed: {e}")

        print("-" * 20)
        
        print("CHECK 3: API Check")
        try:
            resp = requests.get(f"{BASE_URL}/api/studies", timeout=5)
            if resp.status_code == 200:
                studies = resp.json()
                print(f"   API /api/studies: {studies}")
                if studies:
                    first_study = studies[0]
                    resp_data = requests.get(f"{BASE_URL}/api/data?study_id={first_study}", timeout=5)
                    if resp_data.status_code == 200:
                        data = resp_data.json()
                        print(f"   API /api/data (for {first_study}): Found {len(data)} records.")
                    else:
                        print(f"   API /api/data failed: {resp_data.status_code}")
                else:
                    print("   API returned empty studies list.")
            else:
                print(f"   API /api/studies failed: {resp.status_code}")
        except Exception as e:
            print(f"   API Connection failed: {e}")
            
    except Exception as general_e:
        print(f"General script error: {general_e}")
    finally:
        sys.stdout = orig_stdout
