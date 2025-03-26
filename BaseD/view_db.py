import sqlite3
import os
import json,sys
sys.stdout.reconfigure(encoding='utf-8')
# Chemin absolu vers la base
db_path = os.path.abspath("logs_memory.db")

# Connexion
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Requête pour lire les logs
cursor.execute("SELECT id, category, root_cause, created_at FROM processed_logs ORDER BY created_at DESC")
rows = cursor.fetchall()

print("🧠 Logs enregistrés dans la base:")
for row in rows:
    print(f"🆔 ID: {row[0]} | 📂 Catégorie: {row[1]} | 🪵 Root Cause: {row[2]} | 📅 Date: {row[3]}")

conn.close()
