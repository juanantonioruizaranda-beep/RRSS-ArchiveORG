"""Proxy list parsing and round-robin rotation for archive.org requests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional
from urllib.parse import quote


@dataclass(frozen=True)
class Proxy:
    """HTTP proxy with optional authentication."""

    host: str
    port: int
    username: str = ""
    password: str = ""

    def requests_dict(self) -> dict[str, str]:
        """Return a ``requests``-compatible per-scheme proxy mapping."""
        if self.username or self.password:
            auth = f"{quote(self.username, safe='')}:{quote(self.password, safe='')}"
            proxy_url = f"http://{auth}@{self.host}:{self.port}"
        else:
            proxy_url = f"http://{self.host}:{self.port}"
        return {"http": proxy_url, "https": proxy_url}

    @classmethod
    def parse(cls, line: str) -> Optional["Proxy"]:
        """Parse ``host:port`` or ``host:port:user:pass`` lines."""
        line = line.strip()
        if not line or line.startswith("#"):
            return None

        parts = line.split(":")
        if len(parts) == 2:
            host, port = parts
            return cls(host=host, port=int(port))
        if len(parts) == 4:
            host, port, username, password = parts
            return cls(
                host=host,
                port=int(port),
                username=username,
                password=password,
            )
        raise ValueError(
            f"invalid proxy format {line!r}; expected host:port or host:port:user:pass"
        )


def load_proxies(path: Path) -> list[Proxy]:
    """Load proxies from a newline-delimited text file."""
    proxies: list[Proxy] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        proxy = Proxy.parse(line)
        if proxy is not None:
            proxies.append(proxy)
    return proxies


class ProxyPool:
    """Round-robin pool that rotates proxies on rate limits or connection errors."""

    def __init__(self, proxies: list[Proxy]):
        if not proxies:
            raise ValueError("proxy pool requires at least one proxy")
        self._proxies = list(proxies)
        self._index = 0

    def __len__(self) -> int:
        return len(self._proxies)

    def __iter__(self) -> Iterator[Proxy]:
        return iter(self._proxies)

    @property
    def current(self) -> Proxy:
        return self._proxies[self._index]

    def apply_to_session(self, session) -> None:
        """Set the active proxy on a ``requests.Session``."""
        session.proxies.clear()
        session.proxies.update(self.current.requests_dict())

    def rotate(self) -> Proxy:
        """Advance to the next proxy and return it."""
        self._index = (self._index + 1) % len(self._proxies)
        return self.current

    def rotate_for_site(self) -> Proxy:
        """Spread load by using a different proxy for each site."""
        return self.rotate()
