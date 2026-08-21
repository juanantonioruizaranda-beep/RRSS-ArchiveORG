"""Orchestration layer between CLI configuration and archive.org client."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Callable

from .config import RunConfig
from .extractor import extract_social_links
from .extractors.corporate_email import extract_emails
from .io import read_sites
from .models import SiteResult, SnapshotInfo
from .proxy import Proxy, ProxyPool, load_proxies
from .utils import domain_from_url
from .wayback import WaybackClient, WaybackError


def process_site(
    client: WaybackClient,
    site: str,
    timestamp: str | None,
) -> SiteResult:
    """Resolve a site through archive.org and extract its social links."""
    result = SiteResult(site=site)
    try:
        snapshot = client.closest_snapshot(site, timestamp=timestamp)
        result.snapshot = SnapshotInfo(
            url=snapshot.archived_url,
            timestamp=snapshot.timestamp,
        )
        html = client.fetch_html(snapshot)
        result.social = extract_social_links(html)
        site_domain = domain_from_url(site)
        corporate, all_found = extract_emails(html, site_domain)
        result.corporate_emails = corporate
        result.all_emails = all_found
    except WaybackError as exc:
        result.error = str(exc)
    return result


def build_client(
    config: RunConfig,
    *,
    proxies: list[Proxy] | None = None,
) -> tuple[WaybackClient, ProxyPool | None]:
    """Create a configured Wayback client and optional proxy pool."""
    proxy_pool: ProxyPool | None = None
    if proxies is None and config.proxies_path is not None:
        proxies = load_proxies(config.proxies_path)
        if not proxies:
            raise ValueError(f"no proxies found in {config.proxies_path}")
    if proxies:
        proxy_pool = ProxyPool(proxies)

    client = WaybackClient(
        timeout=config.timeout,
        max_retries=config.max_retries,
        backoff=config.backoff,
        backoff_max=config.backoff_max,
        proxy_pool=proxy_pool,
    )
    return client, proxy_pool


def run_batch(
    config: RunConfig,
    *,
    log: Callable[[str], None] | None = None,
    on_result: Callable[[SiteResult, int, int], None] | None = None,
) -> list[SiteResult]:
    """Process all configured sites and return structured results."""
    sites = _load_sites(config)
    return run_sites_batch(
        sites,
        timestamp=config.timestamp,
        timeout=config.timeout,
        max_retries=config.max_retries,
        backoff=config.backoff,
        backoff_max=config.backoff_max,
        delay=config.delay,
        proxies_path=config.proxies_path,
        log=log,
        on_result=on_result,
    )


class BatchCancelled(Exception):
    """Raised when a batch run is stopped before all sites are processed."""


def run_sites_batch(
    sites: list[str],
    *,
    timestamp: str | None = None,
    timeout: int = 30,
    max_retries: int = 4,
    backoff: float = 2.0,
    backoff_max: float = 60.0,
    delay: float = 0.0,
    proxies_path: Path | None = None,
    proxies: list[Proxy] | None = None,
    log: Callable[[str], None] | None = None,
    on_result: Callable[[SiteResult, int, int], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> list[SiteResult]:
    """Process an in-memory site list and optionally emit each result."""
    client, proxy_pool = build_client(
        RunConfig(
            sites_path=Path("-"),
            output_path=None,
            output_format="json",
            timestamp=timestamp,
            limit=None,
            timeout=timeout,
            max_retries=max_retries,
            backoff=backoff,
            backoff_max=backoff_max,
            delay=delay,
            proxies_path=proxies_path,
            verbose=False,
        ),
        proxies=proxies,
    )

    if not sites:
        raise ValueError("no websites to process")

    if log and proxy_pool is not None:
        source = "custom list" if proxies else str(proxies_path)
        log(
            f"Using cyclic routes: IP propia + {len(proxy_pool)} proxy/proxies from {source}"
        )

    results: list[SiteResult] = []
    total = len(sites)
    for index, site in enumerate(sites, start=1):
        if should_cancel is not None and should_cancel():
            raise BatchCancelled(f"cancelled after {len(results)} of {total} site(s)")

        if index > 1 and delay > 0:
            _interruptible_sleep(delay, should_cancel)

        if should_cancel is not None and should_cancel():
            raise BatchCancelled(f"cancelled after {len(results)} of {total} site(s)")

        if log:
            log(f"[{index}/{total}] {site}")

        if proxy_pool is not None:
            client.prepare_for_site()
            if log:
                log(f"    route: {proxy_pool.display_current()}")

        item = process_site(client, site, timestamp)
        if log:
            if item.error:
                log(f"    error: {item.error}")
            else:
                social_count = sum(len(values) for values in item.social.values())
                log(
                    f"    found {social_count} social link(s), "
                    f"{len(item.corporate_emails)} corporate email(s)"
                )
        results.append(item)
        if on_result is not None:
            on_result(item, index, total)

    return results


def _interruptible_sleep(
    seconds: float,
    should_cancel: Callable[[], bool] | None,
    *,
    step: float = 0.25,
) -> None:
    """Sleep in short chunks so cancellation can stop between sites quickly."""
    elapsed = 0.0
    while elapsed < seconds:
        if should_cancel is not None and should_cancel():
            return
        chunk = min(step, seconds - elapsed)
        time.sleep(chunk)
        elapsed += chunk


def _load_sites(config: RunConfig) -> list[str]:
    sites = read_sites(config.sites_path)
    if config.limit is not None:
        sites = sites[: config.limit]
    if not sites:
        raise ValueError("no websites to process")
    return sites


def stderr_logger(message: str) -> None:
    print(message, file=sys.stderr)
