import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer

# Load model and data
model = SentenceTransformer("all-MiniLM-L6-v2")
index = faiss.read_index("semantic_index.faiss")

with open("metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

# Search function
def search(query, k=5):
    query_vec = model.encode([query], convert_to_numpy=True).astype("float32")
    distances, indices = index.search(query_vec, k)
    results = []
    for i in indices[0]:
        if i < len(metadata):
            results.append(metadata[i])
    return results


if __name__ == "__main__":
    query = "How do I deploy to Vercel?"
    results = search(query, k=3)

    for i, res in enumerate(results, 1):
        print(f"\nResult #{i}")
        print("Title:", res.get('title'))
        print("URL:", res.get('url'))
        print("Text:", res.get('text')[:300], "...")
