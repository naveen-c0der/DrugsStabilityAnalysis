import time
import os
import random
import requests
import argparse

API_URL = "http://127.0.0.1:5000/api/data"
BATCH_ID = "STB-001"

# Starting base values
current_month = 0
current_potency = 100.0
current_impurity = 0.05

def generate_sensor_data(inject_anomaly=False):
    global current_month, current_potency, current_impurity
    
    current_month += 1
    
    if inject_anomaly:
        # Generate an Out-Of-Trend (OOT) spike
        potency = current_potency - random.uniform(3.0, 5.0) # Sudden drop
        impurity = current_impurity + random.uniform(0.3, 0.6) # Sudden increase
        print(f"[!] Injecting Anomaly at Month {current_month}...")
    else:
        # Normal degradation
        potency = current_potency - random.uniform(0.1, 0.5)
        impurity = current_impurity + random.uniform(0.01, 0.05)
    
    # Add some noise
    potency += random.uniform(-0.2, 0.2)
    impurity += random.uniform(-0.02, 0.02)
    
    # Update state for next iteration
    current_potency = potency
    current_impurity = impurity
    
    return {
        "study_id": BATCH_ID,
        "time": current_month,
        "potency": round(potency, 2),
        "impurities": round(impurity, 3),
        "source": "sensor"
    }

def run_simulator(interval=30):
    print(f"[*] Starting Sensor Simulator... Sending data every {interval} seconds.")
    print("Press Ctrl+C to stop.")
    
    count = 0
    while True:
        try:
            # Inject an anomaly every ~10 data points
            inject_anomaly = count > 0 and count % 10 == 0
            
            payload = generate_sensor_data(inject_anomaly)
            
            print(f"[{time.strftime('%H:%M:%S')}] Sending Data: {payload}")
            response = requests.post(API_URL, json=payload)
            
            if response.status_code == 200:
                print("  [+] Successfully sent to Real-time Backend.")
            else:
                print(f"  [-] Error: {response.status_code} - {response.text}")
                
            count += 1
            time.sleep(interval)
            
        except requests.exceptions.ConnectionError:
            print("  [-] Connection Error: Backend is not running. Retrying...")
            time.sleep(5)
        except KeyboardInterrupt:
            print("\n[!] Sensor Simulator Stopped.")
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real-Time Sensor Simulator")
    parser.add_argument("--interval", type=int, default=10, help="Interval between readings in seconds")
    args = parser.parse_args()
    
    # For demo purposes, running every 10 seconds is better than 30s
    run_simulator(interval=args.interval)
