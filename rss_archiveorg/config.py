"""Runtime configuration parsed from CLI arguments."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

OutputFormat = Literal["json", "csv"]


@dataclass(frozen=True)
class RunConfig:
    """Validated settings for a single extraction run."""

    sites_path: Path
    output_path: Path | None
    output_format: OutputFormat
    timestamp: str | None
    limit: int | None
    timeout: int
    max_retries: int
    backoff: float
    backoff_max: float
    delay: float
    proxies_path: Path | None
    verbose: bool

    @classmethod
    def from_namespace(cls, args: argparse.Namespace) -> "RunConfig":
        return cls(
            sites_path=args.sites,
            output_path=args.output,
            output_format=args.format,
            timestamp=args.timestamp,
            limit=args.limit,
            timeout=args.timeout,
            max_retries=args.max_retries,
            backoff=args.backoff,
            backoff_max=args.backoff_max,
            delay=args.delay,
            proxies_path=args.proxies,
            verbose=args.verbose,
        )
