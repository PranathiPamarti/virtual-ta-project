import json
from pathlib import Path
from typing import List

# --- CONFIG ---
INPUT_FILES = ["anand_scraped.jsonl", "discourse_posts.jsonl"]
OUTPUT_FILE = "chunks.jsonl"
CHUNK_SIZE = 300  # Number of words
CHUNK_OVERLAP = 50  # Number of words to overlap between chunks

# --- FUNCTION ---
def split_text(text: str, size: int, overlap: int) -> List[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), size - overlap):
        chunk = words[i:i + size]
        if chunk:
            chunks.append(" ".join(chunk))
    return chunks

# --- MAIN ---
all_chunks = []

for file_path in INPUT_FILES:
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                doc = json.loads(line)
                content = doc.get("content") or doc.get("text") or ""
                title = doc.get("title", "Unknown")
                url = doc.get("url", None)
                if not content.strip():
                    continue

                for chunk in split_text(content, CHUNK_SIZE, CHUNK_OVERLAP):
                    chunk_obj = {
                        "text": chunk,
                        "title": title,
                        "url": url
                    }
                    all_chunks.append(chunk_obj)
            except json.JSONDecodeError:
                continue

# --- SAVE OUTPUT ---
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for chunk in all_chunks:
        f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

print(f" Done. Wrote {len(all_chunks)} chunks to {OUTPUT_FILE}")
