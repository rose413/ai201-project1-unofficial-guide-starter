"""
ingest.py

Ingestion pipeline for the SCU off-campus housing RAG system.
Loads all sources defined in test_scraper.py, cleans the text, and returns
chunks ready for embedding.

Chunking strategy (per planning.md):
  - Unstructured text (HTML, PDF, Reddit, delimited .txt files):
      Token-aware RecursiveCharacterTextSplitter — 500 tokens / 50 overlap
  - Structured spreadsheets (.xlsx):
      Row-by-row — one chunk per row, columns serialised as "Col: value | ..."

Usage:
    python ingest.py          # prints a summary + sample chunks
    from ingest import load_and_chunk_all   # returns list[dict] for other modules
"""

import io
import re
import sys
import warnings

import pandas as pd
from pathlib import Path
from transformers import AutoTokenizer

from test_scraper import (
    SOURCES,
    scrape_html,
    scrape_pdf,
    scrape_reddit,
    scrape_playwright,
    scrape_local_text,
)

# ── Config ────────────────────────────────────────────────────────────────────

CHUNK_SIZE = 500       # tokens
CHUNK_OVERLAP = 50     # tokens
TOKENIZER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Source IDs to skip entirely (none currently)
SKIP_SOURCE_IDS: set[int] = set()

# For local delimited-text files, map path → delimiter string
SECTION_DELIMITERS = {
    "data/apartments_com_listings.txt": "--- APARTMENTS_COM_DELIMITER ---",
    "data/facebook_housing_posts.txt":  "--- FACEBOOK_POST_DELIMITER ---",
    "data/scu_portal_listings.txt":     "--- SCU_PORTAL_DELIMITER ---",
}

# Excel files whose first row is a title (not column headers); use header=1 for these
EXCEL_TITLE_ROW_FILES = {
    "data/Local-Apartment-Listings---Santa-Clara-County (2).xlsx",
}

# ── Tokenizer (loaded once at module import) ──────────────────────────────────

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    _tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_MODEL)


def _token_len(text: str) -> int:
    """Return the number of tokens in *text* (no special tokens added)."""
    return len(_tokenizer.encode(text, add_special_tokens=False))


# ── Cleaning ──────────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Normalise whitespace and strip the string."""
    text = re.sub(r"[ \t]+", " ", text)       # collapse horizontal whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)    # collapse 3+ newlines → 2
    return text.strip()


# ── Token-aware recursive character splitter ─────────────────────────────────

_DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def _recursive_split(text: str, separators: list[str] | None = None) -> list[str]:
    """
    Split *text* into chunks of at most CHUNK_SIZE tokens with CHUNK_OVERLAP
    token overlap between consecutive chunks.

    Tries separators in order and recursively splits pieces that are still too
    long, mirroring LangChain's RecursiveCharacterTextSplitter behaviour.
    """
    if separators is None:
        separators = _DEFAULT_SEPARATORS

    if _token_len(text) <= CHUNK_SIZE:
        return [text] if text.strip() else []

    # 1. Find the first separator that actually appears in the text
    sep_used = ""
    splits: list[str] = [text]
    for sep in separators:
        if sep == "" or sep in text:
            splits = text.split(sep) if sep else list(text)
            sep_used = sep
            break

    # 2. Recursively split any piece that is still too long
    next_seps = separators[separators.index(sep_used) + 1:] if sep_used in separators else [""]
    good_splits: list[str] = []
    for piece in splits:
        piece = piece.strip()
        if not piece:
            continue
        if _token_len(piece) <= CHUNK_SIZE:
            good_splits.append(piece)
        else:
            good_splits.extend(_recursive_split(piece, next_seps))

    # 3. Merge small splits into chunks, carrying CHUNK_OVERLAP tokens forward
    chunks: list[str] = []
    window: list[str] = []
    window_len = 0

    for piece in good_splits:
        piece_len = _token_len(piece)
        if window_len + piece_len > CHUNK_SIZE and window:
            chunks.append("\n".join(window))
            # Trim the front of the window until it fits within CHUNK_OVERLAP
            while window and window_len > CHUNK_OVERLAP:
                window_len -= _token_len(window[0])
                window.pop(0)
        window.append(piece)
        window_len += piece_len

    if window:
        chunks.append("\n".join(window))

    return [c for c in chunks if c.strip()]


# ── Per-type chunkers ─────────────────────────────────────────────────────────

def _chunk_text(raw_text: str, source_name: str, path: str | None = None) -> list[dict]:
    """
    Clean and chunk a block of plain text.

    If *path* matches a key in SECTION_DELIMITERS the text is first split on
    that delimiter so each logical section is chunked independently (prevents
    apartment listings or Facebook posts bleeding into one another).
    """
    delimiter = SECTION_DELIMITERS.get(path or "") if path else None

    if delimiter:
        sections = raw_text.split(delimiter)
    else:
        sections = [raw_text]

    chunks: list[dict] = []
    for section in sections:
        section = clean_text(section)
        if not section:
            continue
        for piece in _recursive_split(section):
            chunks.append({
                "content": piece,
                "source":  source_name,
                "type":    "text",
            })
    return chunks


def _chunk_excel(path: str, source_name: str, header: int = 0) -> list[dict]:
    """Load an Excel file and return one chunk per non-empty row."""
    df = pd.read_excel(path, engine="openpyxl", header=header)
    df.columns = [re.sub(r"\s+", " ", str(col)).strip() for col in df.columns]
    df = df.dropna(how="all")
    df = df.fillna("")

    chunks: list[dict] = []
    for _, row in df.iterrows():
        parts = [
            f"{col}: {str(val).strip()}"
            for col, val in row.items()
            if str(val).strip()
        ]
        if parts:
            chunks.append({
                "content": " | ".join(parts),
                "source":  source_name,
                "type":    "spreadsheet",
            })
    return chunks


# ── Main entry point ──────────────────────────────────────────────────────────

def load_and_chunk_all() -> list[dict]:
    """
    Load and chunk every source defined in test_scraper.SOURCES.

    Returns a flat list of chunk dicts, each with keys:
        chunk_id  – global integer index
        content   – text to embed
        source    – human-readable source name
        type      – "text" | "spreadsheet"
    """
    all_chunks: list[dict] = []

    for src in SOURCES:
        sid   = src["id"]
        name  = src["name"]
        stype = src["type"]
        url   = src.get("url")
        path  = src.get("path")

        # ── Skip sources that cannot be loaded ────────────────────────────────
        if sid in SKIP_SOURCE_IDS:
            print(f"[SKIP]    Source {sid}: {name}")
            continue

        # ── Dispatch by source type ───────────────────────────────────────────
        try:
            if stype == "local_excel":
                header_row = 1 if path in EXCEL_TITLE_ROW_FILES else 0
                new_chunks = _chunk_excel(path, name, header=header_row)
                status = f"{len(new_chunks)} row chunks"

            elif stype == "local_text":
                success, text = scrape_local_text(path)
                if not success:
                    print(f"[WARNING] Source {sid}: {name} — {text}")
                    continue
                new_chunks = _chunk_text(text, name, path=path)
                status = f"{len(new_chunks)} text chunks"

            elif stype == "pdf":
                success, text = scrape_pdf(url)
                if not success:
                    print(f"[WARNING] Source {sid}: {name} — {text}")
                    continue
                new_chunks = _chunk_text(text, name)
                status = f"{len(new_chunks)} text chunks"

            elif stype == "html":
                success, text = scrape_html(url)
                if not success:
                    print(f"[WARNING] Source {sid}: {name} — {text}")
                    continue
                new_chunks = _chunk_text(text, name)
                status = f"{len(new_chunks)} text chunks"

            elif stype == "reddit":
                success, text = scrape_reddit(url)
                if not success:
                    print(f"[WARNING] Source {sid}: {name} — {text}")
                    continue
                new_chunks = _chunk_text(text, name)
                status = f"{len(new_chunks)} text chunks"

            elif stype == "js":
                success, text = scrape_playwright(url)
                if not success:
                    print(f"[WARNING] Source {sid}: {name} — {text}")
                    continue
                new_chunks = _chunk_text(text, name)
                status = f"{len(new_chunks)} text chunks"

            else:
                print(f"[WARNING] Source {sid}: {name} — unknown type '{stype}', skipping")
                continue

        except Exception as exc:
            print(f"[WARNING] Source {sid}: {name} — unexpected error: {exc}")
            continue

        print(f"[OK]      Source {sid}: {name} -> {status}")
        all_chunks.extend(new_chunks)

    # Assign global chunk IDs
    for i, chunk in enumerate(all_chunks):
        chunk["chunk_id"] = i

    return all_chunks


# ── CLI summary ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Force UTF-8 output so emoji and non-Latin characters don't crash on Windows cp1252
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print("Loading and chunking all sources...\n")
    chunks = load_and_chunk_all()

    print(f"\nTotal chunks: {len(chunks)}")

    # Per-source breakdown
    by_source: dict[str, list[dict]] = {}
    for c in chunks:
        by_source.setdefault(c["source"], []).append(c)

    print(f"\n{'Source':<45} {'Chunks':>7}  {'Type'}")
    print("-" * 62)
    for src_name, cs in by_source.items():
        print(f"{src_name:<45} {len(cs):>7}  {cs[0]['type']}")

    # Sample 5 random chunks — one per source where possible
    import random

    shuffled = chunks[:]
    random.shuffle(shuffled)
    sample: list[dict] = []
    seen_sources: set[str] = set()
    for c in shuffled:
        if c["source"] not in seen_sources:
            sample.append(c)
            seen_sources.add(c["source"])
        if len(sample) == 5:
            break
    while len(sample) < 5 and len(sample) < len(chunks):
        c = random.choice(chunks)
        if c not in sample:
            sample.append(c)

    print("\n-- 5 Random Chunks (quality check) " + "-" * 35)
    for c in sample:
        tokens = _token_len(c["content"])
        if not c["content"].strip():
            flag = "EMPTY"
        elif tokens < 10:
            flag = "FRAGMENT"
        elif tokens > CHUNK_SIZE:
            flag = "OVERSIZED"
        else:
            flag = "OK"
        print(f"\n[chunk_id={c['chunk_id']} | tokens={tokens} | type={c['type']} | {flag}]")
        print(f"source: {c['source']}")
        print(c["content"])
        print("-" * 70)
