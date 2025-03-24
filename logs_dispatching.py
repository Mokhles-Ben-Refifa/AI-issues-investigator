import json
import subprocess
import sys
import re
from groq import Groq

sys.stdout.reconfigure(encoding='utf-8')

API_KEY = "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"
client = Groq(api_key=API_KEY)


input_log_file = r'C:\Users\Legion\Documents\AI issues investigator\logu.log'  

output_log_file = "dispatched_logs.log"


with open(input_log_file, "r", encoding="utf-8") as file:
    logs = file.read()

prompt = f"""
You are an expert in log analysis. Here are system logs:

{logs}

Analyze these logs and classify them into **clusters** based on similar errors or issues.
Return only a JSON output, with no additional explanations or text before/after, in the following format:
{{
  "clusters": [
    {{
      "id": 0,
      "description": "Database connection issues",
      "logs": [
        "2024-03-12 10:15:10 ERROR Failed to connect to database: Connection refused",
        "2024-03-12 10:15:11 ERROR Retrying database connection...",
        "2024-03-12 10:15:12 ERROR Connection failed again: Host unreachable"
      ]
    }},
    {{
      "id": 1,
      "description": "Worker process memory issues",
      "logs": [
        "2024-03-12 10:16:05 ERROR Worker process crashed due to memory limit exceeded",
        "2024-03-12 10:16:10 INFO Worker process restarted successfully"
      ]
    }}
  ]
}}

Do not include **anything** other than the JSON.
"""


try:
   
    response = client.chat.completions.create(
        model="deepseek-r1-distill-llama-70b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=4096,
        top_p=0.95
    )

    
    content = response.choices[0].message.content.strip()

    
    match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
    json_content = match.group(1) if match else content

 
    log_clusters = json.loads(json_content)

    with open(output_log_file, "w", encoding="utf-8") as file:
        json.dump(log_clusters, file, indent=2, ensure_ascii=False)

    print(f"✅ Logs dispatched and saved to {output_log_file}")

except Exception as e:
    print(f"⚠️ Erreur lors de la requête Groq : {str(e)}")

try:
    print("🚀 Starting hub.py...")
    subprocess.run(["python", "hub.py"])  
except Exception as e:
    print(f"⚠️ Failed to start hub.py: {str(e)}")
