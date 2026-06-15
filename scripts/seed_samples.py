#!/usr/bin/env python3
"""
Creates 5 sample text-based PDFs and uploads them to the running backend.
Run: python seed_samples.py
Requires: pip install requests reportlab
"""
import io
import sys
import time
import requests

API = "http://localhost:8000"

# we use reportlab to generate real PDFs on the fly
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except ImportError:
    print("Installing reportlab...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab", "--break-system-packages", "-q"])
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas


def make_pdf(title: str, pages: list[str]) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    for page_text in pages:
        c.setFont("Helvetica-Bold", 16)
        c.drawString(72, 740, title)
        c.setFont("Helvetica", 11)
        y = 710
        for line in page_text.splitlines():
            if y < 80:
                c.showPage()
                c.setFont("Helvetica", 11)
                y = 740
            c.drawString(72, y, line)
            y -= 16
        c.showPage()
    c.save()
    return buf.getvalue()


SAMPLES = [
    (
        "Q1_Financial_Report_2024.pdf",
        "Q1 Financial Report 2024",
        [
            """Executive Summary

Total Revenue: $4.2M (up 18% YoY)
Net Profit: $890K
Operating Expenses: $3.1M
EBITDA Margin: 22%

Key Highlights:
- North America segment grew 24% driven by enterprise contracts
- EMEA region saw 12% growth despite macro headwinds
- Product line A contributed 58% of total revenue
- New customer acquisitions: 142 (target was 120)""",
            """Segment Breakdown

North America: $2.1M revenue, 340 active customers
Europe: $1.3M revenue, 210 active customers
Asia Pacific: $0.8M revenue, 95 active customers

Cost of Goods Sold: $1.4M
Gross Margin: 66.7%

Risk Factors:
- Supply chain disruptions may affect Q2 margins
- Currency fluctuations in EMEA pose ~5% revenue risk
- Planned headcount additions expected to raise OpEx 8% in Q2""",
        ],
    ),
    (
        "Employee_Handbook_2024.pdf",
        "Employee Handbook — Acme Corp",
        [
            """Welcome to Acme Corp

This handbook describes our policies, benefits, and expectations.

Work Hours: Core hours are 10am–4pm local time. Flexible schedule available.
Remote Work: Up to 3 days per week remote allowed after 90-day probation.
Paid Time Off: 20 days PTO annually, accrued monthly.
Sick Leave: 10 days per year, no carry-over.
Parental Leave: 16 weeks paid for primary caregivers, 8 weeks secondary.""",
            """Code of Conduct

All employees must:
1. Treat colleagues with respect regardless of background.
2. Disclose conflicts of interest immediately.
3. Protect confidential company and customer information.
4. Report violations via the anonymous ethics hotline: 1-800-555-0199.

Disciplinary Actions:
Verbal warning → Written warning → Performance Improvement Plan → Termination.
Severe violations (harassment, fraud, data theft) may result in immediate termination.""",
        ],
    ),
    (
        "AI_Research_Overview.pdf",
        "AI Research Overview — NeuraTech Labs",
        [
            """Introduction to Large Language Models

Large language models (LLMs) are neural networks trained on vast text corpora
using self-supervised objectives. The transformer architecture, introduced in
'Attention Is All You Need' (Vaswani et al., 2017), underpins most modern LLMs.

Key capabilities: text generation, summarization, code synthesis,
question answering, and multi-step reasoning.

Scaling laws (Kaplan et al., 2020) show that model performance improves
predictably with increased compute, parameters, and training data.""",
            """Retrieval-Augmented Generation (RAG)

RAG combines parametric knowledge (stored in model weights) with
non-parametric retrieval from an external corpus. Steps:

1. Encode query → dense vector embedding
2. Search vector database for top-k relevant chunks
3. Concatenate chunks as context to the LLM prompt
4. Generate grounded answer with citations

RAG reduces hallucination and allows models to reference up-to-date information
without retraining. Key libraries: FAISS, ChromaDB, Weaviate, LangChain.""",
        ],
    ),
    (
        "Product_Spec_v2.pdf",
        "Product Specification — DataScan Pro v2",
        [
            """Product Overview

DataScan Pro is a document intelligence platform for enterprise.
Supported input formats: PDF, TIFF, PNG, JPEG, DOCX, TXT.
Deployment: SaaS (cloud) or on-premises via Docker.

Performance Targets:
- Parse 100-page PDF in < 30 seconds
- OCR accuracy: > 97% on clean scans
- Classification latency: < 2 seconds per document
- Query response: < 3 seconds (p95)

Supported languages: English, French, Spanish, German, Japanese.""",
            """API Reference

POST /v2/documents/ingest
  Body: multipart/form-data { file, metadata? }
  Returns: { doc_id, status }

GET /v2/documents/{doc_id}
  Returns: { doc_id, status, classification, pages[] }

POST /v2/chat
  Body: { query, doc_ids?, history? }
  Returns: { answer, citations[] }

Authentication: Bearer token (JWT). Tokens expire after 24 hours.
Rate limits: 100 requests/minute per API key.""",
        ],
    ),
    (
        "Climate_Policy_Brief.pdf",
        "Climate Policy Brief — GreenFuture Institute",
        [
            """Global Temperature Trends 2024

Average global surface temperature in 2023 was 1.45°C above pre-industrial
levels, making it the hottest year on record. Arctic sea ice extent reached
a new annual minimum of 4.23 million km².

Emissions by sector (2023):
- Energy: 34%
- Transport: 16%
- Industry: 24%
- Agriculture: 18%
- Other: 8%

Key Policy Recommendations:
1. Carbon pricing at minimum $100/tonne by 2030
2. Phase out coal power by 2035 in OECD nations
3. Double renewable energy investment annually""",
            """Renewable Energy Progress

Solar capacity added globally in 2023: 413 GW (record high)
Wind capacity added globally in 2023: 116 GW
Total renewable share of electricity: 30%

Countries leading in renewables:
- Denmark: 88% wind + solar
- Portugal: 65% renewables
- Germany: 59% renewables

Cost of solar PV dropped 89% over the last decade.
Battery storage costs fell 97% since 2010.
Electric vehicle sales reached 14 million units in 2023.""",
        ],
    ),
]


def upload(name: str, data: bytes):
    r = requests.post(f"{API}/documents/upload", files={"file": (name, data, "application/pdf")}, timeout=30)
    r.raise_for_status()
    return r.json()["doc_id"]


if __name__ == "__main__":
    print("Seeding sample documents...")
    for filename, title, pages in SAMPLES:
        pdf = make_pdf(title, pages)
        try:
            doc_id = upload(filename, pdf)
            print(f"  ✓ {filename} → {doc_id}")
        except Exception as e:
            print(f"  ✗ {filename} failed: {e}")
        time.sleep(0.5)
    print("\nDone. Documents are being processed in background (parsing → classifying → indexing).")
    print("Wait ~30 seconds then try the chat.")
