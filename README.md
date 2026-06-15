# Document Intelligence + Agentic RAG

A full-stack pipeline that ingests messy real-world documents, classifies them, and powers a chatbot with grounded citations and page thumbnails.

---

## Stack

- **Backend**: Python, FastAPI, uvicorn
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Parsing**: pdfplumber, pdf2image, pytesseract (Tesseract OCR)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2, runs locally, free)
- **Vector store**: FAISS (CPU, in-process, no server needed)
- **LLM (classify + RAG)**: Anthropic Claude 3.5 Haiku via API (free tier available)
- **Security**: python-magic, slowapi, bleach, passlib, jose

---

## Tools Used & How to Install Them

### System dependencies

```bash
# Ubuntu / Debian
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils libmagic1

# macOS (Homebrew)
brew install tesseract poppler libmagic
```

| Tool | Purpose |
|------|---------|
| `tesseract-ocr` | OCR engine used by pytesseract |
| `poppler-utils` | Provides `pdftoppm` used by pdf2image to render PDF pages |
| `libmagic` | MIME-type detection for upload security |

### Python packages

```bash
cd backend
pip install -r requirements.txt
```

| Package | Purpose |
|---------|---------|
| `fastapi` | REST API framework |
| `uvicorn` | ASGI server |
| `pdfplumber` | Extract text + tables from PDFs |
| `pdf2image` | Render PDF pages to images (wraps poppler) |
| `pytesseract` | Python wrapper for Tesseract OCR |
| `Pillow` | Image manipulation |
| `sentence-transformers` | Local text embeddings (no API key needed) |
| `faiss-cpu` | Vector similarity search |
| `anthropic` | Claude API client (classify + RAG synthesis) |
| `python-dotenv` | Load `.env` variables |
| `slowapi` | Rate limiting for FastAPI |
| `python-magic` | MIME-type checking from file bytes |
| `cryptography` | Used by jose / passlib |

### Node packages (frontend)

```bash
cd frontend
npm install
```

| Package | Purpose |
|---------|---------|
| `next` | React framework (SSR + file routing) |
| `axios` | HTTP client for API calls |
| `lucide-react` | Icon library |
| `clsx` | Conditional className utility |
| `tailwindcss` | Utility-first CSS |

---

## Setup & Running

### 1. Clone and configure

```bash
cp backend/.env.example backend/.env
# Edit backend/.env and add your ANTHROPIC_API_KEY
```

Get a free Anthropic API key at https://console.anthropic.com

### 2. Install system dependencies

```bash
# Ubuntu
sudo apt-get install -y tesseract-ocr poppler-utils libmagic1
```

### 3. Install Python dependencies

```bash
cd backend
pip install -r requirements.txt
```

Note: On first run, sentence-transformers will download the `all-MiniLM-L6-v2` model (~90MB) automatically.

### 4. Start the backend

```bash
cd backend
python run.py
# API is now running at http://localhost:8000
```

### 5. Install and start the frontend

```bash
cd frontend
npm install
npm run dev
# UI is now running at http://localhost:3000
```

### 6. Seed sample documents (optional but recommended for first run)

```bash
# in a new terminal, with the backend already running
pip install reportlab
python scripts/seed_samples.py
```

This creates 5 sample PDFs (financial report, employee handbook, AI research, product spec, climate policy) and uploads them. Wait ~30 seconds for processing, then chat.

---

## Folder Structure

```
doc-intelligence/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py            # FastAPI routes (upload, chat, document CRUD, page images)
│   ├── classifier/
│   │   ├── __init__.py
│   │   └── document_classifier.py  # LLM-based classification → structured JSON
│   ├── parser/
│   │   ├── __init__.py
│   │   └── document_parser.py # PDF/image/text parsing with OCR fallback
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── rag_agent.py       # RAG answer generation with inline citations
│   │   └── vector_store.py    # FAISS indexing, chunking, similarity search
│   ├── security/
│   │   ├── __init__.py
│   │   └── validators.py      # File validation, MIME check, path sanitization
│   ├── utils/
│   │   ├── __init__.py
│   │   └── registry.py        # JSON-backed document registry (status, metadata)
│   ├── config.py              # Centralised config from .env
│   ├── requirements.txt
│   ├── run.py                 # Entry point
│   └── .env.example
│
├── frontend/
│   ├── components/
│   │   ├── api.ts             # Typed API client
│   │   ├── Layout.tsx         # Nav + shell
│   │   └── PageThumb.tsx      # Clickable thumbnail with full-page modal
│   ├── pages/
│   │   ├── _app.tsx
│   │   ├── index.tsx          # Landing page
│   │   ├── upload.tsx         # Bulk upload + live status per file
│   │   └── chat.tsx           # Chat UI with citations, thumbnails, voice input
│   ├── styles/
│   │   └── globals.css
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── package.json
│
├── scripts/
│   └── seed_samples.py        # Generates 5 sample PDFs and uploads them
│
└── README.md
```

Runtime directories created automatically:

```
backend/
├── uploads/          # raw uploaded files, one subfolder per doc_id
├── pages/            # rendered page JPEGs, one subfolder per doc_id
└── indexes/
    ├── faiss.index   # FAISS vector index
    ├── chunks_meta.pkl  # chunk metadata (doc_id, page, text)
    └── registry.json    # document status and classification store
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/documents/upload` | Upload a document (multipart/form-data) |
| GET | `/documents` | List all documents with status |
| GET | `/documents/{id}` | Get single document info + classification |
| DELETE | `/documents/{id}` | Remove document from index and disk |
| GET | `/documents/{id}/page/{n}/image` | Get rendered page image (JPEG) |
| POST | `/chat` | RAG query with conversation history |
| GET | `/health` | Health check |

---

## Security Decisions

### What was implemented

**Upload layer**
- File size limit enforced before saving (50MB default, configurable)
- Extension allowlist (pdf, png, jpg, jpeg, tiff, txt)
- MIME-type validation via `python-magic` — checks actual file bytes, not just the extension — prevents disguised executables
- Filename sanitization: strips path separators, control characters, and truncates to 100 chars
- Path traversal prevention: resolved paths are checked to remain under the upload root

**Storage layer**
- Each document gets an isolated UUID subdirectory — no shared namespace between uploads
- Page images are served through a validated route that re-checks doc_id format (UUID regex) and page number range before building the file path
- FAISS index and metadata are stored outside the web root

**Processing layer**
- Documents are parsed in background tasks — upload returns immediately; no synchronous processing holds the request open
- Duplicate detection via SHA-256 file hash to avoid re-indexing identical files

**API / retrieval layer**
- CORS is restricted to `ALLOWED_ORIGINS` (configured via env)
- Rate limiting via `slowapi` (20 req/minute per IP, configurable)
- Query length is capped at 2000 chars
- Conversation history is limited to last 6 turns to prevent prompt injection via long histories

### Considered but skipped (would add given more time)

- **Authentication / multi-tenancy**: No user accounts. All uploaded docs are shared. Would add JWT auth so each user only sees their own documents.
- **Encrypted storage at rest**: Files are stored as-is on disk. Would encrypt with a per-document key derived from a master secret.
- **Virus scanning**: ClamAV integration on upload before parsing.
- **Secrets in a vault**: Currently read from `.env`. Would use HashiCorp Vault or AWS Secrets Manager in production.
- **Audit logging**: No log of who uploaded or queried what. Would add structured logging with user context.
- **Input sanitization for LLM prompts**: Basic length limiting is done. Would add more robust prompt injection detection.
