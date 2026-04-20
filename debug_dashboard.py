
import requests
import json
import pandas as pd
import os

BASE_URL = "http://127.0.0.1:5000"

def check_file():
    if os.path.exists("stability_data.csv"):
        print("✅ stability_data.csv found.")
        df = pd.read_csv("stability_data.csv")
        print(f"   Rows: {len(df)}")
        print(f"   Columns: {list(df.columns)}")
        if not df.empty:
            print(f"   Sample Study IDs: {df['Study_ID'].unique().tolist()}")
    else:
        print("❌ stability_data.csv NOT FOUND!")

def check_model_init():
    try:
        from old_ml_engine import StabilityModel
        model = StabilityModel()
        studies = model.get_all_studies()
        print(f"✅ Model initialized. Studies found internally: {studies}")
    except Exception as e:
        print(f"❌ Model initialization failed: {e}")

def check_api():
    print("\n--- Checking API ---")
    try:
        # Check Studies
        resp = requests.get(f"{BASE_URL}/api/studies")
        if resp.status_code == 200:
            studies = resp.json()
            print(f"✅ /api/studies: {studies}")
            
            if studies:
                first_study = studies[0]
                # Check Data
                resp_data = requests.get(f"{BASE_URL}/api/data?study_id={first_study}")
                if resp_data.status_code == 200:
                    data = resp_data.json()
                    print(f"✅ /api/data (for {first_study}): Found {len(data)} records.")
                else:
                    print(f"❌ /api/data failed: {resp_data.status_code}")
            else:
                print("⚠️ No studies returned from API.")
        else:
            print(f"❌ /api/studies failed: {resp.status_code}")
            
    except Exception as e:
        print(f"❌ API Connection failed: {e}")

if __name__ == "__main__":
    check_file()
    print("-" * 20)
    check_model_init()
    print("-" * 20)
    check_api()
