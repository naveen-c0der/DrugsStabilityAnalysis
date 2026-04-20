import os
import time
import requests
import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_DIRECTORY = "data/watch_folder"
PROCESSED_DIRECTORY = "data/processed_folder"
API_URL = "http://127.0.0.1:5000/api/data"

# Ensure directories exist
os.makedirs(WATCH_DIRECTORY, exist_ok=True)
os.makedirs(PROCESSED_DIRECTORY, exist_ok=True)

class CSVHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        if file_path.endswith('.csv'):
            print(f"\n📁 New CSV Detected: {file_path}")
            # Wait a moment to ensure the file writing is complete
            time.sleep(1)
            self.process_csv(file_path)

    def process_csv(self, file_path):
        try:
            df = pd.read_csv(file_path)
            
            # Require standard columns for processing
            required_cols = {"Study_ID", "Time_Point_Month", "Potency_%", "Impurity_%"}
            if not required_cols.issubset(set(df.columns)):
                print(f"  ❌ Invalid CSV Format. Must contain: {required_cols}")
                return

            print(f"  📊 Found {len(df)} rows. Processing via API...")
            success_count = 0
            
            for index, row in df.iterrows():
                payload = {
                    "study_id": row["Study_ID"],
                    "time": row["Time_Point_Month"],
                    "potency": row["Potency_%"],
                    "impurities": row["Impurity_%"],
                    "source": "csv_watcher"
                }

                # Send to Flask API
                try:
                    response = requests.post(API_URL, json=payload, timeout=5)
                    if response.status_code == 200:
                        success_count += 1
                except requests.exceptions.RequestException as e:
                    print(f"  ❌ API Connection Error: {e}")
                    break
                    
            print(f"  ✅ Sent {success_count}/{len(df)} points successfully.")
            
            # Retain in processed folder
            filename = os.path.basename(file_path)
            processed_path = os.path.join(PROCESSED_DIRECTORY, f"{time.time()}_{filename}")
            os.rename(file_path, processed_path)
            print(f"  📂 File moved to: {processed_path}")

        except Exception as e:
            print(f"  ❌ Error processing file {file_path}: {e}")

if __name__ == "__main__":
    print(f"🔍 Starting CSV Watcher... Monitoring: {WATCH_DIRECTORY}")
    
    event_handler = CSVHandler()
    observer = Observer()
    observer.schedule(event_handler, path=WATCH_DIRECTORY, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping CSV Watcher.")
        observer.stop()
    observer.join()
