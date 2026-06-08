"""
generator.py

Milestone 5 — Generation layer for the SCU Off-Campus Housing RAG system.

Pipeline stage:
    User query
        ↓
    retrieve()  →  top-k chunks from ChromaDB  (via embed_and_store.search)
        ↓
    generate_answer()  →  grounded prose from Groq LLM
        ↓
    format_sources()  →  programmatic source list from metadata (NOT from LLM)
        ↓
    rag_pipeline()  →  (answer, sources_markdown) returned to Gradio

Usage:
    from generator import rag_pipeline   # called by app.py
    answer, sources = rag_pipeline("What apartments are closest to SCU?")
"""

import os

import groq
from dotenv import load_dotenv

from embed_and_store import load_collection, search

# ── Load environment variables ────────────────────────────────────────────────

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

# Groq model to use for generation.
# llama-3.3-70b-versatile is a strong, fast model available on the free tier.
GROQ_MODEL = "llama-3.3-70b-versatile"

# Number of chunks to retrieve per query — must match planning.md spec (Top-K = 5).
TOP_K = 5

# System prompt that strictly grounds the LLM in the retrieved context.
# "ONLY the provided context" and the exact fallback string together prevent
# the model from drifting into general knowledge.
SYSTEM_PROMPT = (
    "You are a helpful assistant for Santa Clara University students. "
    "Answer the user's question using ONLY the provided context. "
    "If the context does not contain the answer, reply exactly with: "
    "'I do not have enough information to answer that based on the provided documents.' "
    "Do not use outside knowledge."
)

# ── Module-level initialization (runs once on import) ─────────────────────────
#
# Loading the 90 MB all-MiniLM-L6-v2 embedding model and opening the ChromaDB
# connection are both expensive operations.  By doing this at import time rather
# than inside each function call, Gradio's repeated invocations of rag_pipeline()
# reuse the same already-loaded objects instead of rebuilding them from scratch
# on every request.

print("Initializing RAG backend...")
_collection, _embed_model = load_collection()
_groq_client = groq.Groq(api_key=os.environ["GROQ_API_KEY"])
print("Backend ready.\n")


# ── Retrieval ─────────────────────────────────────────────────────────────────

def retrieve(query: str, k: int = TOP_K) -> list[dict]:
    """
    Embed *query* and return the top-*k* most relevant chunks from ChromaDB.

    Delegates entirely to embed_and_store.search(), which handles:
      - encoding the query with all-MiniLM-L6-v2
      - querying the HNSW cosine-similarity index
      - converting distances to similarity scores

    Each returned dict contains:
        rank, similarity, distance, source, type, chunk_id, content
    """
    return search(query, _collection, _embed_model, k=k)


# ── Generation ────────────────────────────────────────────────────────────────

def generate_answer(query: str, results: list[dict]) -> str:
    """
    Build a grounded context block from *results* and call the Groq LLM.

    The context is formatted as a numbered list so the model can easily
    reference individual passages.  The system prompt forbids the model
    from using any knowledge beyond what is supplied here.

    Returns the model's text response.
    """
    # Build the context block from retrieved chunk content
    context_parts = []
    for r in results:
        context_parts.append(f"[{r['rank']}] {r['content']}")
    context = "\n\n".join(context_parts)

    user_message = (
        f"Context:\n{context}\n\n"
        f"Question: {query}"
    )

    response = _groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        temperature=0.2,   # low temperature for factual, grounded responses
        max_tokens=512,
    )

    return response.choices[0].message.content.strip()


# ── Programmatic source attribution ───────────────────────────────────────────

def format_sources(results: list[dict]) -> str:
    """
    Build a deduplicated Markdown list of sources from ChromaDB metadata.

    WHY THIS PREVENTS HALLUCINATED CITATIONS
    ─────────────────────────────────────────
    The LLM is asked only to produce a prose answer — it is never instructed
    to name, format, or invent citations.  This function reads the 'source'
    field directly from the Python dicts returned by ChromaDB's query result.
    Those values were written to the database during embed_and_store.py's
    upsert() call and reflect the actual file paths / URLs of ingested
    documents.

    Because the source list is assembled entirely in Python from database
    records, it is structurally impossible for the LLM to introduce a
    fabricated source name:  the LLM never touches this data.
    """
    seen: set[str] = set()
    lines: list[str] = []

    for r in results:
        source = r["source"]          # pulled from ChromaDB metadata, not LLM output
        if source not in seen:
            seen.add(source)
            # Include similarity score so the user can judge relevance at a glance
            lines.append(f"- **{source}** *(similarity: {r['similarity']:.2f})*")

    header = "### Sources Retrieved\n\n"
    return header + ("\n".join(lines) if lines else "No sources found.")


# ── Orchestrator ──────────────────────────────────────────────────────────────

def rag_pipeline(query: str) -> tuple[str, str]:
    """
    End-to-end RAG pipeline called by the Gradio UI.

    Steps:
        1. Retrieve top-k chunks from ChromaDB
        2. Generate a grounded answer via the Groq LLM
        3. Format the source list programmatically from metadata

    Returns:
        (answer, sources_markdown) — both strings, ready for Gradio components
    """
    if not query.strip():
        return "Please enter a question.", ""

    results = retrieve(query, k=TOP_K)
    answer  = generate_answer(query, results)
    sources = format_sources(results)

    return answer, sources
