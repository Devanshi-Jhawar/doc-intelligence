import hashlib
import re
from pathlib import Path
from fastapi import UploadFile, HTTPException
import filetype

from config import ALLOWED_MIME_TYPES, ALLOWED_EXTENSIONS, MAX_FILE_SIZE, UPLOAD_DIR

# --- Upload layer security ---

DANGEROUS_PATTERNS = re.compile(
    r"\.\.(\/|\\)|"  # path traversal
    r"[\x00-\x1f\x7f]|"  # control chars
    r"[<>:\"|?*]"  # invalid filename chars
)

def sanitize_filename(name: str) -> str:
    name = Path(name).name  # strip directory components
    name = DANGEROUS_PATTERNS.sub("_", name)
    # limit length
    stem = Path(name).stem[:100]
    suffix = Path(name).suffix[:10]
    return stem + suffix

async def validate_upload(file: UploadFile) -> bytes:
    # read with size limit
    data = await file.read(MAX_FILE_SIZE + 1)
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(413, f"File too large. Max {MAX_FILE_SIZE // 1048576}MB.")

    # check extension
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File type {suffix} not allowed.")

    kind = filetype.guess(data[:2048])
    mime = kind.mime if kind else "text/plain"
    if mime not in ALLOWED_MIME_TYPES:
        if not (suffix == ".txt"):
            raise HTTPException(status_code=400, detail=f"File content type {mime} not allowed.")

    return data

def safe_upload_path(doc_id: str, filename: str) -> Path:
    clean_name = sanitize_filename(filename)
    dest = UPLOAD_DIR / doc_id
    dest.mkdir(parents=True, exist_ok=True)
    final = (dest / clean_name).resolve()
    # ensure it's still under UPLOAD_DIR (no traversal)
    if not str(final).startswith(str(UPLOAD_DIR.resolve())):
        raise HTTPException(400, "Invalid file path.")
    return final

# --- Storage layer: serve page images securely ---

def safe_page_path(doc_id: str, page_num: int, pages_dir: Path) -> Path:
    # validate doc_id is a uuid-like string (no path traversal)
    if not re.fullmatch(r"[0-9a-f\-]{36}", doc_id):
        raise HTTPException(400, "Invalid document ID.")
    if page_num < 1 or page_num > 9999:
        raise HTTPException(400, "Invalid page number.")

    path = (pages_dir / doc_id / f"page_{page_num}.jpg").resolve()
    if not str(path).startswith(str(pages_dir.resolve())):
        raise HTTPException(400, "Access denied.")
    if not path.exists():
        raise HTTPException(404, "Page image not found.")
    return path
