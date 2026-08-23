"""Input/output helpers for site lists and result serialization."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import IO, Iterable, Mapping, Any
from urllib.parse import urlparse

from .models import SiteResult
from .utils import normalize_url


def normalize_site_url(raw: str) -> str:
    """Validate and return a site URL restricted to HTTP(S).

    Bare domains such as ``example.com`` are accepted and normalized to
    ``https://example.com``.
    """
    url = raw.strip()
    if not url:
        raise ValueError(f"invalid site URL {raw!r}; expected http(s)://host")

    if "://" in url:
        scheme = urlparse(url).scheme
        if scheme not in {"http", "https"}:
            raise ValueError(f"invalid site URL {raw!r}; expected http(s)://host")

    normalized = normalize_url(url)
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"invalid site URL {raw!r}; expected http(s)://host")
    return normalized


def read_sites(path: Path) -> list[str]:
    """Read a newline-delimited list of websites, ignoring blanks and comments."""
    sites: list[str] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            sites.append(normalize_site_url(stripped))
        except ValueError as exc:
            raise ValueError(f"{path}:{line_no}: {exc}") from exc
    return sites


def parse_sites_text(raw: str) -> list[str]:
    """Parse newline-delimited URLs from form input."""
    sites: list[str] = []
    for line_no, line in enumerate(raw.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            sites.append(normalize_site_url(stripped))
        except ValueError as exc:
            raise ValueError(f"line {line_no}: {exc}") from exc
    return sites


def write_json(results: Iterable[SiteResult], out: IO[str]) -> None:
    json.dump([result.to_dict() for result in results], out, indent=2, ensure_ascii=False)
    out.write("\n")


def write_csv(results: Iterable[SiteResult], out: IO[str]) -> None:
    writer = csv.writer(out)
    writer.writerow(
        [
            "site",
            "status",
            "network",
            "profile_url",
            "email",
            "email_type",
            "snapshot_timestamp",
            "error",
        ]
    )
    for item in results:
        timestamp = item.snapshot.timestamp if item.snapshot else ""
        status = _result_status(item)
        if item.error:
            writer.writerow([item.site, status, "", "", "", "", timestamp, item.error])
            continue

        wrote_row = False
        for network, links in item.social.items():
            for link in links:
                writer.writerow([item.site, status, network, link, "", "", timestamp, ""])
                wrote_row = True
        for email in item.corporate_emails:
            writer.writerow([item.site, status, "", "", email, "corporate", timestamp, ""])
            wrote_row = True
        for email in item.all_emails:
            if email in item.corporate_emails:
                continue
            writer.writerow([item.site, status, "", "", email, "other", timestamp, ""])
            wrote_row = True
        if not wrote_row:
            writer.writerow([item.site, status, "", "", "", "", timestamp, ""])


def _result_status(item: SiteResult) -> str:
    if item.error:
        return "error"
    if not item.social and not item.corporate_emails and not item.all_emails:
        return "empty"
    return "ok"


def results_to_json_text(results: Iterable[Mapping[str, Any]]) -> str:
    return json.dumps(list(results), indent=2, ensure_ascii=False) + "\n"


def results_to_csv_text(results: Iterable[Mapping[str, Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "site",
            "status",
            "network",
            "profile_url",
            "email",
            "email_type",
            "snapshot_timestamp",
            "error",
        ]
    )
    for item in results:
        timestamp = (item.get("snapshot") or {}).get("timestamp", "")
        status = item.get("status", "")
        error = item.get("error") or ""
        if error:
            writer.writerow([item.get("site", ""), status, "", "", "", "", timestamp, error])
            continue

        wrote_row = False
        social = item.get("social") or {}
        for network, links in social.items():
            for link in links:
                writer.writerow([item.get("site", ""), status, network, link, "", "", timestamp, ""])
                wrote_row = True
        corporate = item.get("corporate_emails") or []
        for email in corporate:
            writer.writerow([item.get("site", ""), status, "", "", email, "corporate", timestamp, ""])
            wrote_row = True
        all_emails = item.get("all_emails") or []
        corporate_set = set(corporate)
        for email in all_emails:
            if email in corporate_set:
                continue
            writer.writerow([item.get("site", ""), status, "", "", email, "other", timestamp, ""])
            wrote_row = True
        if not wrote_row:
            writer.writerow([item.get("site", ""), status, "", "", "", "", timestamp, ""])
    return buffer.getvalue()
