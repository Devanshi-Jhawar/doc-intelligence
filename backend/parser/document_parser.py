import io
import uuid
import hashlib
from pathlib import Path
from typing import Optional
import pdfplumber
import pkgutil
if not hasattr(pkgutil, 'find_loader'):
    pkgutil.find_loader = lambda name: None
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

from config import PAGES_DIR

# each page result: {page_num, text, image_path, doc_id}

def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def parse_pdf(file_path: Path, doc_id: str) -> list[dict]:
    pages = []
    doc_pages_dir = PAGES_DIR / doc_id
    doc_pages_dir.mkdir(parents=True, exist_ok=True)

    # render all pages to images first (used for thumbnails + OCR fallback)
    rendered = convert_from_path(str(file_path), dpi=150, fmt="jpeg")

    with pdfplumber.open(file_path) as pdf:
        for i, plumber_page in enumerate(pdf.pages):
            page_num = i + 1
            text = plumber_page.extract_text() or ""

            # if pdfplumber got nothing useful, fall back to tesseract
            if len(text.strip()) < 30:
                text = pytesseract.image_to_string(rendered[i])

            # save page image
            img_path = doc_pages_dir / f"page_{page_num}.jpg"
            rendered[i].save(str(img_path), "JPEG", quality=85)

            # also extract tables if any
            tables = plumber_page.extract_tables() or []
            table_text = ""
            for tbl in tables:
                for row in tbl:
                    table_text += " | ".join(str(c or "") for c in row) + "\n"
            if table_text:
                text += "\n\n[TABLE]\n" + table_text

            pages.append({
                "page_num": page_num,
                "text": text.strip(),
                "image_path": str(img_path),
                "doc_id": doc_id,
            })

    return pages

def parse_image(file_path: Path, doc_id: str) -> list[dict]:
    doc_pages_dir = PAGES_DIR / doc_id
    doc_pages_dir.mkdir(parents=True, exist_ok=True)

    img = Image.open(file_path).convert("RGB")
    text = pytesseract.image_to_string(img)

    img_path = doc_pages_dir / "page_1.jpg"
    img.save(str(img_path), "JPEG", quality=85)

    return [{
        "page_num": 1,
        "text": text.strip(),
        "image_path": str(img_path),
        "doc_id": doc_id,
    }]

def parse_text(file_path: Path, doc_id: str) -> list[dict]:
    # plain text - treat as single page, no image
    text = file_path.read_text(errors="replace")
    return [{
        "page_num": 1,
        "text": text.strip(),
        "image_path": None,
        "doc_id": doc_id,
    }]

def parse_document(file_path: Path, original_filename: str) -> dict:
    doc_id = str(uuid.uuid4())
    suffix = Path(original_filename).suffix.lower()
    file_hash = _hash_file(file_path)

    if suffix == ".pdf":
        pages = parse_pdf(file_path, doc_id)
    elif suffix in {".png", ".jpg", ".jpeg", ".tiff"}:
        pages = parse_image(file_path, doc_id)
    elif suffix == ".txt":
        pages = parse_text(file_path, doc_id)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    full_text = "\n\n".join(p["text"] for p in pages if p["text"])

    return {
        "doc_id": doc_id,
        "filename": original_filename,
        "file_hash": file_hash,
        "num_pages": len(pages),
        "pages": pages,
        "full_text": full_text,
    }
