"""Shared URL and email helpers."""

from __future__ import annotations

from urllib.parse import urlparse

FREE_EMAIL_DOMAINS = frozenset(
    {
        "gmail.com",
        "googlemail.com",
        "hotmail.com",
        "outlook.com",
        "live.com",
        "yahoo.com",
        "yahoo.es",
        "icloud.com",
        "protonmail.com",
        "proton.me",
        "aol.com",
        "mail.com",
        "gmx.com",
        "gmx.es",
        "yandex.com",
        "zoho.com",
    }
)


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url:
        return url
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    path = parsed.path or ""
    if parsed.query:
        path = f"{path}?{parsed.query}"
    return f"https://{host}{path}"


def domain_from_url(url: str) -> str:
    parsed = urlparse(normalize_url(url))
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def email_matches_domain(email: str, site_domain: str) -> bool:
    if "@" not in email:
        return False

    email_domain = email.rsplit("@", 1)[1].lower()
    site_domain = site_domain.lower().strip()
    if not site_domain:
        return False

    if email_domain in FREE_EMAIL_DOMAINS:
        return False

    if email_domain == site_domain:
        return True

    return email_domain.endswith(f".{site_domain}")
