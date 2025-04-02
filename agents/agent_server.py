from groq import Groq
import os
import datetime
import json,re
from serpapi import GoogleSearch
import time
from agno.agent import Agent
from multiprocessing import Queue
import sqlite3
import hashlib

from agents.RAG.server.rag_server import initialize_rag_chain, query_rag_chain

from dotenv import load_dotenv
load_dotenv()


class ServerAgent(Agent):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue
        self.logs_directory = "logs_processed_server"  # Dossier où enregistrer les logs
        self.recommendations_directory = "recommendations_server"  # Dossier pour les recommandations
        self.rag_chain = initialize_rag_chain("agents/RAG/server/server_doc.md")


        if not os.path.exists(self.logs_directory):
            os.makedirs(self.logs_directory)
        if not os.path.exists(self.recommendations_directory):
            os.makedirs(self.recommendations_directory)

        self.client = Groq(api_key="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")
        self.serp_api_key = "424558b7399112915fbefbb834dab8bb9c95d638623681c75decd9b9fd2a0100"

        
        #self.serp_api_key = "bccb5398af513a4b65beb318d3891c679fbe3ea71364e93af6f4643fac41b55d"

    def listen_for_logs(self):
        """Écoute les messages envoyés par HubAgent."""
        print("🚀 ServerAgent en attente de logs...")
        while True:
            if not self.queue.empty():
                message = self.queue.get()
                if isinstance(message, dict) and message.get("stop"):
                    print("🛑 Arrêt du ServerAgent.")
                    break  # Arrête proprement la boucle
                #print(f"🔹 Message reçu : {message}")
                self.receive_message(message)
            time.sleep(1)

    def receive_message(self, message):
        """Reçoit et traite un log."""
        if isinstance(message, dict):
            log_text = json.dumps(message, indent=2, ensure_ascii=False)  # Convertir en JSON formaté
            #print(f"📥 Log reçu par ServerAgent:\n{log_text}")
            self.process_log(message)  # Passer le dict directement

    def process_log(self, log_data):
            root_cause = log_data.get("Root Cause", "Inconnu")
            explanation = log_data.get("Explanation", {}).get("Analysis", "Aucune explication fournie.")
            print(f"⚙️ Traitement du log database - Cause: {root_cause}")
            
            self.save_log_report(log_data)
            recommendation = self.generate_recommendation(root_cause, explanation)
            self.save_recommendation(recommendation)

            # ✅ Génére le hash du log
            log_text = json.dumps(log_data, sort_keys=True, ensure_ascii=False)
            log_hash = hashlib.sha256(log_text.encode("utf-8")).hexdigest()

            # ✅ Sauvegarde en base
            self.save_to_db(log_text, root_cause, recommendation, log_hash)


    def save_log_report(self, log_data):
        """Sauvegarde le log traité dans un fichier JSON."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        log_filename = f"{self.logs_directory}/log_{timestamp}.json"

        with open(log_filename, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=4, ensure_ascii=False)

        print(f"✅ Log sauvegardé : {log_filename}")

    def search_google(self, query):
        """Effectue une recherche Google pour enrichir la recommandation."""
        params = {
            "q": query,
            "hl": "fr",
            "gl": "fr",
            "api_key": self.serp_api_key
        }
        search = GoogleSearch(params)
        results = search.get_dict()

        if "organic_results" not in results:
            print("⚠ Warning: Aucun résultat de recherche pertinent.")
            return []

        return results["organic_results"][:3]  

    def generate_recommendation(self, root_cause, explanation):
        """Génère une recommandation basée sur la cause du problème."""
        search_query = f"Comment résoudre {root_cause}? Explication: {explanation}"
        search_results = self.search_google(search_query)
        # Appel à RAG pour récupérer les infos internes
        rag_info = self.rag_chain.run(f"How to resolve this server issue: {root_cause}")


        if not search_results:
            top_results = "Aucun résultat pertinent trouvé."
        else:
            top_results = "\n".join([result.get("snippet", "Pas de description") for result in search_results])

        prompt_recommendation = f"""
        ### **Server Diagnostic**
        The system has identified the following root cause:
        **Root Cause:** "{root_cause}"

        ### **Log Analysis:**
        {explanation}

        ### **Internal Documentation (RAG Knowledge):**
        {rag_info if rag_info else "No internal knowledge retrieved."}

        ### **Web Results Overview:**
        {top_results}

        ### **Task:**
        As a **server expert**, your role is to:
        1. Use both internal documentation and web search results to recommend a solution.
        2. Provide a **structured technical recommendation** to fix the issue.
        3. Include detailed steps, tools, and best practices.
        4. **Limit your response to the top 2-3 most critical steps only.** These should be the highest-impact and most common actions to resolve the issue.

        5. Don’t include anything else other than the JSON recommendation.


        ### **Expected Format:**
        Respond **only** in JSON format: 
        ```json
        {{
            "Recommendation": {{
                "title": "Short Summary of the Solution",
                "steps": [
                    {{
                        "step": 1,
                        "action": "Describe the first troubleshooting step",
                        "tools": ["Relevant command/tool if applicable"],
                        "description": "Explain why this step is necessary."
                    }},
                    {{
                        "step": 2,
                        "action": "Describe the second troubleshooting step",
                        "tools": ["Another relevant command/tool"],
                        "description": "Explain why this step is necessary."
                    }}
                ]
            }}
        }}

                            ```
        """

        '''
        completion = self.client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt_recommendation}],
        temperature=0.3,
        max_tokens=1024,
        top_p=1,
        stream=False
        )
                '''
        
        completion = self.client.chat.completions.create(
            #model="llama3-70b-8192",
            #model="qwen-2.5-32b",
            #model="llama-3.3-70b-versatile",
            model="deepseek-r1-distill-llama-70b",
            messages=[{"role": "user", "content": prompt_recommendation}],
            temperature=0.6,
            max_tokens=4096,
            #response_format={"type": "json_object"},
            top_p=0.95
        )

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
        
        resp = completion.choices[0].message.content
        raw_data=extract_json(resp)
        
        
        
        
        





        
    

      
    






     

        try:
           
            parsed_recommendation =raw_data
            return parsed_recommendation
        except json.JSONDecodeError:
            print("❌ Erreur: Réponse LLM invalide.")
            return "Impossible de générer une recommandation."

    def clean_text(self, text):
        """Nettoie le JSON renvoyé par Groq."""
        lines = text.split("\n")
        result_lines = []
        for i, line in enumerate(lines[3:], start=3):
            if "```" in line:
                break
            result_lines.append(line)
        return "\n".join(result_lines)

    
    

   
    

    




    

    def save_recommendation(self, recommendation_text):
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        recommendation_filename = f"{self.recommendations_directory}/recommendation_{timestamp}.json"
        with open(recommendation_filename, "w", encoding="utf-8") as file:
            json.dump( recommendation_text, file, indent=4, ensure_ascii=False)
        print(f"✅ Recommandation sauvegardée : {recommendation_filename}")
    def save_to_db(self, log_text, root_cause, recommendation, log_hash):
            try:
                db_path = os.path.abspath("logs_memory.db")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT OR IGNORE INTO processed_logs_server (log, root_cause, recommendation, log_hash)
                    VALUES (?, ?, ?, ?)
                """, (log_text, root_cause, json.dumps(recommendation, ensure_ascii=False), log_hash))

                conn.commit()
                conn.close()
                print("💾 Log server enregistré en base avec succès.")

            except Exception as e:
                print(f"⚠️ Erreur lors de l'enregistrement en base : {e}")

import multiprocessing
if __name__ == "__main__":
    if multiprocessing.current_process().name == "MainProcess":
        log_queue = Queue()
        server_agent = ServerAgent(log_queue)
        server_agent.listen_for_logs()


        
