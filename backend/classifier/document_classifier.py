import json
import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

CLASSIFY_PROMPT = """You are a document classification system. Analyze the document text and return ONLY a JSON object with this exact schema:

{
  "type": "<one of: invoice, report, contract, academic_paper, news_article, manual, form, letter, presentation, medical_record, legal_document, financial_statement, other>",
  "topic": "<brief topic in 3-5 words>",
  "language": "<ISO 639-1 code, e.g. en>",
  "content_characteristics": {
    "has_tables": <bool>,
    "has_images": <bool>,
    "has_handwriting": <bool>,
    "is_scanned": <bool>,
    "estimated_reading_time_minutes": <int>
  },
  "sensitivity": "<one of: public, internal, confidential, restricted>",
  "sensitivity_reason": "<one sentence why>",
  "summary": "<2-3 sentence summary>",
  "key_entities": ["<entity1>", "<entity2>"],
  "date_range": "<estimated date or date range if detectable, else null>"
}

Return ONLY valid JSON, no markdown, no explanation."""

def classify_document(doc_info: dict) -> dict:
    # use first 3000 chars of text to keep token cost low
    sample_text = doc_info.get("full_text", "")[:3000]
    filename = doc_info.get("filename", "")
    num_pages = doc_info.get("num_pages", 1)

    user_msg = f"Filename: {filename}\nPages: {num_pages}\n\nDocument text:\n{sample_text}"

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        system=CLASSIFY_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw = response.content[0].text.strip()

    try:
        classification = json.loads(raw)
    except json.JSONDecodeError:
        # best-effort parse if model added backticks
        import re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        classification = json.loads(match.group()) if match else {"type": "other", "raw": raw}

    return classification
