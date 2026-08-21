from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class PageResult:
    original_url: str
    archive_url: str | None = None
    snapshot_timestamp: str | None = None
    social_links: dict[str, list[str]] = field(default_factory=dict)
    corporate_emails: list[str] = field(default_factory=list)
    all_emails: list[str] = field(default_factory=list)
    fetched_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    errors: list[str] = field(default_factory=list)
