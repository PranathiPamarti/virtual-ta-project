import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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
import pytesseract
from dotenv import load_dotenv
load_dotenv()

AIPIPE_API_KEY = os.getenv("AIPIPE_API_KEY")
AIPIPE_LLM_URL = "https://aipipe.org/openai/v1/chat/completions"

# Configure Tesseract path based on environment
if os.name == 'nt':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
else:  # Linux/Unix
    pytesseract.pytesseract.tesseract_cmd = 'tesseract'

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
model = SentenceTransformer("paraphrase-MiniLM-L3-v2")
model.max_seq_length = 128

# Define request body structure
class QueryRequest(BaseModel):
    question: str
    image: Optional[str] = None  # base64 string

# Set up FastAPI app
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Semantic search logic
def get_relevant_chunks(question: str, k: int = 5) -> List[dict]:
    try:
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
    except Exception as e:
        print(f"Error in semantic search: {e}")
        return []

def synthesize_answer(question: str, context_chunks: List[dict]) -> str:
    try:
        context = "\n\n".join(chunk["text"] for chunk in context_chunks)

        system_prompt = (
            "You are a helpful AI assistant answering student questions using the provided course materials. "
            "Use only the given context to answer. If the answer is not found, say 'I couldn't find an exact answer.' "
            "Be concise and accurate in your responses."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
        ]

        payload = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 500
        }

        response = requests.post(AIPIPE_LLM_URL, headers=HEADERS, json=payload)

        if response.ok:
            content = response.json()["choices"][0]["message"]["content"].strip()
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict) and "answer" in parsed:
                    return parsed
            except json.JSONDecodeError:
                pass
            return {"answer": content}
        else:
            return {"answer": f"Error: {response.status_code} - {response.text}"}
    except Exception as e:
        print(f"Error in answer synthesis: {e}")
        return {"answer": "Sorry, I encountered an error while processing your request."}

# API endpoint
@app.post("/api/")
async def answer_query(query: QueryRequest):
    try:
        # Step 1: Decode and load image if provided
        image_text = ""
        if query.image:
            try:
                # Check if it's a URL or base64
                if query.image.startswith("http://") or query.image.startswith("https://"):
                    response = requests.get(query.image)
                    image = Image.open(BytesIO(response.content))
                elif query.image.startswith("file://"):
                    local_path = query.image.replace("file://", "")
                    image = Image.open(local_path)
                else:
                    image_data = base64.b64decode(query.image)
                    image = Image.open(BytesIO(image_data))

                # Run OCR
                image_text = pytesseract.image_to_string(image)
                print("Extracted from image:", image_text)

            except Exception as e:
                print(f"Error processing image: {e}")
                image_text = ""

        # Combine image text with question
        full_question = query.question
        if image_text.strip():
            full_question += "\n\nText extracted from image:\n" + image_text
        
        relevant_chunks = get_relevant_chunks(full_question, k=5)
        answer = synthesize_answer(full_question, relevant_chunks)
        
        if isinstance(answer, dict) and "answer" in answer:
            answer = answer["answer"]

        links = [
            {"url": chunk["url"], "text": chunk["title"] or chunk["url"]}
            for chunk in relevant_chunks if chunk["url"]
        ]

        return {
            "answer": answer,
            "links": links
        }
    except Exception as e:
        print(f"Error in API endpoint: {e}")
        return {
            "answer": "Sorry, I encountered an error while processing your request.",
            "links": []
        }

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # default to 8000 for local
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

