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
    snapshot: SnapshotInfo | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the JSON/CSV-friendly dict shape used by the CLI."""
        payload: dict[str, Any] = {
            "site": self.site,
            "social": self.social,
            "snapshot": None,
            "error": self.error,
        }
        if self.snapshot is not None:
            payload["snapshot"] = asdict(self.snapshot)
        return payload
