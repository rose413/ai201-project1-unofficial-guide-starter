"""
test_scraper.py

Tests whether each source URL from planning.md can be scraped.
Prints a summary of what text was extracted (or why it failed).

Requirements (core):
    pip install requests beautifulsoup4 pdfplumber pandas openpyxl

Optional (for JS-rendered sites like Student Sublet & Apartments.com):
    pip install playwright
    playwright install chromium
"""

import io
import os
import textwrap

import requests
from bs4 import BeautifulSoup

try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("[WARNING] pdfplumber not installed — PDF scraping disabled.")
    print("          Run: pip install pdfplumber\n")

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_SUPPORT = True
except ImportError:
    PLAYWRIGHT_SUPPORT = False

# ---------------------------------------------------------------------------
# Source definitions
# ---------------------------------------------------------------------------

SOURCES = [
    {
        "id": 1,
        "name": "SCU Off-Campus Housing Information",
        "type": "html",
        "url": "https://www.scu.edu/ocl/off-campus-housing/",
    },
    {
        "id": 2,
        "name": "Off-Campus Landlord Contacts (PDF)",
        "type": "pdf",
        "url": "https://www.scu.edu/media/offices/dean-of-students-office/off-campus-living/Off-Campus-Landlord-Contacts-4.pdf",
    },
    {
        "id": 3,
        "name": "Local Apartment Listings (local file)",
        "type": "local_excel",
        "path": "data/Local-Apartment-Listings---Santa-Clara-County (2).xlsx"
        # "note": "Requires SCU login — local Excel file, not a URL.",
    },
    {
        "id": 4,
        "name": "Rental Listings Portal",
        "type": "local_text",
        "path": "data/scu_portal_listings.txt",
        "url": "https://www.scu.edu/apps/org/osl/housing/?&rent_max=3000&dt_avail=2026-6-30",
        "note": "Portal is JS-rendered; collected manually into local file.",
    },
    {
        "id": 5,
        "name": "Roommate Finder Responses",
        "type": "local_excel",
        "path": "data/2026-2027 Roommate Finder Results (Responses).xlsx",
        "url": None,
    },
    {
        "id": 6,
        "name": "Sublease Listing Responses",
        "type": "local_excel",
        "path": "data/Sublease Listing & Connection Form (Responses).xlsx",
        "url": None,
    },
    {
        "id": 7,
        "name": "Student Sublet",
        "type": "js",
        "url": "https://www.studentsublet.app/",
        "note": "React app — requires Playwright for JS rendering.",
    },
    {
        "id": 8,
        "name": "Apartments.com – Santa Clara",
        "type": "local_text",
        "path": "data/apartments_com_listings.txt",
        "url": "https://www.apartments.com/santa-clara-ca/",
        "note": "Akamai bot protection blocks all automated access. Collect manually.",
    },
    {
        "id": 9,
        "name": "Reddit – SCU Off-Campus Apartment Recommendation",
        "type": "reddit",
        "url": "https://old.reddit.com/r/SCU/comments/ca39x3/offcampus_apartment_recommendation/",
    },
    {
        "id": 10,
        "name": "SCU Facebook Housing Group",
        "type": "local_text",
        "path": "data/facebook_housing_posts.txt",
        "url": "https://www.facebook.com/groups/308542176473013/",
        "note": "Loaded from manually collected local file.",
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
TIMEOUT = 15
PREVIEW_CHARS = 500  # characters of text to preview

# Phrases that indicate the server returned a bot-block page instead of content
BOT_BLOCK_PHRASES = [
    "access denied",
    "you don't have permission to access",
    "403 forbidden",
    "enable javascript and cookies to continue",
    "checking your browser",
    "please enable cookies",
    "reference #",          # Akamai EdgeSuite error pages
    "ray id:",              # Cloudflare error pages
]


def is_bot_blocked(text: str) -> bool:
    """Return True if the extracted text looks like a bot-block error page."""
    lower = text.lower()
    return any(phrase in lower for phrase in BOT_BLOCK_PHRASES)


# ---------------------------------------------------------------------------
# Scraping helpers
# ---------------------------------------------------------------------------

def scrape_html(url: str) -> tuple[bool, str]:
    """Fetch an HTML page and return visible text from the main content area."""
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    # Remove script / style / navigation noise before extracting text
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()
    # Prefer the <main> landmark or common content containers over the full page.
    # This strips breadcrumb nav, sidebar links, and repeated heading text that
    # would otherwise pollute the embedding of the actual page content.
    content_node = (
        soup.find("main")
        or soup.find(id="main-content")
        or soup.find(id="content")
        or soup.find("article")
        or soup.body
        or soup
    )
    text = content_node.get_text(separator=" ", strip=True)
    # Collapse whitespace
    text = " ".join(text.split())
    if len(text) < 50:
        return False, "Page returned almost no readable text (possibly JS-rendered or login-gated)."
    if is_bot_blocked(text):
        return False, f"Bot-block detected (server refused access). First 200 chars: {text[:200]}"
    return True, text


def scrape_pdf(url: str) -> tuple[bool, str]:
    """Download a PDF and extract text with pdfplumber."""
    if not PDF_SUPPORT:
        return False, "pdfplumber not installed — run: pip install pdfplumber"
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
        pages_text = []
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                pages_text.append(t)
    text = "\n".join(pages_text).strip()
    if not text:
        return False, "PDF downloaded but no text could be extracted (may be image-based)."
    return True, text


def scrape_reddit(url: str) -> tuple[bool, str]:
    """Fetch a Reddit thread, trying the JSON API first then falling back to HTML."""
    # Reddit requires a descriptive User-Agent or it returns 429/403
    reddit_headers = {
        "User-Agent": "python:scu-housing-scraper:v1.0 (educational scraper)",
        "Accept": "application/json",
    }

    # --- Attempt 1: JSON API with raw_json=1 to avoid HTML-escaped text ---
    base_url = url.rstrip("/").removesuffix(".json")
    json_url = base_url + ".json?raw_json=1"
    try:
        resp = requests.get(json_url, headers=reddit_headers, timeout=TIMEOUT)
        resp.raise_for_status()
        # Verify we actually got JSON (not a login redirect page)
        data = resp.json()
        if isinstance(data, list) and len(data) >= 2:
            comments = []

            def extract_comments(node):
                if isinstance(node, dict):
                    kind = node.get("kind")
                    d = node.get("data", {})
                    if kind == "t3":
                        title = d.get("title", "")
                        body = d.get("selftext", "")
                        comments.append(f"[POST] {title}\n{body}")
                    elif kind == "t1":
                        body = d.get("body", "")
                        if body and body != "[deleted]":
                            comments.append(f"[COMMENT] {body}")
                    if "replies" in d and isinstance(d["replies"], dict):
                        extract_comments(d["replies"])
                    if "children" in d:
                        for child in d["children"]:
                            extract_comments(child)

            for top in data:
                extract_comments(top)

            text = "\n\n".join(c for c in comments if c.strip())
            if text:
                return True, text

    except Exception:
        pass  # Fall through to HTML fallback

    # --- Attempt 2: Scrape old.reddit.com HTML ---
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    parts = []
    # Post title
    title_tag = soup.find("a", class_="title")
    if title_tag:
        parts.append(f"[POST] {title_tag.get_text(strip=True)}")
    # Selftext (if any)
    selftext = soup.find("div", class_="usertext-body")
    if selftext:
        parts.append(selftext.get_text(separator=" ", strip=True))
    # Comments
    for entry in soup.find_all("div", class_="usertext-body"):
        t = entry.get_text(separator=" ", strip=True)
        if t:
            parts.append(f"[COMMENT] {t}")

    text = "\n\n".join(p for p in parts if p.strip())
    if not text:
        return False, "Reddit: JSON API blocked and HTML fallback found no text."
    return True, text


def scrape_playwright(url: str) -> tuple[bool, str]:
    """Render a JS-heavy page with a headless Chromium browser via Playwright."""
    if not PLAYWRIGHT_SUPPORT:
        return False, (
            "JS-rendered page requires Playwright. Install with:\n"
            "  pip install playwright && playwright install chromium"
        )
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=HEADERS["User-Agent"],
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
        )
        page.goto(url, wait_until="networkidle", timeout=30_000)
        # Wait a moment for any deferred rendering
        page.wait_for_timeout(2000)
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()
    text = " ".join(soup.get_text(separator=" ", strip=True).split())
    if len(text) < 50:
        return False, "Playwright rendered the page but found no readable text."
    if is_bot_blocked(text):
        return False, f"Bot-block detected (server refused access). First 200 chars: {text[:200]}"
    return True, text


def scrape_local_excel(path: str) -> tuple[bool, str]:
    """Read a local Excel file and convert each row to a text entry."""
    try:
        import pandas as pd
    except ImportError:
        return False, "pandas not installed — run: pip install pandas openpyxl"
    if not os.path.exists(path):
        return False, f"File not found: {path}"
    df = pd.read_excel(path, engine="openpyxl")
    df = df.dropna(how="all")
    parts = []
    for _, row in df.iterrows():
        fields = [
            f"{col}: {row[col]}"
            for col in df.columns
            if pd.notna(row[col]) and str(row[col]).strip()
        ]
        if fields:
            parts.append("[ENTRY] " + " | ".join(fields))
    text = "\n\n".join(parts)
    if not text:
        return False, "Excel file read but contained no data."
    return True, text


def scrape_local_text(path: str) -> tuple[bool, str]:
    """Read a local plain-text file."""
    if not os.path.exists(path):
        return False, f"File not found: {path}"
    with open(path, encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        return False, "Text file is empty."
    return True, text


FB_SESSION_FILE = "fb_session.json"
FB_OUTPUT_FILE = os.path.join("data", "facebook_housing_posts.txt")


def scrape_facebook(url: str) -> tuple[bool, str]:
    """Scrape a Facebook group using a saved Playwright session.

    Before running, generate fb_session.json by logging in once:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            ctx = browser.new_context()
            ctx.new_page().goto("https://www.facebook.com/login")
            input("Log in, then press Enter...")
            ctx.storage_state(path="fb_session.json")
            browser.close()
    """
    if not PLAYWRIGHT_SUPPORT:
        return False, (
            "Facebook scraping requires Playwright. Install with:\n"
            "  pip install playwright && playwright install chromium"
        )
    if not os.path.exists(FB_SESSION_FILE):
        return False, (
            f"No saved session found at '{FB_SESSION_FILE}'.\n"
            "Log in to Facebook once in a Playwright browser and save the session."
        )

    with sync_playwright() as p:
        # headless=False reduces bot-detection on Facebook
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=FB_SESSION_FILE)
        page = context.new_page()

        page.goto(url)
        page.wait_for_load_state("networkidle")

        # Scroll to load more posts (each scroll ~1–2 posts on Facebook)
        for _ in range(15):
            page.evaluate("window.scrollBy(0, 1000)")
            page.wait_for_timeout(2000)

        # Collect post containers
        posts = page.query_selector_all('div[role="article"]')
        parts = [p.inner_text() for p in posts if p.inner_text().strip()]
        browser.close()

    if not parts:
        return False, "No posts found — session may have expired. Delete fb_session.json and log in again."

    # Save to file for use in the RAG ingestion pipeline
    os.makedirs(os.path.dirname(FB_OUTPUT_FILE), exist_ok=True)
    with open(FB_OUTPUT_FILE, "w", encoding="utf-8") as f:
        for post_text in parts:
            f.write(f"--- POST ---\n\n{post_text.strip()}\n\n")
    print(f"  Saved {len(parts)} posts to {FB_OUTPUT_FILE}")

    return True, "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Main test runner
# ---------------------------------------------------------------------------

def run_tests():
    results = []

    for src in SOURCES:
        sid = src["id"]
        name = src["name"]
        stype = src["type"]
        url = src.get("url")
        path = src.get("path")
        note = src.get("note", "")

        print(f"\n{'='*70}")
        print(f"Source {sid}: {name}")
        if path:
            print(f"Path: {path}")
        elif url:
            print(f"URL: {url}")
        if note:
            print(f"Note: {note}")
        print("-" * 70)

        # --- Attempt scraping ---
        try:
            if stype == "local_excel":
                success, text = scrape_local_excel(path)
            elif stype == "local_text":
                success, text = scrape_local_text(path)
            elif stype == "pdf":
                success, text = scrape_pdf(url)
            elif stype == "reddit":
                success, text = scrape_reddit(url)
            elif stype == "js":
                success, text = scrape_playwright(url)
            elif stype == "facebook":
                success, text = scrape_facebook(url)
            else:
                success, text = scrape_html(url)

            if success:
                preview = textwrap.fill(text[:PREVIEW_CHARS], width=68)
                print(f"[SUCCESS] Extracted {len(text):,} characters.\nPreview:\n{preview}...")
                results.append((sid, name, "SUCCESS", f"{len(text):,} chars extracted"))
            else:
                print(f"[PARTIAL] {text}")
                results.append((sid, name, "PARTIAL", text))

        except requests.exceptions.HTTPError as e:
            detail = f"HTTP {e.response.status_code}: {e}"
            print(f"[FAIL] {detail}")
            results.append((sid, name, "FAIL", detail))
        except requests.exceptions.ConnectionError as e:
            detail = f"Connection error: {e}"
            print(f"[FAIL] {detail}")
            results.append((sid, name, "FAIL", detail))
        except requests.exceptions.Timeout:
            detail = "Request timed out."
            print(f"[FAIL] {detail}")
            results.append((sid, name, "FAIL", detail))
        except Exception as e:
            detail = f"Unexpected error: {e}"
            print(f"[FAIL] {detail}")
            results.append((sid, name, "FAIL", detail))

    # --- Summary table ---
    print(f"\n\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"{'#':<4} {'Status':<16} {'Source'}")
    print("-" * 70)
    for sid, name, status, _ in results:
        print(f"{sid:<4} {status:<16} {name}")

    print()
    counts = {}
    for _, _, status, _ in results:
        counts[status] = counts.get(status, 0) + 1
    for status, count in sorted(counts.items()):
        print(f"  {status}: {count}")


if __name__ == "__main__":
    run_tests()
