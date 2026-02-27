"""
Fetch and extract candidate profile text from URLs.
Supports: LinkedIn public profiles, portfolio sites, GitHub, PDF links, any public page.
"""
import re
import tempfile
from pathlib import Path
from typing import Tuple
from urllib.parse import urlparse

import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "no-cache",
}

MAX_CHARS = 20000


def _clean(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\t+", " ", text)
    return text.strip()


def _detect_linkedin_gate(text: str) -> bool:
    """Detect if LinkedIn returned a sign-in wall instead of a profile."""
    gates = [
        "join now to see",
        "sign in to see who",
        "authwall",
        "join linkedin",
        "to view this profile",
        "sign in",
    ]
    low = text.lower()
    return sum(1 for g in gates if g in low) >= 2


def _extract_linkedin(soup) -> str:
    """Extract structured text from a LinkedIn public profile page."""
    parts = []

    # Name (h1)
    h1 = soup.find("h1")
    if h1:
        parts.append(f"Name: {h1.get_text(strip=True)}")

    # Headline / subheading near top
    for sel in [
        ".top-card-layout__headline",
        ".pv-text-details__left-panel h2",
        "h2.top-card-layout__headline",
        '[class*="headline"]',
        '[class*="subheading"]',
    ]:
        try:
            elem = soup.select_one(sel)
            if elem and elem.get_text(strip=True):
                parts.append(f"Headline: {elem.get_text(strip=True)}")
                break
        except Exception:
            pass

    # All significant text blocks (sections, articles, divs with good content)
    seen = set()
    for tag in soup.find_all(["section", "article", "div", "li"]):
        raw = tag.get_text(separator=" ", strip=True)
        if len(raw) < 40 or raw in seen:
            continue
        # Avoid duplicating nested content
        seen.add(raw[:100])
        parts.append(raw)

    if parts:
        return _clean("\n\n".join(dict.fromkeys(parts)))  # deduplicate order-preserving

    return _clean(soup.get_text(separator="\n", strip=True))


def _extract_github(soup, url: str) -> str:
    """Extract bio, repos, and README from GitHub profile/repo."""
    parts = []

    # Name / username
    for sel in [".p-name", "span.p-nickname", "h1"]:
        try:
            elem = soup.select_one(sel)
            if elem:
                parts.append(f"Name/Username: {elem.get_text(strip=True)}")
                break
        except Exception:
            pass

    # Bio
    bio = soup.select_one(".p-note, .user-profile-bio")
    if bio:
        parts.append(f"Bio: {bio.get_text(strip=True)}")

    # README or main content
    readme = soup.select_one("#readme, article.markdown-body, .Box-body")
    if readme:
        parts.append(readme.get_text(separator="\n", strip=True))

    # Pinned repos / description
    for item in soup.select(".pinned-item-desc, .repo-description"):
        parts.append(item.get_text(strip=True))

    if parts:
        return _clean("\n\n".join(parts))

    return _clean(soup.get_text(separator="\n", strip=True))


def _extract_generic(soup) -> str:
    """Generic HTML text extraction: strip boilerplate, keep main content."""
    # Remove noisy tags
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "aside", "noscript", "form", "button", "iframe",
                     "svg", "img", "link", "meta"]):
        tag.decompose()

    # Prefer semantic main content
    main = (
        soup.find("main")
        or soup.find(id=re.compile(r"main|content|profile|resume|bio", re.I))
        or soup.find(class_=re.compile(r"main|content|profile|resume|bio|portfolio", re.I))
        or soup.body
    )
    if main:
        return _clean(main.get_text(separator="\n", strip=True))
    return _clean(soup.get_text(separator="\n", strip=True))


def _fetch_pdf_url(url: str, timeout: int) -> str:
    """Download a PDF from URL and extract text."""
    resp = requests.get(url, headers=HEADERS, timeout=timeout, stream=True)
    resp.raise_for_status()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        for chunk in resp.iter_content(chunk_size=8192):
            tmp.write(chunk)
        tmp_path = Path(tmp.name)

    try:
        from src.cv_parser import extract_text_from_file
        return extract_text_from_file(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


def fetch_text_from_url(url: str, timeout: int = 30) -> Tuple[str, str]:
    """
    Fetch candidate profile text from a URL.

    Returns:
        (extracted_text, source_label)
        e.g. ("John Doe\\nSoftware Engineer...", "LinkedIn Profile")

    Raises:
        ValueError: if the URL is unreachable or returns no usable content.
    """
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    hostname = parsed.netloc.lower().replace("www.", "")
    path_lower = parsed.path.lower()

    # ── PDF link ──────────────────────────────────────────────────────────────
    if path_lower.endswith(".pdf"):
        text = _fetch_pdf_url(url, timeout)
        if not text.strip():
            raise ValueError("No text found in the PDF at the provided URL.")
        return text[:MAX_CHARS], "PDF Document"

    # ── Fetch HTML ────────────────────────────────────────────────────────────
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise ValueError(f"Could not connect to {hostname}. Check the URL and try again.")
    except requests.exceptions.Timeout:
        raise ValueError(f"Request to {hostname} timed out after {timeout}s.")
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response is not None else "?"
        if code == 999:
            raise ValueError(
                "LinkedIn blocked this request (HTTP 999). "
                "LinkedIn requires authentication for full profiles. "
                "Please export your CV as PDF from LinkedIn and upload it instead."
            )
        raise ValueError(f"HTTP {code} from {hostname}. The page may be private or unavailable.")

    content_type = resp.headers.get("content-type", "")
    if "application/pdf" in content_type:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(resp.content)
            tmp_path = Path(tmp.name)
        try:
            from src.cv_parser import extract_text_from_file
            text = extract_text_from_file(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)
        if not text.strip():
            raise ValueError("No text found in the PDF.")
        return text[:MAX_CHARS], "PDF Document"

    # ── Parse HTML ────────────────────────────────────────────────────────────
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "lxml")
    except ImportError:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
        except ImportError:
            raise ValueError("BeautifulSoup is not installed. Run: pip install beautifulsoup4 lxml")

    # ── Source-specific extraction ────────────────────────────────────────────
    if "linkedin.com" in hostname:
        raw = _extract_linkedin(soup)
        if _detect_linkedin_gate(raw):
            raise ValueError(
                "LinkedIn requires you to be logged in to view this profile. "
                "Please use LinkedIn's 'Save to PDF' feature (More → Save to PDF) "
                "and upload the PDF file instead."
            )
        if len(raw.strip()) < 200:
            raise ValueError(
                "Not enough content extracted from LinkedIn. "
                "The profile may be private. Try downloading as PDF instead."
            )
        return raw[:MAX_CHARS], "LinkedIn Profile"

    if "github.com" in hostname:
        text = _extract_github(soup, url)
        label = "GitHub Profile"
        if "/blob/" in path_lower or "/tree/" in path_lower:
            label = "GitHub Repository"
        return text[:MAX_CHARS], label

    if "stackoverflow.com" in hostname:
        text = _extract_generic(soup)
        return text[:MAX_CHARS], "Stack Overflow Profile"

    # ── Generic pages (portfolio, personal site, CV hosted page) ─────────────
    text = _extract_generic(soup)
    if len(text.strip()) < 100:
        raise ValueError("Very little text found at this URL. The page may be mostly images or require JavaScript.")

    # Label the source
    label_map = {
        "behance.net": "Behance Portfolio",
        "dribbble.com": "Dribbble Portfolio",
        "medium.com": "Medium Profile",
        "dev.to": "Dev.to Profile",
        "about.me": "About.me Profile",
        "xing.com": "XING Profile",
        "glassdoor.com": "Glassdoor Profile",
    }
    label = label_map.get(hostname, f"Web Page ({hostname})")
    return text[:MAX_CHARS], label


def url_to_display_name(url: str) -> str:
    """Create a human-readable name for storage from the URL."""
    parsed = urlparse(url)
    hostname = parsed.netloc.replace("www.", "")
    path_parts = [p for p in parsed.path.split("/") if p]
    if path_parts:
        slug = path_parts[-1][:40]
        return f"{hostname}/{slug}"
    return hostname
