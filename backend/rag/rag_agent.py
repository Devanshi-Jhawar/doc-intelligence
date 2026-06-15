import anthropic
from config import ANTHROPIC_API_KEY
from .vector_store import search

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

RAG_SYSTEM = """You are a document intelligence assistant. Answer questions using ONLY the provided context chunks.
Rules:
- Cite every fact with [doc_name, p.N] inline. Example: "The revenue was $5M [annual_report.pdf, p.3]."
- If the context does not contain the answer, say exactly: "I don't have enough information in the uploaded documents to answer that."
- Never hallucinate or use outside knowledge.
- Be concise and direct."""

def _build_context(chunks: list[dict]) -> str:
    parts = []
    for c in chunks:
        fname = c["filename"]
        pnum = c["page_num"]
        text = c["text"]
        parts.append(f"[Source: {fname}, page {pnum}]\n{text}")
    return "\n\n---\n\n".join(parts)

def answer_question(
    query: str,
    conversation_history: list[dict],
    top_k: int = 6,
) -> dict:
    chunks = search(query, top_k=top_k)

    if not chunks:
        return {
            "answer": "No documents are indexed yet. Please upload documents first.",
            "citations": [],
            "chunks": [],
        }

    context = _build_context(chunks)
    context_msg = f"Context from documents:\n\n{context}\n\nQuestion: {query}"

    # build message list including history
    messages = []
    for turn in conversation_history[-6:]:  # keep last 6 turns to manage context
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": context_msg})

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1200,
        system=RAG_SYSTEM,
        messages=messages,
    )

    answer = response.content[0].text.strip()

    # extract unique citations from chunks used
    citations = []
    seen = set()
    for c in chunks:
        key = (c["filename"], c["page_num"])
        if key not in seen:
            seen.add(key)
            citations.append({
                "filename": c["filename"],
                "page_num": c["page_num"],
                "doc_id": c["doc_id"],
                "image_path": c.get("image_path"),
                "score": round(c.get("score", 0), 3),
            })

    return {
        "answer": answer,
        "citations": citations,
        "chunks": chunks,
    }
