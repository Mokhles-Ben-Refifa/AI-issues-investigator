from groq import Groq
import os
import datetime
import json
from serpapi import GoogleSearch
import sys
from multiprocessing import Queue, Process
from agno.agent import Agent
from agents.agent_server import ServerAgent
from agents.agent_system import SystemAgent
from agents.agent_network import NetworkAgent
from agents.agent_db import DatabaseAgent
from agents.agent_app import ApplicationAgent
import sqlite3
import hashlib

import unicodedata

sys.stdout.reconfigure(encoding='utf-8')




#API_KEY = "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"
#API_KEY = "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"
#@gmail
#API_KEY = "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"

API_KEY = "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"






#SERP_API_KEY = "424558b7399112915fbefbb834dab8bb9c95d638623681c75decd9b9fd2a0100"
SERP_API_KEY = "bccb5398af513a4b65beb318d3891c679fbe3ea71364e93af6f4643fac41b55d"

client = Groq(api_key=API_KEY)
log_path = r'C:\Users\Legion\Documents\AI issues investigator\dispatched_logs.log'

try:
    with open(log_path, 'r', encoding="utf-8") as f:
        log_entry = f.read()
except FileNotFoundError:
    print(f"❌ Fichier log introuvable : {log_path}")
    sys.exit(1)

prompt_root_cause = f"""
You are a senior log analysis expert.

You will receive a list of **log clusters**, each identified by an `id` and a list of associated log messages.

### Your task:
For **each cluster**, determine whether the logs indicate a system failure or critical issue.

- If the cluster contains any log with level `ERROR` or `CRITICAL`, analyze it and identify the **most probable root cause**.
- Otherwise, **do not include that cluster** in your response.

For each relevant cluster, return a root cause in the appropriate category:
- **Server**: web server failure, 5xx errors, load balancer issues.
- **Database**: query failures, timeouts, replication issues.
- **Application**: unhandled exceptions, crashes, logic bugs.
- **System**: OS errors, memory/CPU issues, file system problems.
- **Network**: timeouts, packet loss, latency spikes.

### Instructions:
- Use only the logs that include `"ERROR"` or `"CRITICAL"` for root cause determination.
- Output your analysis in **valid JSON format** only.
- **Do not include any explanations or extra text** outside the JSON structure.
- If no cluster has issues, return an **empty JSON object** (`{{}}`).

### Output format:
```json
{{
  "CATEGORY_NAME": [
    {{
      "Cluster ID": <cluster_id>,
      "Root Cause": "Describe the exact root cause concisely.",
      "Log Classification": "CATEGORY_NAME",
      "Explanation": {{
        "Log Message": "Highlight the most relevant error or critical log.",
        "Possible Causes": [
          "List possible reasons for this issue."
        ],
        "Detailed Root Cause Analysis": {{
          "Observations": "What do the logs reveal?",
          "Impact": "What is the impact on the system?",
          "Correlations": "Link to any related logs or patterns."
        }},
        "Conclusion": "Why is this the most likely root cause?"
      }}
    }}
  ]
}}







### **Log Entry:**
{log_entry}
"""

completion_root_cause = client.chat.completions.create(
        #model="llama3-70b-8192",
        #model="qwen-2.5-32b",
        #model="llama-3.3-70b-versatile",
        model="deepseek-r1-distill-llama-70b",
        messages=[{"role": "user", "content": prompt_root_cause}],
        temperature=0.6,
        max_tokens=4096,
        #response_format={"type": "json_object"},
        top_p=0.95
    )

import re
def extract_json(response_text):
    """
    Extracts the JSON portion from a text response.
    
    Args:
        response_text (str): The full response containing text and JSON.
    
    Returns:
        dict: Parsed JSON object if valid, else None.
    """
    
    match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
    
    if not match:
        
        match = re.search(r'(\{.*\})', response_text, re.DOTALL)

    if match:
        json_text = match.group(1).strip()
        try:
            return json.loads(json_text) 
        except json.JSONDecodeError:
            return None 
    
    return None 


timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
#root_cause_file = f"root_cause_analysis_{timestamp}.json"
directory="analysis"
root_cause_file = f"{directory}/root_cause_analysis_{timestamp}.json"

def clean_text(text):
    lines = text.split("\n")
    if len(lines) > 3:
        return "\n".join(lines[3:-1])
    print("⚠️ Pas assez de lignes à nettoyer.")
    return ""

if completion_root_cause.choices:
    cleaned_json = extract_json(completion_root_cause.choices[0].message.content)
    
    with open(root_cause_file, 'w', encoding="utf-8") as output_file:
        output_file.write(json.dumps(cleaned_json, indent=4, ensure_ascii=False))
    print(f"✅ Analyse sauvegardée : {root_cause_file}")
else:
    print("❌ Erreur: aucune réponse générée.")

def normalize_text(text):
    """Normalise les caractères spéciaux en ASCII."""
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')


def is_log_already_processed_llm(log_entry, client):
    """
    Uses a LLM to compare the current root cause to previously stored root causes
    in the category-specific table. Returns True if a similar one is found.
    """
    try:
        db_path = os.path.abspath("logs_memory.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Extract root cause and category
        new_root_cause = log_entry.get("Root Cause", "").strip()
        category = log_entry.get("Log Classification", "").strip().lower()  # Ex: "system", "server"

        if not new_root_cause or not category:
            print("⚠️ Missing root cause or category in log entry.")
            return False

        # Map to the correct table name
        table_name = f"processed_logs_{category}"
        cursor.execute(f"SELECT root_cause, recommendation FROM {table_name}")
        rows = cursor.fetchall()
        past_root_causes = [row[0] for row in rows]
        recommendations = [row[1] for row in rows]
        conn.close()

        # 🧪 Debug print
        print(f"\n🔍 New Root Cause:\n{new_root_cause}\n")
        print(f"📦 Past Root Causes in '{table_name}' ({len(past_root_causes)} found):")

        if not past_root_causes:
            return False

        prompt = f"""

You are an expert in log root cause analysis.

Your task is to determine whether the following **new root cause** is semantically equivalent to **any** of the previously seen root causes.

---

🆕 New Root Cause:
"{new_root_cause}"

📂 Previously Recorded Root Causes:
{json.dumps(past_root_causes, indent=2)}

---

### Rules:
- Two root causes are considered **equivalent** if they describe the same underlying issue, even with different wording.
- Be strict: respond "True" only if the meaning is clearly the same.
- Respond "False" if it's uncertain, ambiguous, or different.
- Your answer **must be either** `True` or `False`, with **no explanation**.
- give me the final result true or false without the </think>

### Final Answer:True or False nothing else you don't give me anything else i want just true or false 
"""


        response = client.chat.completions.create(
            model="deepseek-r1-distill-llama-70b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=4096,
            top_p=0.95
        )

        result = response.choices[0].message.content.strip().lower()
        print(f"🧠 LLM Response: {result}")
        if result=="true":
            print(recommendations[0])

        return result == "true"

    except Exception as e:
        print(f"⚠️ Error in is_log_already_processed_llm: {e}")
        return False




class HubAgent(Agent):
    def __init__(self, queues):
        super().__init__()
        self.queues = queues



    def distribute_logs(self):
        """Envoie les logs classifiés aux agents appropriés."""
        if hasattr(self, "_already_executed"):
            print("⚠️ distribute_logs() a déjà été exécuté, annulation.")
            return
        self._already_executed = True  
        print("📌 Début de distribute_logs()")

        try:
            with open(root_cause_file, "r", encoding="utf-8") as file:
                analyzed_logs = json.load(file)
        except json.JSONDecodeError as e:
            print(f"❌ Erreur JSON : {e}")
            return

       
        for category, logs in analyzed_logs.items():
            normalized_category = normalize_text(category)  
            print(f"🔍 Catégorie détectée : {normalized_category}")

            if normalized_category in self.queues:
                for log_entry in logs: 
                    if not is_log_already_processed_llm(log_entry, client):
                        self.queues[normalized_category].put(log_entry)
                        print(f"📤 Log envoyé à {normalized_category}Agent")
                    else:
                        print(f"♻️ Log ignoré (déjà traité - cache hit).")

                   
            else:
                print(f"⚠️ Aucune queue trouvée pour {normalized_category}")


import time
import multiprocessing
import threading
if __name__ == "__main__":
    print(f"📌 Processus principal : {multiprocessing.current_process().name}")
    
    queues = {
        "Server": Queue(),
        "Database": Queue(),
        "Application": Queue(),
        "System": Queue(),
        "Network": Queue()
    }

    # ServerAgent
    server_agent = ServerAgent(queues["Server"])
    server_thread = threading.Thread(target=server_agent.listen_for_logs, daemon=True)
    server_thread.start()

    # SystemAgent 
    system_agent = SystemAgent(queues["System"])
    system_thread = threading.Thread(target=system_agent.listen_for_logs, daemon=True)
    system_thread.start()
    # NetworkAgent
    network_agent = NetworkAgent(queues["Network"])
    network_thread = threading.Thread(target=network_agent.listen_for_logs, daemon=True)
    network_thread.start()

    # DatabaseAgent
    database_agent = DatabaseAgent(queues["Database"])
    database_thread = threading.Thread(target=database_agent.listen_for_logs, daemon=True)
    database_thread.start()

    # ApplicationAgent
    application_agent = ApplicationAgent(queues["Application"])
    application_thread = threading.Thread(target=application_agent.listen_for_logs, daemon=True)
    application_thread.start()


 

    hub = HubAgent(queues)
    hub.distribute_logs()

    
    queues["Server"].put({"stop": True})
    server_thread.join()
    print("🛑 ServerAgent arrêté proprement.")

    queues["System"].put({"stop": True})
    system_thread.join()
    print("🛑 SystemAgent arrêté proprement.")  

    queues["Network"].put({"stop": True})
    network_thread.join()
    print("🛑 NetworkAgent arrêté proprement.")

    queues["Database"].put({"stop": True})
    database_thread.join()
    print("🛑 DatabaseAgent arrêté proprement.")

    queues["Application"].put({"stop": True})
    application_thread.join()
    print("🛑 ApplicationAgent arrêté proprement.")
