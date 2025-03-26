import sqlite3
import os, sys
sys.stdout.reconfigure(encoding='utf-8')

db_path = os.path.abspath("logs_memory.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

categories = ["server", "system", "application", "network", "database"]

for cat in categories:
    table_name = f"processed_logs_{cat}"
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        log TEXT,
        root_cause TEXT,
        recommendation TEXT,
        log_hash TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    print(f"✅ Table '{table_name}' (re)créée avec succès.")

conn.commit()
conn.close()
