"""Command-line interface for RSS-ArchiveORG."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Dict, List

from .extractor import extract_social_links
from .wayback import WaybackClient, WaybackError


def read_sites(path: Path) -> List[str]:
    """Read a newline-delimited list of websites, ignoring blanks and comments."""
    sites: List[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        sites.append(line)
    return sites


def process_site(client: WaybackClient, site: str, timestamp: str | None) -> Dict:
    """Resolve a site through archive.org and extract its social links."""
    result: Dict = {"site": site, "social": {}, "snapshot": None, "error": None}
    try:
        snapshot = client.closest_snapshot(site, timestamp=timestamp)
        result["snapshot"] = {
            "url": snapshot.archived_url,
            "timestamp": snapshot.timestamp,
        }
        html = client.fetch_html(snapshot)
        result["social"] = extract_social_links(html)
    except WaybackError as exc:
        result["error"] = str(exc)
    return result


def write_json(results: List[Dict], out) -> None:
    json.dump(results, out, indent=2, ensure_ascii=False)
    out.write("\n")


def write_csv(results: List[Dict], out) -> None:
    writer = csv.writer(out)
    writer.writerow(["site", "network", "profile_url", "snapshot_timestamp", "error"])
    for item in results:
        ts = (item.get("snapshot") or {}).get("timestamp", "")
        if item["error"]:
            writer.writerow([item["site"], "", "", ts, item["error"]])
            continue
        social = item["social"]
        if not social:
            writer.writerow([item["site"], "", "", ts, ""])
            continue
        for network, links in social.items():
            for link in links:
                writer.writerow([item["site"], network, link, ts, ""])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rss-archiveorg",
        description="Extract social network (RRSS) links from a list of websites "
        "using archive.org snapshots.",
    )
    parser.add_argument(
        "sites",
        type=Path,
        help="Path to a text file with one website URL per line.",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Write results to this file instead of stdout.",
    )
    parser.add_argument(
        "-f", "--format",
        choices=("json", "csv"),
        default="json",
        help="Output format (default: json).",
    )
    parser.add_argument(
        "-t", "--timestamp",
        help="Preferred snapshot date as YYYYMMDD[hhmmss] (default: most recent).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Only process the first N sites (useful for quick checks).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Per-request timeout in seconds (default: 30).",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=4,
        help="Retries for throttled (429) or transient errors (default: 4).",
    )
    parser.add_argument(
        "--backoff",
        type=float,
        default=2.0,
        help="Base seconds for exponential backoff between retries (default: 2).",
    )
    parser.add_argument(
        "--backoff-max",
        type=float,
        default=60.0,
        help="Cap in seconds for the backoff between retries (default: 60).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Seconds to wait between sites to stay under archive.org rate limits.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress to stderr while processing.",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.sites.exists():
        print(f"error: sites file not found: {args.sites}", file=sys.stderr)
        return 2

    sites = read_sites(args.sites)
    if args.limit is not None:
        sites = sites[: args.limit]
    if not sites:
        print("error: no websites to process", file=sys.stderr)
        return 2

    client = WaybackClient(
        timeout=args.timeout,
        max_retries=args.max_retries,
        backoff=args.backoff,
        backoff_max=args.backoff_max,
    )
    results: List[Dict] = []
    for index, site in enumerate(sites, start=1):
        if index > 1 and args.delay > 0:
            time.sleep(args.delay)
        if args.verbose:
            print(f"[{index}/{len(sites)}] {site}", file=sys.stderr)
        item = process_site(client, site, args.timestamp)
        if args.verbose:
            if item["error"]:
                print(f"    error: {item['error']}", file=sys.stderr)
            else:
                total = sum(len(v) for v in item["social"].values())
                print(f"    found {total} social link(s)", file=sys.stderr)
        results.append(item)

    out = args.output.open("w", encoding="utf-8") if args.output else sys.stdout
    try:
        if args.format == "csv":
            write_csv(results, out)
        else:
            write_json(results, out)
    finally:
        if args.output:
            out.close()

    if args.output:
        print(f"Wrote {len(results)} result(s) to {args.output}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
