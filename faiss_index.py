import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer

# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Load embedded data
with open("embedded_chunks.jsonl", "r", encoding="utf-8") as f:
    data = [json.loads(line) for line in f]

texts = [item["text"] for item in data]
embeddings = np.array([item["embedding"] for item in data], dtype="float32")

# Build FAISS index
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# Save the index
faiss.write_index(index, "semantic_index.faiss")

# Save metadata for lookup
with open("metadata.json", "w", encoding="utf-8") as f:
    json.dump(data, f)

print(f" FAISS index built with {len(embeddings)} vectors.")
