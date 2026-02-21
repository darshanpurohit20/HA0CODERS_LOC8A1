import requests
import json

# Replace this with Seth's actual IP address
SETHS_IP = "10.120.101.22" 
OLLAMA_URL = f"http://{SETHS_IP}:11434/api/generate"

def ask_seths_llama(prompt):
    payload = {
        "model": "llama3",  # Ensure Seth has this model downloaded
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()['response']
    except requests.exceptions.ConnectionError:
        return "Error: Cannot reach Seth's PC. Check the IP or Firewall."

# Test it
print(ask_seths_llama("Analyze this news: Import taxes on steel have risen by 5%."))