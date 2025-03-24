from groq import Groq
import os
import datetime
import json,re
from serpapi import GoogleSearch
import time
from agno.agent import Agent
from multiprocessing import Queue

class SystemAgent(Agent):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue
        self.logs_directory = "logs_processed_system"
        self.recommendations_directory = "recommendations_system"

        os.makedirs(self.logs_directory, exist_ok=True)
        os.makedirs(self.recommendations_directory, exist_ok=True)

        self.client = Groq(api_key="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")
        #self.serp_api_key = "424558b7399112915fbefbb834dab8bb9c95d638623681c75decd9b9fd2a0100"

        
        self.serp_api_key = "bccb5398af513a4b65beb318d3891c679fbe3ea71364e93af6f4643fac41b55d"

    def listen_for_logs(self):
        print("🚀 SystemAgent en attente de logs...")
        while True:
            if not self.queue.empty():
                message = self.queue.get()
                if isinstance(message, dict) and message.get("stop"):
                    print("🛑 Arrêt du SystemAgent.")
                    break
                self.receive_message(message)
            time.sleep(1)

    def receive_message(self, message):
        if isinstance(message, dict):
            self.process_log(message)

    def process_log(self, log_data):
        root_cause = log_data.get("Root Cause", "Inconnu")
        explanation = log_data.get("Explanation", {}).get("Analysis", "Aucune explication fournie.")
        print(f"⚙️ Traitement du log system - Cause: {root_cause}")
        self.save_log_report(log_data)
        recommendation = self.generate_recommendation(root_cause, explanation)
        self.save_recommendation(recommendation)

    def save_log_report(self, log_data):
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        log_filename = f"{self.logs_directory}/log_{timestamp}.json"
        with open(log_filename, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=4, ensure_ascii=False)
        print(f"✅ Log sauvegardé : {log_filename}")

    def search_google(self, query):
        params = {"q": query, "hl": "fr", "gl": "fr", "api_key": self.serp_api_key}
        search = GoogleSearch(params)
        results = search.get_dict()
        return results.get("organic_results", [])[:3]

    def generate_recommendation(self, root_cause, explanation):
        search_query = f"Comment résoudre {root_cause}? Explication: {explanation}"
        search_results = self.search_google(search_query)

        if not search_results:
            top_results = "Aucun résultat pertinent trouvé."
        else:
            top_results = "\n".join([result.get("snippet", "Pas de description") for result in search_results])

        prompt_recommendation = f"""
                    ### **System Diagnostic**
                    The system has identified the following root cause:
                    **Root Cause:** "{root_cause}"

                    ### **Log Analysis:**
                    {explanation}

                    ### **Task:**
                    As a **system expert**, your role is to:
                    1. Identify the detected failure or anomaly in the **system component**.
                    2. Provide a **detailed technical recommendation** to resolve the issue.
                    3. If no immediate solution is available, suggest **advanced diagnostic steps** (e.g., log verification, hardware tests, system commands).
                    4. Reference best practices and commonly used tools (e.g., `dmesg`, `journalctl`, `syslog`).
                    5. replace /n with return to new line 

                    ### **Web Results Overview:**
                    {top_results}

                    ### **Expected Format:**
                    Respond only in JSON:
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
                                }},
                                ...
                            ]
                        }}
                    }}

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
        raw_data1=extract_json(resp)
        
        def format_recommendation(recommendation_text):
            """
            Formats the recommendation text by properly aligning new lines with indentation.

            Args:
                recommendation_text (str or dict): The recommendation text.

            Returns:
                dict: Formatted recommendation text in JSON-compatible format.
            """
            if isinstance(recommendation_text, dict) and "Recommendation" in recommendation_text:
                text = recommendation_text["Recommendation"]
            elif isinstance(recommendation_text, str):
                text = recommendation_text
            else:
                return {"Recommendation": ""}  

           
            lines = text.split("\n")
            formatted_text = "".join(["\\n" + line if i > 0 else line for i, line in enumerate(lines)])

            return {"Recommendation": formatted_text}
        
        def format_and_save_recommendation(recommendation_text):
                """
                Splits recommendation text into separate lines and saves it as a structured JSON file.

                Args:
                    recommendation_text (str or dict): The recommendation text.
                    save_directory (str): Directory where the file should be saved.

                Returns:
                    str: Path of the saved JSON file.
                """
                if isinstance(recommendation_text, dict) and "Recommendation" in recommendation_text:
                    text = recommendation_text["Recommendation"]
                elif isinstance(recommendation_text, str):
                    text = recommendation_text
                else:
                    return None 

                
                lines = text.split("\n")
                formatted_data = {"Recommendation": lines}
                return formatted_data
        





        
        raw_data=format_and_save_recommendation(raw_data1)

      
    






        print(raw_data)

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

if __name__ == "__main__":
    log_queue = Queue()
    system_agent = SystemAgent(log_queue)
    system_agent.listen_for_logs()
