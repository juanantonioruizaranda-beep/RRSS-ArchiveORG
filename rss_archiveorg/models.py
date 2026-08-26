"""Shared data models for pipeline input and output."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SnapshotInfo:
    """Metadata for an archive.org snapshot used during extraction."""

    url: str
    timestamp: str


@dataclass
class SiteResult:
    """Extraction outcome for a single input site."""

    site: str
    social: dict[str, list[str]] = field(default_factory=dict)
    corporate_emails: list[str] = field(default_factory=list)
    all_emails: list[str] = field(default_factory=list)
    snapshot: SnapshotInfo | None = None
    error: str | None = None

    @property
    def has_social(self) -> bool:
        return bool(self.social)

    @property
    def has_emails(self) -> bool:
        return bool(self.corporate_emails)

    def warnings(self) -> list[str]:
        """Human-readable notices for missing data on successful fetches."""
        if self.error:
            return []
        notices: list[str] = []
        if not self.has_social:
            notices.append("no_rrss")
        if not self.has_emails:
            notices.append("no_email")
        return notices

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the JSON/CSV-friendly dict shape used by the CLI."""
        payload: dict[str, Any] = {
            "site": self.site,
            "social": self.social,
            "corporate_emails": self.corporate_emails,
            "all_emails": self.all_emails,
            "snapshot": None,
            "error": self.error,
        }
        if self.snapshot is not None:
            payload["snapshot"] = asdict(self.snapshot)
        return payload

    def to_web_dict(self, *, index: int, total: int) -> dict[str, Any]:
        """Serialize for the landing page SSE stream."""
        if self.error:
            status = "error"
        elif not self.has_social and not self.has_emails:
            status = "empty"
        else:
            status = "ok"

        payload = self.to_dict()
        payload.update(
            {
                "type": "result",
                "index": index,
                "total": total,
                "status": status,
                "warnings": self.warnings(),
            }
        )
        return payload
