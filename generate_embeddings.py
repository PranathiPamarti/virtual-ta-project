from sentence_transformers import SentenceTransformer
import json
from tqdm import tqdm
import numpy as np

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Load chunks
chunks = []
with open("chunks.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        chunks.append(json.loads(line))

# Extract texts
texts = [chunk['text'] for chunk in chunks]

# Generate embeddings
print(" Generating embeddings...")
embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

# Save to file
with open("embedded_chunks.jsonl", "w", encoding="utf-8") as f:
    for chunk, vector in zip(chunks, embeddings):
        chunk["embedding"] = vector.tolist()
        f.write(json.dumps(chunk) + "\n")

print(f"Saved {len(chunks)} embeddings to embedded_chunks.jsonl")
