import json
from pathlib import Path
from config import INDEX_DIR

_REGISTRY_PATH = INDEX_DIR / "registry.json"

def _load() -> dict:
    if not _REGISTRY_PATH.exists():
        return {}
    return json.loads(_REGISTRY_PATH.read_text())

def _save(data: dict):
    _REGISTRY_PATH.write_text(json.dumps(data, indent=2))

def register_document(doc_id: str, record: dict):
    data = _load()
    data[doc_id] = record
    _save(data)

def get_document(doc_id: str) -> dict | None:
    return _load().get(doc_id)

def list_documents() -> list[dict]:
    data = _load()
    return [{"doc_id": k, **v} for k, v in data.items()]

def update_document_status(doc_id: str, status: str, extra: dict | None = None):
    data = _load()
    if doc_id not in data:
        return
    data[doc_id]["status"] = status
    if extra:
        data[doc_id].update(extra)
    _save(data)

def delete_document(doc_id: str):
    data = _load()
    data.pop(doc_id, None)
    _save(data)

def document_exists_by_hash(file_hash: str) -> str | None:
    # returns doc_id if duplicate, None otherwise
    for doc_id, v in _load().items():
        if v.get("file_hash") == file_hash:
            return doc_id
    return None
