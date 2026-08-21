"""RSS-ArchiveORG: extract social network (RRSS) links from a list of websites
using snapshots stored in the Internet Archive's Wayback Machine (archive.org).
"""

from .extractor import SOCIAL_NETWORKS, extract_social_links
from .models import SiteResult, SnapshotInfo
from .proxy import Proxy, ProxyPool, load_proxies
from .wayback import WaybackClient, WaybackError, Snapshot

__all__ = [
    "SOCIAL_NETWORKS",
    "SiteResult",
    "SnapshotInfo",
    "extract_social_links",
    "Proxy",
    "ProxyPool",
    "load_proxies",
    "WaybackClient",
    "WaybackError",
    "Snapshot",
]

__version__ = "0.1.0"
