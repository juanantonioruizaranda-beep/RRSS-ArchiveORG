"""Thin client for the Internet Archive Wayback Machine (archive.org)."""

from __future__ import annotations

import gzip
import time
import zlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

import requests

if TYPE_CHECKING:
    from .proxy import ProxyPool

AVAILABILITY_API = "https://archive.org/wayback/available"
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 4
DEFAULT_BACKOFF = 2.0
DEFAULT_BACKOFF_MAX = 60.0
USER_AGENT = "RSS-ArchiveORG/0.1 (+https://github.com/juanantonioruizaranda-beep/RSS-ArchiveORG)"

# Status codes worth retrying: archive.org throttles content endpoints with 429
# and occasionally returns transient 5xx errors under load.
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class WaybackError(RuntimeError):
    """Raised when a website cannot be resolved or fetched from archive.org."""


@dataclass
class Snapshot:
    """A single archived snapshot of a URL."""

    original_url: str
    archived_url: str
    timestamp: str
    status: str


class WaybackClient:
    """Look up and fetch archived snapshots from the Wayback Machine."""

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        session: Optional[requests.Session] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff: float = DEFAULT_BACKOFF,
        backoff_max: float = DEFAULT_BACKOFF_MAX,
        proxy_pool: Optional["ProxyPool"] = None,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff = backoff
        self.backoff_max = backoff_max
        self.proxy_pool = proxy_pool
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", USER_AGENT)
        if self.proxy_pool is not None:
            self.proxy_pool.apply_to_session(self.session)

    def _get(self, url: str, params: Optional[dict] = None) -> requests.Response:
        """GET with retry/backoff for throttling (429) and transient 5xx errors."""
        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            if self.proxy_pool is not None:
                self.proxy_pool.apply_to_session(self.session)

            retry_after: Optional[float] = None
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
            except requests.RequestException as exc:
                last_exc = exc
                if self.proxy_pool is not None:
                    self.proxy_pool.rotate()
            else:
                if resp.status_code not in _RETRYABLE_STATUS:
                    return resp
                last_exc = requests.HTTPError(
                    f"{resp.status_code} {resp.reason}", response=resp
                )
                retry_after = self._retry_after_seconds(resp)
                if self.proxy_pool is not None:
                    self.proxy_pool.rotate()
            if attempt < self.max_retries:
                delay = retry_after or min(self.backoff * (2 ** attempt), self.backoff_max)
                time.sleep(delay)
        assert last_exc is not None
        raise last_exc

    def prepare_for_site(self) -> None:
        """Rotate to the next proxy before processing a new site."""
        if self.proxy_pool is not None:
            self.proxy_pool.rotate_for_site()
            self.proxy_pool.apply_to_session(self.session)

    @staticmethod
    def _retry_after_seconds(resp: requests.Response) -> Optional[float]:
        value = resp.headers.get("Retry-After")
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    def closest_snapshot(self, url: str, timestamp: Optional[str] = None) -> Snapshot:
        """Return the closest available snapshot for ``url``.

        ``timestamp`` is an optional YYYYMMDD[hhmmss] hint; the API returns the
        snapshot nearest to it (or the most recent one when omitted).
        """
        params = {"url": url}
        if timestamp:
            params["timestamp"] = timestamp

        try:
            resp = self._get(AVAILABILITY_API, params=params)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as exc:
            raise WaybackError(f"availability lookup failed for {url}: {exc}") from exc

        closest = (data.get("archived_snapshots") or {}).get("closest")
        if not closest or not closest.get("available"):
            raise WaybackError(f"no archived snapshot available for {url}")

        return Snapshot(
            original_url=url,
            archived_url=closest["url"],
            timestamp=closest.get("timestamp", ""),
            status=closest.get("status", ""),
        )

    def fetch_html(self, snapshot: Snapshot, raw: bool = False) -> str:
        """Download the archived HTML for a snapshot.

        By default this fetches the Wayback Machine's rendered page, which the
        service serves as decompressed ``text/html`` (outbound links are rewritten
        as ``/web/<timestamp>/<url>`` and unwrapped again by the extractor).

        When ``raw`` is true the ``id_`` modifier requests the original captured
        response instead; that content may still carry its original transfer
        encoding, so the rendered page is preferred for reliable parsing.
        """
        fetch_url = self._raw_url(snapshot) if raw else snapshot.archived_url
        try:
            resp = self._get(fetch_url)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise WaybackError(f"failed to fetch snapshot {fetch_url}: {exc}") from exc
        return self._decode_body(resp)

    @staticmethod
    def _decode_body(resp: requests.Response) -> str:
        """Return response text, transparently decompressing raw gzip bodies.

        The ``id_`` endpoint can serve the original captured bytes with their
        stored gzip encoding but without a ``Content-Encoding`` header, so
        ``requests`` does not auto-decompress. Detect the gzip magic bytes and
        decompress manually in that case.
        """
        content = resp.content
        if content[:2] == b"\x1f\x8b":
            try:
                content = gzip.decompress(content)
            except (OSError, zlib.error):
                return resp.text
            encoding = resp.encoding or resp.apparent_encoding or "utf-8"
            return content.decode(encoding, errors="replace")
        return resp.text

    @staticmethod
    def _raw_url(snapshot: Snapshot) -> str:
        marker = "/web/"
        idx = snapshot.archived_url.find(marker)
        if idx == -1 or not snapshot.timestamp:
            return snapshot.archived_url
        tail = snapshot.archived_url[idx + len(marker) + len(snapshot.timestamp):]
        prefix = snapshot.archived_url[: idx + len(marker)]
        return f"{prefix}{snapshot.timestamp}id_{tail}"
