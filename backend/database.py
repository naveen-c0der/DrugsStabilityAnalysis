import sqlite3
import datetime
import os

# Use an absolute path so the DB is always found regardless of which directory
# Python is launched from (fixes errors when running from backend/ vs project root)
DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stability_system.db")

def init_db():
    """Initializes the SQLite database with the required tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Table 1: Batches (Master table for the studies)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT UNIQUE NOT NULL,
            product_name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            status TEXT DEFAULT 'Active'
        )
    """)

    # Table 2: Stability Data (Every single test result)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stability_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT NOT NULL,
            time_point_month INTEGER NOT NULL,
            potency REAL NOT NULL,
            impurity REAL NOT NULL,
            source TEXT NOT NULL,           -- 'manual', 'csv_watcher', 'sensor'
            timestamp TEXT NOT NULL,
            FOREIGN KEY(batch_id) REFERENCES batches(batch_id)
        )
    """)

    # Table 3: OOT Alerts (Logged anomalies)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS oot_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT NOT NULL,
            attribute TEXT NOT NULL,        -- 'Potency' or 'Impurity'
            expected_value REAL,
            actual_value REAL NOT NULL,
            deviation REAL,
            severity TEXT NOT NULL,         -- 'Warning', 'Investigate', 'Critical'
            timestamp TEXT NOT NULL,
            FOREIGN KEY(batch_id) REFERENCES batches(batch_id)
        )
    """)

    # Insert a dummy batch just to ensure we have a starting point
    cursor.execute("INSERT OR IGNORE INTO batches (batch_id, product_name, start_date) VALUES (?, ?, ?)", 
                   ("STB-001", "Aspirin_100mg", datetime.datetime.now().strftime("%Y-%m-%d")))

    conn.commit()
    conn.close()
    print("Database Initialized Successfully.")

def insert_data(batch_id, time_point, potency, impurity, source):
    """Inserts a new data point into the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.datetime.now().isoformat()
    
    # Ensure batch exists
    cursor.execute("INSERT OR IGNORE INTO batches (batch_id, product_name, start_date) VALUES (?, ?, ?)", 
                   (batch_id, "Unknown_Product", datetime.datetime.now().strftime("%Y-%m-%d")))
                   
    cursor.execute("""
        INSERT INTO stability_data (batch_id, time_point_month, potency, impurity, source, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (batch_id, time_point, potency, impurity, source, now))
    
    conn.commit()
    conn.close()

def log_oot_alert(batch_id, attribute, expected, actual, deviation, severity):
    """Logs an Out-of-Trend alert to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO oot_alerts (batch_id, attribute, expected_value, actual_value, deviation, severity, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (batch_id, attribute, expected, actual, deviation, severity, now))

    conn.commit()
    conn.close()

def get_study_data(batch_id):
    """Retrieves all data for a specific batch, sorted by time."""
    conn = sqlite3.connect(DB_NAME)
    # Return dictionary-like rows
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT time_point_month, potency, impurity, source, timestamp 
        FROM stability_data 
        WHERE batch_id = ? 
        ORDER BY time_point_month ASC
    """, (batch_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_oot_alerts(batch_id):
    """Retrieves all OOT alerts for a specific batch."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT attribute, expected_value, actual_value, severity, timestamp
        FROM oot_alerts
        WHERE batch_id = ?
        ORDER BY timestamp DESC
    """, (batch_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_all_batches():
    """Retrieves all available batch IDs."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT batch_id FROM batches ORDER BY batch_id ASC")
    rows = cursor.fetchall()
    conn.close()
    
    return [row['batch_id'] for row in rows]

if __name__ == "__main__":
    init_db()
