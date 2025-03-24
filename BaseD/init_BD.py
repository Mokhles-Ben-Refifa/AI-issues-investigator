# init_db.py
import sqlite3

conn = sqlite3.connect("logs_memory.db")  # crée le fichier SQLite

cursor = conn.cursor()

# Création de la table de cache
cursor.execute("""
CREATE TABLE IF NOT EXISTS processed_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log TEXT NOT NULL,
    category TEXT,
    root_cause TEXT,
    recommendation TEXT,
    log_hash TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

conn.commit()
conn.close()

print("✅ Base de données SQLite initialisée.")
