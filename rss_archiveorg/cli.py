"""Command-line interface for RSS-ArchiveORG."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from .config import RunConfig
from .io import write_csv, write_json
from .pipeline import run_batch, stderr_logger


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
        "--proxies",
        type=Path,
        metavar="FILE",
        help="Path to a proxy list (host:port or host:port:user:pass per line). "
        "Proxies rotate on 429/5xx errors and between sites.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress to stderr while processing.",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = RunConfig.from_namespace(args)

    if not config.sites_path.exists():
        print(f"error: sites file not found: {config.sites_path}", file=sys.stderr)
        return 2

    if config.proxies_path is not None and not config.proxies_path.exists():
        print(f"error: proxy file not found: {config.proxies_path}", file=sys.stderr)
        return 2

    try:
        results = run_batch(
            config,
            log=stderr_logger if config.verbose else None,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    out = config.output_path.open("w", encoding="utf-8") if config.output_path else sys.stdout
    try:
        if config.output_format == "csv":
            write_csv(results, out)
        else:
            write_json(results, out)
    finally:
        if config.output_path:
            out.close()

    if config.output_path:
        print(
            f"Wrote {len(results)} result(s) to {config.output_path}",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
