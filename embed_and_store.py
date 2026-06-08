"""
embed_and_store.py

Milestone 4 — Embedding and Retrieval for the SCU Off-Campus Housing RAG system.

Pipeline stage:
    chunks (from ingest.py)
        ↓
    sentence-transformers/all-MiniLM-L6-v2  (local embedding model)
        ↓
    ChromaDB  (persistent on-disk vector store)
        ↓
    top-k cosine similarity retrieval

Usage:
    python embed_and_store.py          # ingest all chunks + run 5 evaluation queries
    from embed_and_store import search, load_collection   # import for use in rag.py
"""

import io
import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from ingest import load_and_chunk_all

# ── Config ────────────────────────────────────────────────────────────────────

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHROMA_PATH     = str(Path(__file__).parent / "chroma_db")  # persists next to this file
COLLECTION_NAME = "scu_housing"
TOP_K           = 5
BATCH_SIZE      = 64  # chunks per upsert call; keeps memory usage flat for large corpora

# Evaluation queries drawn directly from the planning.md Evaluation Plan table.
# Run these to visually verify retrieval quality before wiring up the LLM.
EVAL_QUERIES = [
    "Who can I contact at SCU to seek advice on off-campus housing?",
    "What are some local apartments that are closest to SCU?",
    "What apartment complex on El Camino Real is closest to SCU?",
    "How far in advance does SCU recommend starting your housing search?",
    "What summer subleases are listed near SCU campus?",
]


# ── Vector store initialisation ───────────────────────────────────────────────

def init_chroma(
    path: str = CHROMA_PATH,
    collection_name: str = COLLECTION_NAME,
) -> chromadb.Collection:
    """
    Open (or create) a persistent ChromaDB instance and return the collection.

    ChromaDB API explained
    ──────────────────────
    chromadb.PersistentClient(path=...)
        Opens an on-disk store backed by SQLite + an HNSW vector index at
        *path*.  The data survives process restarts, so re-running this script
        will NOT re-embed documents that are already present — upsert handles
        that gracefully.

    client.get_or_create_collection(name, metadata)
        Returns the named collection if it already exists; creates a fresh one
        otherwise.  The metadata dict configures the HNSW similarity space:
            "hnsw:space": "cosine"
                Tells the index to measure cosine distance (= 1 − cosine_sim).
                Lower distance → higher relevance.  This is the correct metric
                for sentence-transformer embeddings because those models are
                trained to place semantically similar sentences close together
                in cosine space.
    """
    client = chromadb.PersistentClient(path=path)
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


# ── Embedding model ───────────────────────────────────────────────────────────

def load_model(model_name: str = EMBEDDING_MODEL) -> SentenceTransformer:
    """
    Load the sentence-transformer embedding model.

    sentence-transformers caches the model weights locally after the first
    download, so subsequent calls are instant.
    """
    print(f"Loading embedding model: {model_name}")
    return SentenceTransformer(model_name)


# ── Embedding and ingestion ───────────────────────────────────────────────────

def embed_and_ingest(
    chunks: list[dict],
    collection: chromadb.Collection,
    model: SentenceTransformer,
) -> None:
    """
    Generate embeddings for every chunk and upsert them into ChromaDB.

    ChromaDB API explained
    ──────────────────────
    collection.upsert(ids, embeddings, documents, metadatas)
        Adds each document if its id is new; updates it if the id already
        exists.  Using upsert (rather than add) makes this function idempotent
        — safe to re-run without creating duplicate entries.

        ids         — unique string key per document.  We use str(chunk_id)
                      (e.g. "0", "1", …) so the integer index survives a round
                      trip through the string-only ChromaDB id field.
        embeddings  — parallel list of float vectors (one per document).
                      Must be Python lists, not numpy arrays.
        documents   — the raw text stored alongside the vector.  ChromaDB
                      returns this on query so you can read the content back
                      without a separate lookup.
        metadatas   — parallel list of dicts.  Supports filtering at query
                      time (e.g. where={"type": "spreadsheet"}).  Only scalar
                      values (str, int, float, bool) are allowed per key.

    sentence_transformers.SentenceTransformer.encode(texts, normalize_embeddings=True)
        normalize_embeddings=True applies L2 normalisation so every vector has
        unit length.  This makes cosine_similarity(a, b) == dot(a, b), which
        is required for the "cosine" distance space configured on the
        collection.  Without normalisation the distances would be incorrect.
    """
    existing = collection.count()
    if existing == len(chunks):
        print(f"Collection already contains {existing} chunks — skipping ingestion.")
        return
    if existing > 0:
        print(f"Collection has {existing}/{len(chunks)} chunks — upserting all to sync.")

    print(f"Embedding {len(chunks)} chunks in batches of {BATCH_SIZE}...\n")

    for batch_start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[batch_start : batch_start + BATCH_SIZE]
        batch_end = batch_start + len(batch)

        texts = [c["content"] for c in batch]

        # encode() returns a (batch_size, 384) float32 numpy array.
        # .tolist() converts it to nested Python lists that ChromaDB accepts.
        embeddings = model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

        collection.upsert(
            ids=[str(c["chunk_id"]) for c in batch],
            embeddings=embeddings,
            documents=texts,
            metadatas=[
                {
                    "source":   c["source"],
                    "type":     c["type"],
                    "chunk_id": c["chunk_id"],
                }
                for c in batch
            ],
        )
        print(f"  Upserted chunks {batch_start}–{batch_end - 1} ({len(batch)} items)")

    print(f"\nIngestion complete. Collection now holds {collection.count()} chunks.\n")


# ── Retrieval ─────────────────────────────────────────────────────────────────

def search(
    query: str,
    collection: chromadb.Collection,
    model: SentenceTransformer,
    k: int = TOP_K,
) -> list[dict]:
    """
    Embed *query* and return the top-*k* most relevant chunks from ChromaDB.

    ChromaDB API explained
    ──────────────────────
    collection.query(query_embeddings, n_results, include)
        Runs an approximate nearest-neighbour (ANN) search against the HNSW
        index stored on disk.

        query_embeddings — list of query vectors (one per query string).
                           We submit one query at a time, so this is a list
                           containing a single 384-d vector.
        n_results        — how many results to return per query (our top-k).
        include          — which fields to attach to the response:
                             "documents"  → the stored raw text
                             "metadatas"  → the metadata dicts we upserted
                             "distances"  → cosine distance scores
                                           (0 = identical, 1 = orthogonal,
                                            2 = opposite direction)

        The response is a dict of lists-of-lists: the outer list has one entry
        per submitted query.  Because we always submit exactly one query we
        index [0] on each field to unwrap it.

    We convert distance → similarity with:  score = 1 − distance
    so that score = 1.0 means a perfect match and score = 0.0 means completely
    unrelated.
    """
    query_embedding = model.encode(
        [query],
        normalize_embeddings=True,
    ).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    # Unwrap the outer list (one result-set per query; we only submitted one)
    docs      = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    return [
        {
            "rank":       rank + 1,
            "similarity": round(1.0 - dist, 4),   # higher = better match (0–1)
            "distance":   round(dist, 4),           # lower  = better match (0–2); checkpoint: < 0.50
            "source":     meta["source"],
            "type":       meta["type"],
            "chunk_id":   meta["chunk_id"],
            "content":    doc,
        }
        for rank, (doc, meta, dist) in enumerate(zip(docs, metadatas, distances))
    ]


# ── Pretty printer ────────────────────────────────────────────────────────────

def print_results(query: str, results: list[dict]) -> None:
    """
    Pretty-print retrieval results to the console for visual quality inspection.

    Output format per result:
        Rank · similarity · distance · pass/fail · chunk_id · content type
        Full chunk content (word-wrapped at 72 chars, no line cap)

    Scoring key
    -----------
    similarity  = 1 − cosine_distance  (higher = better; 1.0 = perfect match)
    distance    = raw cosine distance  (lower  = better; checkpoint: < 0.50)
    ✓ / ✗       = distance < 0.50 (passes checkpoint) vs ≥ 0.50 (review needed)
    """
    width = 72
    print("=" * width)
    print(f"QUERY: {query}")
    print("=" * width)

    for r in results:
        flag = "✓" if r["distance"] < 0.50 else "✗"
        header = (
            f"  Rank {r['rank']}  |  "
            f"similarity={r['similarity']:.4f}  distance={r['distance']:.4f}  {flag}  |  "
            f"chunk_id={r['chunk_id']}  |  type={r['type']}"
        )
        print(header)
        print(f"  Source: {r['source']}")
        print(f"  {'─' * (width - 4)}")

        # Word-wrap content at (width - 4) characters — full chunk, no cap
        max_w = width - 4
        lines_out = []
        for raw_line in r["content"].splitlines():
            words = raw_line.split()
            current = "  "
            for word in words:
                if len(current) + len(word) + 1 > max_w:
                    lines_out.append(current.rstrip())
                    current = "  " + word
                else:
                    current += ("" if current == "  " else " ") + word
            if current.strip():
                lines_out.append(current.rstrip())

        for line in lines_out:
            print(line)
        print()

    print()


# ── Public helper for rag.py ──────────────────────────────────────────────────

def load_collection(
    path: str = CHROMA_PATH,
    collection_name: str = COLLECTION_NAME,
    model_name: str = EMBEDDING_MODEL,
) -> tuple[chromadb.Collection, SentenceTransformer]:
    """
    Convenience function for the next pipeline stage (rag.py).

    Returns a (collection, model) tuple that is ready to pass to search().
    Assumes embed_and_store.py has already been run to populate the collection.
    """
    collection = init_chroma(path, collection_name)
    model = load_model(model_name)
    return collection, model


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Force UTF-8 output so non-Latin characters don't crash on Windows cp1252
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    # ── Step 1: load and chunk ──────────────────────────────────────────────
    print("── Step 1: Load and chunk all sources ───────────────────────────────────\n")
    chunks = load_and_chunk_all()
    print(f"\nTotal chunks loaded: {len(chunks)}\n")

    # ── Step 2: initialise ChromaDB and the embedding model ─────────────────
    print("── Step 2: Initialise ChromaDB and embedding model ──────────────────────\n")
    collection = init_chroma()
    model      = load_model()
    print(f"\nChromaDB path : {CHROMA_PATH}")
    print(f"Collection    : {COLLECTION_NAME}")
    print(f"Chunks on disk: {collection.count()}\n")

    # ── Step 3: embed and ingest (idempotent) ───────────────────────────────
    print("── Step 3: Embed and ingest into ChromaDB ───────────────────────────────\n")
    embed_and_ingest(chunks, collection, model)

    # ── Step 4: retrieval quality test ──────────────────────────────────────
    print("── Step 4: Retrieval quality test — 5 evaluation queries ────────────────\n")
    print("These queries come from the planning.md Evaluation Plan table.")
    print("Inspect each result set: do the top chunks contain the expected answer?")
    print("Scoring: similarity (higher=better) | distance=1-similarity (lower=better, <0.50 passes checkpoint)\n")

    for query in EVAL_QUERIES:
        results = search(query, collection, model, k=TOP_K)
        print_results(query, results)
