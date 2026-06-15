import json
import pickle
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import INDEX_DIR

_INDEX_PATH = INDEX_DIR / "tfidf.pkl"

def _load_index():
    if not _INDEX_PATH.exists():
        return None, []
    with open(_INDEX_PATH, "rb") as f:
        return pickle.load(f)

def _save_index(vectorizer, matrix, meta):
    with open(_INDEX_PATH, "wb") as f:
        pickle.dump((vectorizer, matrix, meta), f)

def _chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

def index_document(doc_id: str, filename: str, pages: list[dict]):
    result = _load_index()
    if result[0] is None:
        existing_meta = []
        existing_texts = []
    else:
        _, _, existing_meta = result
        existing_texts = [m["text"] for m in existing_meta]

    new_chunks = []
    new_metas = []
    for page in pages:
        text = page.get("text", "").strip()
        if not text:
            continue
        for chunk in _chunk_text(text):
            new_chunks.append(chunk)
            new_metas.append({
                "doc_id": doc_id,
                "filename": filename,
                "page_num": page["page_num"],
                "image_path": page.get("image_path"),
                "text": chunk,
            })

    if not new_chunks:
        return

    all_texts = existing_texts + new_chunks
    all_meta = existing_meta + new_metas

    vectorizer = TfidfVectorizer(max_features=10000, stop_words="english")
    matrix = vectorizer.fit_transform(all_texts)
    _save_index(vectorizer, matrix, all_meta)

def search(query: str, top_k: int = 5) -> list[dict]:
    result = _load_index()
    if result[0] is None:
        return []
    vectorizer, matrix, meta = result

    q_vec = vectorizer.transform([query])
    scores = cosine_similarity(q_vec, matrix)[0]
    top_indices = np.argsort(scores)[::-1][:top_k * 2]

    seen = {}
    for idx in top_indices:
        if scores[idx] < 0.01:
            continue
        m = meta[idx].copy()
        m["score"] = float(scores[idx])
        key = (m["doc_id"], m["page_num"])
        if key not in seen or m["score"] > seen[key]["score"]:
            seen[key] = m

    return list(seen.values())[:top_k]

def remove_document(doc_id: str):
    result = _load_index()
    if result[0] is None:
        return
    _, _, meta = result
    keep = [m for m in meta if m["doc_id"] != doc_id]
    if not keep:
        _INDEX_PATH.unlink(missing_ok=True)
        return
    texts = [m["text"] for m in keep]
    vectorizer = TfidfVectorizer(max_features=10000, stop_words="english")
    matrix = vectorizer.fit_transform(texts)
    _save_index(vectorizer, matrix, keep)