from __future__ import annotations

import httpx

from rss_archiveorg.utils import normalize_url

CDX_API = "https://web.archive.org/cdx/search/cdx"
USER_AGENT = "RSS-ArchiveORG/0.1 (+https://github.com/juanantonioruizaranda-beep/RSS-ArchiveORG)"


def resolve_snapshot(original_url: str, timeout: float = 30.0) -> tuple[str | None, str | None]:
    """Resolve the latest archived snapshot for a URL via the CDX API."""
    url = normalize_url(original_url)
    params = {
        "url": url,
        "output": "json",
        "filter": "statuscode:200",
        "limit": "1",
        "sort": "timestamp:desc",
    }

    with httpx.Client(timeout=timeout, headers={"User-Agent": USER_AGENT}) as client:
        response = client.get(CDX_API, params=params)
        response.raise_for_status()
        rows = response.json()

    if len(rows) < 2:
        return None, None

    _, timestamp, _, _, _ = rows[1]
    archive_url = f"https://web.archive.org/web/{timestamp}/{url}"
    return archive_url, timestamp


def fetch_archived_page(archive_url: str, timeout: float = 30.0) -> str:
    with httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        response = client.get(archive_url)
        response.raise_for_status()
        return response.text
