"""Detect and normalize social network (RRSS) links found in HTML pages."""

from __future__ import annotations

import re
from typing import Dict, List
from urllib.parse import urlparse, unquote

from bs4 import BeautifulSoup

# Map a canonical network name to the host substrings that identify it.
SOCIAL_NETWORKS: Dict[str, tuple] = {
    "facebook": ("facebook.com", "fb.com", "fb.me"),
    "twitter": ("twitter.com", "x.com"),
    "instagram": ("instagram.com",),
    "linkedin": ("linkedin.com",),
    "youtube": ("youtube.com", "youtu.be"),
    "tiktok": ("tiktok.com",),
    "pinterest": ("pinterest.com", "pinterest.es"),
    "telegram": ("t.me", "telegram.me"),
    "whatsapp": ("wa.me", "whatsapp.com"),
    "vimeo": ("vimeo.com",),
    "flickr": ("flickr.com",),
    "spotify": ("open.spotify.com",),
}

# Wayback Machine rewrites outbound links as /web/<timestamp>/<original-url>.
# This strips the archive prefix so we recover the real destination.
_WAYBACK_PREFIX = re.compile(r"^(?:https?://[^/]*web\.archive\.org)?/?web/\d+[a-z_]*/", re.IGNORECASE)


def _clean_href(href: str) -> str:
    """Remove any Wayback Machine rewriting from an href and normalize it."""
    href = href.strip()
    match = _WAYBACK_PREFIX.match(href)
    if match:
        rest = href[match.end():]
        if rest.lower().startswith(("http://", "https://")):
            href = rest
        elif rest.startswith("//"):
            href = "https:" + rest
        else:
            href = "https://" + rest
    return unquote(href)


def _classify(url: str) -> str | None:
    """Return the social network name for a URL, or None if it is not social."""
    host = (urlparse(url).netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    for network, hosts in SOCIAL_NETWORKS.items():
        for candidate in hosts:
            if host == candidate or host.endswith("." + candidate):
                return network
    return None


def extract_social_links(html: str) -> Dict[str, List[str]]:
    """Parse HTML and return a mapping of network name -> sorted unique links.

    Only networks with at least one match are included in the result.
    """
    soup = BeautifulSoup(html, "lxml")
    found: Dict[str, set] = {}

    for anchor in soup.find_all("a", href=True):
        url = _clean_href(anchor["href"])
        if not url.lower().startswith(("http://", "https://")):
            continue
        network = _classify(url)
        if network is None:
            continue
        found.setdefault(network, set()).add(url)

    return {network: sorted(links) for network, links in sorted(found.items())}
