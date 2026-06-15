import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-prod")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
INDEX_DIR = Path(os.getenv("INDEX_DIR", "./indexes"))
PAGES_DIR = Path(os.getenv("PAGES_DIR", "./pages"))
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 52428800))
RATE_LIMIT = os.getenv("RATE_LIMIT_PER_MINUTE", "20/minute")

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/tiff",
    "text/plain",
}
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".txt"}

# create dirs on import
for d in [UPLOAD_DIR, INDEX_DIR, PAGES_DIR]:
    d.mkdir(parents=True, exist_ok=True)
