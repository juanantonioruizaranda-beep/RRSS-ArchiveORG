from __future__ import annotations

from rss_archiveorg.extractors import extract_emails, extract_social_links
from rss_archiveorg.models import PageResult
from rss_archiveorg.sources.archive_org import fetch_archived_page, resolve_snapshot
from rss_archiveorg.utils import domain_from_url, normalize_url


def process_url(original_url: str) -> PageResult:
    url = normalize_url(original_url)
    site_domain = domain_from_url(url)
    result = PageResult(original_url=url)

    try:
        archive_url, timestamp = resolve_snapshot(url)
    except Exception as exc:  # noqa: BLE001 - surface per-URL failures in output
        result.errors.append(f"No se pudo resolver snapshot: {exc}")
        return result

    if not archive_url:
        result.errors.append("No se encontró snapshot archivado en archive.org")
        return result

    result.archive_url = archive_url
    result.snapshot_timestamp = timestamp

    try:
        html = fetch_archived_page(archive_url)
    except Exception as exc:  # noqa: BLE001
        result.errors.append(f"No se pudo descargar la página archivada: {exc}")
        return result

    result.social_links = extract_social_links(html)
    corporate_emails, all_emails = extract_emails(html, site_domain)
    result.corporate_emails = corporate_emails
    result.all_emails = all_emails
    return result
