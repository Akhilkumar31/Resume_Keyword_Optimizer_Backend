"""Job description scraper using BeautifulSoup for clean text extraction."""

import re
import logging
from typing import Optional, Tuple

import requests
from bs4 import BeautifulSoup, Tag
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Tags whose entire subtrees should be discarded before extraction
_DISCARD_TAGS = {
    "script", "style", "noscript", "nav", "footer", "header",
    "aside", "form", "iframe", "button", "svg", "img",
}

# CSS class/id substrings that suggest a container holds the main job content.
# Checked in priority order — first match wins.
_JOB_CONTENT_HINTS = [
    "job-description", "jobdescription", "job_description",
    "job-detail", "jobdetail", "job_detail",
    "job-body", "jobbody",
    "description", "job-content", "jobcontent",
    "posting-description", "listing-description",
    "details", "content", "main",
]

# CSS class/id substrings that suggest a container is boilerplate
_BOILERPLATE_HINTS = [
    "cookie", "banner", "modal", "popup", "ad-", "-ad",
    "advertisement", "promo", "newsletter", "subscribe",
    "sidebar", "breadcrumb", "pagination", "share", "social",
    "related", "recommended", "similar-jobs",
]

# Minimum character length for a text line to be kept
_MIN_LINE_LENGTH = 30


def _is_boilerplate_element(tag: Tag) -> bool:
    """Return True if a tag looks like boilerplate (ads, cookies, etc.)."""
    class_str = " ".join(tag.get("class", []))
    id_str = tag.get("id", "")
    combined = (class_str + " " + id_str).lower()
    return any(hint in combined for hint in _BOILERPLATE_HINTS)


def _find_job_container(soup: BeautifulSoup) -> Optional[Tag]:
    """
    Try to locate the HTML element most likely to hold the job description.

    Searches <div>, <section>, and <article> elements whose class or id
    contains one of the known job-content hint strings.  Returns the first
    match, or None if no heuristic match is found.
    """
    for hint in _JOB_CONTENT_HINTS:
        # Search by class attribute (partial match)
        for tag in soup.find_all(["div", "section", "article"]):
            if _is_boilerplate_element(tag):
                continue
            class_str = " ".join(tag.get("class", []))
            id_str = tag.get("id", "")
            combined = (class_str + " " + id_str).lower()
            if hint in combined:
                return tag
    return None


def _extract_text_from_container(container: Tag) -> str:
    """
    Extract clean text from a container by focusing on paragraph and list
    elements, which carry the bulk of meaningful job description content.
    """
    parts: list[str] = []

    for element in container.find_all(["p", "li", "h1", "h2", "h3", "h4", "h5", "h6"]):
        text = element.get_text(separator=" ", strip=True)
        if text:
            parts.append(text)

    return "\n".join(parts)


def _extract_text_full_page(soup: BeautifulSoup) -> str:
    """
    Fallback: extract paragraphs and list items from the whole page body
    when no job-specific container is detected.
    """
    body = soup.find("body") or soup
    parts: list[str] = []

    for element in body.find_all(["p", "li", "h1", "h2", "h3", "h4", "h5", "h6"]):
        # Skip elements inside boilerplate parents
        parent = element.parent
        if parent and _is_boilerplate_element(parent):
            continue
        text = element.get_text(separator=" ", strip=True)
        if text:
            parts.append(text)

    return "\n".join(parts)


def _clean_text(raw: str) -> str:
    """
    Normalise extracted text:
    - Collapse multiple spaces / tabs into a single space per line
    - Remove lines that are too short to be meaningful (likely nav items)
    - Collapse runs of blank lines into a single blank line
    - Strip leading/trailing whitespace
    """
    lines = raw.splitlines()
    cleaned: list[str] = []

    for line in lines:
        # Collapse internal whitespace
        line = re.sub(r"[ \t]+", " ", line).strip()

        # Drop very short lines (navigation labels, button text, etc.)
        if line and len(line) < _MIN_LINE_LENGTH:
            # Keep headings even if short (they provide structure)
            if not re.search(r"[A-Z]", line):
                continue

        cleaned.append(line)

    # Join and collapse multiple consecutive blank lines
    text = "\n".join(cleaned)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_title(soup: BeautifulSoup) -> Optional[str]:
    """Return a best-effort page title."""
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    return None


def scrape_job_description(url: str) -> Tuple[str, Optional[str]]:
    """
    Fetch a webpage and return ``(clean_text, page_title)``.

    Raises:
        ValueError: For invalid or empty URL.
        requests.exceptions.Timeout: When the server takes too long.
        requests.exceptions.ConnectionError: When the host is unreachable.
        requests.exceptions.HTTPError: On 4xx/5xx HTTP responses.
        RuntimeError: When the page yields no meaningful text.
    """
    url = url.strip()
    if not url:
        raise ValueError("URL cannot be empty")

    # Prepend scheme if missing
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)
    if not parsed.netloc:
        raise ValueError(f"Invalid URL format: {url!r}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    response = requests.get(url, timeout=10, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    # Remove boilerplate subtrees entirely before any extraction
    for tag in soup(_DISCARD_TAGS):
        tag.decompose()

    title = _extract_title(soup)

    # Try focused extraction from a job-content container first
    container = _find_job_container(soup)
    if container:
        logger.info("Job content container found; using focused extraction")
        raw_text = _extract_text_from_container(container)
    else:
        logger.info("No job container found; falling back to full-page extraction")
        raw_text = _extract_text_full_page(soup)

    clean = _clean_text(raw_text)

    if not clean:
        raise RuntimeError("No meaningful text content found on the webpage")

    return clean, title
