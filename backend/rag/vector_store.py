import json
import pickle
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer

from config import INDEX_DIR


_MODEL_NAME = "paraphrase-MiniLM-L3-v2"
_model = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME, device="cpu")
        _model.max_seq_length = 128
    return _model

def _index_path() -> Path:
    return INDEX_DIR / "faiss.index"

def _meta_path() -> Path:
    return INDEX_DIR / "chunks_meta.pkl"

def _load_index() -> tuple[faiss.IndexFlatL2 | None, list]:
    if not _index_path().exists():
        return None, []
    index = faiss.read_index(str(_index_path()))
    with open(_meta_path(), "rb") as f:
        meta = pickle.load(f)
    return index, meta

def _save_index(index: faiss.IndexFlatL2, meta: list):
    faiss.write_index(index, str(_index_path()))
    with open(_meta_path(), "wb") as f:
        pickle.dump(meta, f)

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
    model = _get_model()
    index, meta = _load_index()

    all_chunks = []
    all_metas = []

    for page in pages:
        page_text = page.get("text", "").strip()
        if not page_text:
            continue
        chunks = _chunk_text(page_text)
        for chunk in chunks:
            all_chunks.append(chunk)
            all_metas.append({
                "doc_id": doc_id,
                "filename": filename,
                "page_num": page["page_num"],
                "image_path": page.get("image_path"),
                "text": chunk,
            })

    if not all_chunks:
        return

    embeddings = model.encode(all_chunks, show_progress_bar=False).astype("float32")
    dim = embeddings.shape[1]

    if index is None:
        index = faiss.IndexFlatL2(dim)

    index.add(embeddings)
    meta.extend(all_metas)
    _save_index(index, meta)

def search(query: str, top_k: int = 5) -> list[dict]:
    index, meta = _load_index()
    if index is None or index.ntotal == 0:
        return []

    model = _get_model()
    q_emb = model.encode([query]).astype("float32")
    distances, indices = index.search(q_emb, min(top_k, index.ntotal))

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0:
            continue
        chunk_meta = meta[idx].copy()
        chunk_meta["score"] = float(1 / (1 + dist))  # normalize to 0-1
        results.append(chunk_meta)

    # dedupe by (doc_id, page_num) keeping best score
    seen = {}
    for r in results:
        key = (r["doc_id"], r["page_num"])
        if key not in seen or r["score"] > seen[key]["score"]:
            seen[key] = r
    return list(seen.values())

def remove_document(doc_id: str):
    # FAISS flat index doesn't support deletion, so rebuild without that doc
    index, meta = _load_index()
    if index is None:
        return

    keep_meta = [m for m in meta if m["doc_id"] != doc_id]
    if not keep_meta:
        _index_path().unlink(missing_ok=True)
        _meta_path().unlink(missing_ok=True)
        return

    model = _get_model()
    texts = [m["text"] for m in keep_meta]
    embeddings = model.encode(texts, show_progress_bar=False).astype("float32")
    dim = embeddings.shape[1]
    new_index = faiss.IndexFlatL2(dim)
    new_index.add(embeddings)
    _save_index(new_index, keep_meta)
