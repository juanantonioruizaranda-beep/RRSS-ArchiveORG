from __future__ import annotations

import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

PLATFORM_PATTERNS: dict[str, re.Pattern[str]] = {
    "twitter": re.compile(r"(?:twitter\.com|x\.com)/", re.I),
    "facebook": re.compile(r"facebook\.com/", re.I),
    "instagram": re.compile(r"instagram\.com/", re.I),
    "linkedin": re.compile(r"linkedin\.com/", re.I),
    "youtube": re.compile(r"(?:youtube\.com|youtu\.be)/", re.I),
    "tiktok": re.compile(r"tiktok\.com/", re.I),
    "pinterest": re.compile(r"pinterest\.com/", re.I),
    "github": re.compile(r"github\.com/", re.I),
}


def _normalize_social_url(href: str) -> str | None:
    href = href.strip()
    if not href or href.startswith("#"):
        return None
    if href.startswith("//"):
        href = f"https:{href}"
    elif href.startswith("/"):
        return None
    elif not href.startswith(("http://", "https://")):
        return None

    parsed = urlparse(href)
    if not parsed.netloc:
        return None

    return href.rstrip("/")


def extract_social_links(html: str) -> dict[str, list[str]]:
    soup = BeautifulSoup(html, "lxml")
    found: dict[str, set[str]] = {platform: set() for platform in PLATFORM_PATTERNS}

    for anchor in soup.find_all("a", href=True):
        href = _normalize_social_url(anchor["href"])
        if not href:
            continue

        for platform, pattern in PLATFORM_PATTERNS.items():
            if pattern.search(href):
                found[platform].add(href)

    return {platform: sorted(urls) for platform, urls in found.items() if urls}
