import requests
import json

API_URL = "https://aipipe.org/openai/v1/embeddings"
API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjMwMDA1NzBAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.3W41cggvkH3l0poFK5wAYoxFKRZALaGWvaW4t4Y-pq0"  # DO NOT put "Bearer " before it unless specified

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
