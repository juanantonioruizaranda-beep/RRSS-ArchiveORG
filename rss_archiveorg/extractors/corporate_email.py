"""Extract corporate and general email addresses from archived HTML."""

from __future__ import annotations

import html
import re

from bs4 import BeautifulSoup

from rss_archiveorg.utils import email_matches_domain

EMAIL_CORE = (
    r"[a-zA-Z0-9][a-zA-Z0-9._%+\-]*@"
    r"[a-zA-Z0-9](?:[a-zA-Z0-9.\-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}"
)
EMAIL_PATTERN = re.compile(EMAIL_CORE, re.I)
EMAIL_BOUNDED_PATTERN = re.compile(
    rf"(?<![A-Za-z0-9._%+\-]){EMAIL_CORE}(?![A-Za-z0-9._%+\-])",
    re.I,
)
OBFUSCATED_AT_PATTERN = re.compile(
    r"([a-zA-Z0-9._%+\-]+)\s*(?:\[?\s*(?:at|\(at\)|&#64;|&commat;)\s*\]?)\s*"
    r"([a-zA-Z0-9.\-]+)\s*(?:\[?\s*(?:dot|\.|\(dot\)|&#46;|&period;)\s*\]?)\s*"
    r"([a-zA-Z]{2,})",
    re.I,
)


def _decode_text(text: str) -> str:
    return html.unescape(text)


def _normalize_email(raw: str) -> str | None:
    email = raw.strip().lower()
    email = email.removeprefix("mailto:")
    if "?" in email:
        email = email.split("?", 1)[0]
    email = email.strip(".,;:\"'<>()[]")

    if not EMAIL_PATTERN.fullmatch(email):
        return None

    local, _, domain = email.partition("@")
    if (
        not local
        or not domain
        or ".." in email
        or local.startswith(".")
        or local.endswith(".")
        or domain.startswith(".")
        or domain.endswith(".")
        or ".." in domain
    ):
        return None

    return email


def _extract_from_mailto(soup: BeautifulSoup) -> set[str]:
    emails: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href.lower().startswith("mailto:"):
            continue
        normalized = _normalize_email(href)
        if normalized:
            emails.add(normalized)
    return emails


def _extract_from_text(text: str) -> set[str]:
    emails: set[str] = set()
    decoded = _decode_text(text)

    for match in EMAIL_BOUNDED_PATTERN.findall(decoded):
        normalized = _normalize_email(match)
        if normalized:
            emails.add(normalized)

    for local, domain, tld in OBFUSCATED_AT_PATTERN.findall(decoded):
        candidate = f"{local}@{domain}.{tld}"
        normalized = _normalize_email(candidate)
        if normalized:
            emails.add(normalized)

    return emails


def extract_emails(html: str, site_domain: str) -> tuple[list[str], list[str]]:
    """Return (corporate_emails, all_emails) found in page HTML.

    Only emails whose domain matches the searched site are returned.
    """
    soup = BeautifulSoup(html, "lxml")

    for tag in soup.find_all(["script", "style", "noscript"]):
        tag.decompose()

    all_found: set[str] = set()
    all_found.update(_extract_from_mailto(soup))
    all_found.update(_extract_from_text(soup.get_text(" ", strip=True)))

    for meta in soup.find_all("meta"):
        for attr in ("content", "name"):
            value = meta.get(attr)
            if value:
                all_found.update(_extract_from_text(str(value)))

    domain_emails = sorted(
        email for email in all_found if email_matches_domain(email, site_domain)
    )
    corporate_emails = domain_emails
    return corporate_emails, domain_emails
