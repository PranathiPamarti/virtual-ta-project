import requests
import json
from dotenv import load_dotenv
load_dotenv()

import os
API_KEY = os.getenv("AIPIPE_API_KEY")
API_URL = "https://aipipe.org/openai/v1/embeddings"

headers = {
    "Authorization": API_KEY,
    "Content-Type": "application/json"
}

data = {
    "model": "text-embedding-3-small",
    "input": "What is 2 + 2?"
}

response = requests.post(API_URL, headers=headers, data=json.dumps(data))

if response.ok:
    embedding = response.json()["data"][0]["embedding"]
    print(" Success. First 5 dimensions of embedding:", embedding[:5])
else:
    print("Error:", response.status_code, response.text)
