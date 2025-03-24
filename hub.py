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
log_path = r'C:\Users\Legion\Documents\AI issues investigator\logu.log'

try:
    with open(log_path, 'r', encoding="utf-8") as f:
        log_entry = f.read()
except FileNotFoundError:
    print(f"❌ Fichier log introuvable : {log_path}")
    sys.exit(1)

prompt_root_cause = f"""
Analyze the log file below and identify root causes for any detected issues and you must respond in json format following the structure that i give to you bellow. The response **must** be a structured JSON object where each **existing category** has its own detailed breakdown.

### **Instructions:**
1. **Extract unique log categories** present in the file:
   - **Server** (e.g., Web server failures, load balancer issues)
   - **Database** (e.g., slow queries, connection limits, replication lag)
   - **Application** (e.g., unhandled exceptions, crashes, memory leaks)
   - **System** (e.g., CPU overload, disk I/O bottlenecks, OS-level issues)
   - **Network** (e.g., timeouts, packet loss, high latency)

2. **For each detected category, return the following JSON structure:**
3. **Output the response in JSON format only.**
4. **Do not include any introductory text, explanations, or formatting outside the JSON structure.**
5.**give me just the result without writing tou thoughts**
```json
{{
  "CATEGORY_NAME": [
    {{
      "Root Cause": "Describe the exact root cause concisely.",
      "Log Classification": "CATEGORY_NAME",
      "Explanation": {{
        "Log Message": "Provide the critical error message from the log.",
        "Possible Causes": [
          "List all potential reasons for the issue."
        ],
        "Detailed Root Cause Analysis": {{
          "Observations": "Explain what patterns are observed in the log.",
          "Impact": "Describe how this issue affects the system or application.",
          "Correlations": "Link this issue to other logs or system components."
        }},
        "Conclusion": "Summarize why this is the most likely root cause."
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
root_cause_file = f"root_cause_analysis_{timestamp}.json"

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
                    self.queues[normalized_category].put(log_entry)
                    print(f"📤 Log envoyé à {normalized_category}Agent")
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
