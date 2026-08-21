"""Input/output helpers for site lists and result serialization."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import IO, Iterable
from urllib.parse import urlparse

from .models import SiteResult


def normalize_site_url(raw: str) -> str:
    """Validate and return a site URL restricted to HTTP(S)."""
    url = raw.strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"invalid site URL {url!r}; expected http(s)://host")
    return url


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


def write_json(results: Iterable[SiteResult], out: IO[str]) -> None:
    json.dump([result.to_dict() for result in results], out, indent=2, ensure_ascii=False)
    out.write("\n")


def write_csv(results: Iterable[SiteResult], out: IO[str]) -> None:
    writer = csv.writer(out)
    writer.writerow(["site", "network", "profile_url", "snapshot_timestamp", "error"])
    for item in results:
        timestamp = item.snapshot.timestamp if item.snapshot else ""
        if item.error:
            writer.writerow([item.site, "", "", timestamp, item.error])
            continue
        if not item.social:
            writer.writerow([item.site, "", "", timestamp, ""])
            continue
        for network, links in item.social.items():
            for link in links:
                writer.writerow([item.site, network, link, timestamp, ""])
