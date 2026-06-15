import asyncio
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request

from config import ALLOWED_ORIGINS, PAGES_DIR, UPLOAD_DIR, RATE_LIMIT
from security import validate_upload, safe_upload_path, safe_page_path
from parser import parse_document
from classifier import classify_document
from rag import answer_question, index_document, remove_document
from utils.registry import (
    register_document, get_document, list_documents,
    update_document_status, delete_document, document_exists_by_hash,
)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Document Intelligence API", version="1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
    allow_credentials=False,
)

# serve page thumbnails as static files (with path validation at the route level)
app.mount("/pages", StaticFiles(directory=str(PAGES_DIR)), name="pages")


# --- background processing pipeline ---

async def _process_document(doc_id: str, file_path: Path, filename: str):
    try:
        update_document_status(doc_id, "parsing")
        loop = asyncio.get_event_loop()

        parsed = await loop.run_in_executor(None, parse_document, file_path, filename)

        update_document_status(doc_id, "classifying")
        classification = await loop.run_in_executor(None, classify_document, parsed)

        update_document_status(doc_id, "indexing")
        await loop.run_in_executor(None, index_document, doc_id, filename, parsed["pages"])

        update_document_status(doc_id, "ready", {
            "classification": classification,
            "num_pages": parsed["num_pages"],
            "file_hash": parsed["file_hash"],
        })

    except Exception as e:
        update_document_status(doc_id, "error", {"error_msg": str(e)})


# --- routes ---

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/documents/upload")
@limiter.limit(RATE_LIMIT)
async def upload_document(request: Request, file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    data = await validate_upload(file)
    from security.validators import sanitize_filename
    clean_name = sanitize_filename(file.filename or "upload")

    # quick dedup check (parse won't run yet, check later post-parse)
    import uuid
    doc_id = str(uuid.uuid4())

    dest = safe_upload_path(doc_id, clean_name)
    dest.write_bytes(data)

    register_document(doc_id, {
        "filename": clean_name,
        "status": "queued",
        "uploaded_at": datetime.utcnow().isoformat(),
        "num_pages": None,
        "classification": None,
        "file_hash": None,
        "error_msg": None,
    })

    background_tasks.add_task(_process_document, doc_id, dest, clean_name)
    return {"doc_id": doc_id, "filename": clean_name, "status": "queued"}

@app.get("/documents")
def get_documents():
    return list_documents()

@app.get("/documents/{doc_id}")
def get_document_info(doc_id: str):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return {"doc_id": doc_id, **doc}

@app.delete("/documents/{doc_id}")
def delete_doc(doc_id: str):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    # remove files
    upload_dir = UPLOAD_DIR / doc_id
    pages_dir = PAGES_DIR / doc_id
    shutil.rmtree(upload_dir, ignore_errors=True)
    shutil.rmtree(pages_dir, ignore_errors=True)

    remove_document(doc_id)
    delete_document(doc_id)
    return {"deleted": doc_id}

@app.get("/documents/{doc_id}/page/{page_num}/image")
def get_page_image(doc_id: str, page_num: int):
    # safe_page_path validates both inputs before serving
    path = safe_page_path(doc_id, page_num, PAGES_DIR)
    return FileResponse(path, media_type="image/jpeg")


class ChatRequest(BaseModel):
    query: str
    history: list[dict[str, Any]] = []

@app.post("/chat")
@limiter.limit(RATE_LIMIT)
async def chat(request: Request, body: ChatRequest):
    if not body.query.strip():
        raise HTTPException(400, "Query cannot be empty")
    if len(body.query) > 2000:
        raise HTTPException(400, "Query too long (max 2000 chars)")

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, answer_question, body.query, body.history
    )
    return result
