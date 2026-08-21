"""Orchestration layer between CLI configuration and archive.org client."""

from __future__ import annotations

import sys
import time
from typing import Callable

from .config import RunConfig
from .extractor import extract_social_links
from .io import read_sites
from .models import SiteResult, SnapshotInfo
from .proxy import ProxyPool, load_proxies
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
    except WaybackError as exc:
        result.error = str(exc)
    return result


def build_client(config: RunConfig) -> tuple[WaybackClient, ProxyPool | None]:
    """Create a configured Wayback client and optional proxy pool."""
    proxy_pool: ProxyPool | None = None
    if config.proxies_path is not None:
        proxies = load_proxies(config.proxies_path)
        if not proxies:
            raise ValueError(f"no proxies found in {config.proxies_path}")
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
) -> list[SiteResult]:
    """Process all configured sites and return structured results."""
    client, proxy_pool = build_client(config)
    sites = _load_sites(config)

    if log and proxy_pool is not None:
        log(
            f"Using {len(proxy_pool)} proxy/proxies from {config.proxies_path}"
        )

    results: list[SiteResult] = []
    for index, site in enumerate(sites, start=1):
        if index > 1 and config.delay > 0:
            time.sleep(config.delay)

        if log:
            log(f"[{index}/{len(sites)}] {site}")

        if proxy_pool is not None:
            client.prepare_for_site()
            if log:
                proxy = proxy_pool.current
                log(f"    proxy: {proxy.display_host()}")

        item = process_site(client, site, config.timestamp)
        if log:
            if item.error:
                log(f"    error: {item.error}")
            else:
                total = sum(len(values) for values in item.social.values())
                log(f"    found {total} social link(s)")
        results.append(item)

    return results


def _load_sites(config: RunConfig) -> list[str]:
    sites = read_sites(config.sites_path)
    if config.limit is not None:
        sites = sites[: config.limit]
    if not sites:
        raise ValueError("no websites to process")
    return sites


def stderr_logger(message: str) -> None:
    print(message, file=sys.stderr)
