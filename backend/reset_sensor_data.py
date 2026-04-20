import sqlite3
import datetime
import random

DB_NAME = "backend/stability_system.db"

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Remove all data to restore a clean slate
cursor.execute("DELETE FROM stability_data")
cursor.execute("DELETE FROM oot_alerts")
cursor.execute("DELETE FROM batches")
conn.commit()
print("Cleaned all data. Adding 20 Active Studies...")

now = datetime.datetime.now()

# Add a realistic initial stability baseline for 20 studies
for i in range(1, 21):
    batch_id = f"STB-{i:03d}"
    
    # Register the batch
    cursor.execute("INSERT INTO batches (batch_id, product_name, start_date) VALUES (?, ?, ?)", 
                   (batch_id, f"Product_{i:03d}", now.strftime("%Y-%m-%d")))
    
    # Generate some slightly different baselines for each product
    start_pot = random.uniform(98.5, 101.5)
    start_imp = random.uniform(0.05, 0.15)
    
    # Each batch degrades at slightly different rates
    pot_drop = random.uniform(0.1, 0.5)
    imp_inc = random.uniform(0.02, 0.08)
    
    baseline_data = [
        (0, start_pot, start_imp),
        (3, start_pot - pot_drop*1.1, start_imp + imp_inc*1.1),
        (6, start_pot - pot_drop*2.2, start_imp + imp_inc*2.3),
        (9, start_pot - pot_drop*3.1, start_imp + imp_inc*3.2)
    ]
    
    now_iso = now.isoformat()
    for time_point, pot, imp in baseline_data:
        cursor.execute("""
            INSERT INTO stability_data (batch_id, time_point_month, potency, impurity, source, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (batch_id, time_point, round(pot, 2), round(imp, 3), 'manual', now_iso))

conn.commit()
print("Added baseline data for 20 studies!")
conn.close()
