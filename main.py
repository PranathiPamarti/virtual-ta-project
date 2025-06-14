import requests
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import faiss
import json
import uvicorn
import numpy as np
from sentence_transformers import SentenceTransformer
import os
import base64
from io import BytesIO
from PIL import Image

AIPIPE_LLM_URL = "https://aipipe.org/openai/v1/chat/completions"
AIPIPE_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjMwMDA1NzBAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.3W41cggvkH3l0poFK5wAYoxFKRZALaGWvaW4t4Y-pq0"

HEADERS = {
    "Authorization": AIPIPE_API_KEY,
    "Content-Type": "application/json"
}

# Load FAISS index and metadata
index = faiss.read_index("semantic_index.faiss")

with open("embedded_chunks.jsonl", "r") as f:
    embedded_chunks = [json.loads(line) for line in f if line.strip()]


with open("metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

# Load local embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Define request body structure
class QueryRequest(BaseModel):
    question: str
    image: Optional[str] = None  # base64 string

# Set up FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow any origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Semantic search logic
def get_relevant_chunks(question: str, k: int = 5) -> List[dict]:
    embedding = model.encode([question])[0].astype("float32")
    distances, indices = index.search(np.array([embedding]), k)
    results = []

    for idx in indices[0]:
        if idx < len(metadata):
            chunk_info = {
                "text": embedded_chunks[idx]["text"],
                "url": metadata[idx].get("url", ""),
                "title": metadata[idx].get("title", ""),
            }
            results.append(chunk_info)
    return results


# API endpoint
@app.post("/api/")
async def answer_query(query: QueryRequest):
    relevant_chunks = get_relevant_chunks(query.question, k=5)
    answer = synthesize_answer(query.question, relevant_chunks)
    

    links = [
        {"url": chunk["url"], "text": chunk["title"] or chunk["url"]}
        for chunk in relevant_chunks if chunk["url"]
    ]

    return {
        "answer": answer,
        "links": links
    }

# Run the app
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

def synthesize_answer(question: str, context_chunks: List[dict]) -> str:
    context = "\n\n".join(chunk["text"] for chunk in context_chunks)

    system_prompt = (
        "You are a helpful AI assistant answering student questions using the provided course materials. "
        "Use only the given context to answer. If the answer is not found, say 'I couldn't find an exact answer.'"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
    ]

    payload = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "temperature": 0.2
    }

    response = requests.post(AIPIPE_LLM_URL, headers=HEADERS, json=payload)

    if response.ok:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        return f"LLM error: {response.status_code} - {response.text}"

