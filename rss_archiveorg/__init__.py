"""RSS-ArchiveORG: extract social network (RRSS) links from a list of websites
using snapshots stored in the Internet Archive's Wayback Machine (archive.org).
"""

from .extractor import SOCIAL_NETWORKS, extract_social_links
from .wayback import WaybackClient, WaybackError, Snapshot

__all__ = [
    "SOCIAL_NETWORKS",
    "extract_social_links",
    "WaybackClient",
    "WaybackError",
    "Snapshot",
]

__version__ = "0.1.0"
