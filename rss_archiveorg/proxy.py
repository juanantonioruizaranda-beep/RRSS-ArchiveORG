"""Proxy list parsing and round-robin rotation for archive.org requests."""

from __future__ import annotations

import ipaddress
import re
import stat
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional
from urllib.parse import quote

_HOSTNAME_RE = re.compile(
    r"^[a-zA-Z0-9](?:[a-zA-Z0-9.-]{0,253}[a-zA-Z0-9])?$"
)


def _validate_host(host: str) -> str:
    host = host.strip()
    if not host:
        raise ValueError("empty proxy host")
    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        pass
    if _HOSTNAME_RE.match(host):
        return host
    raise ValueError(f"invalid proxy host {host!r}")


def _validate_port(port: int) -> int:
    if not 1 <= port <= 65535:
        raise ValueError(f"invalid proxy port {port}")
    return port


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

    def display_host(self) -> str:
        """Return a log-safe host:port label without credentials."""
        return f"{self.host}:{self.port}"

    def __repr__(self) -> str:
        if self.password:
            return (
                f"Proxy(host={self.host!r}, port={self.port}, "
                f"username={self.username!r}, password='***')"
            )
        return f"Proxy(host={self.host!r}, port={self.port})"

    @classmethod
    def parse(cls, line: str) -> Optional["Proxy"]:
        """Parse ``host:port`` or ``host:port:user:pass`` lines."""
        line = line.strip()
        if not line or line.startswith("#"):
            return None

        parts = line.split(":")
        if len(parts) == 2:
            host, port_text = parts
            return cls(
                host=_validate_host(host),
                port=_validate_port(int(port_text)),
            )
        if len(parts) >= 4:
            host, port_text, username = parts[0], parts[1], parts[2]
            password = ":".join(parts[3:])
            return cls(
                host=_validate_host(host),
                port=_validate_port(int(port_text)),
                username=username,
                password=password,
            )
        raise ValueError(
            f"invalid proxy format {line!r}; expected host:port or host:port:user:pass"
        )


def _warn_if_world_readable(path: Path) -> None:
    if not path.exists():
        return
    mode = path.stat().st_mode
    if mode & (stat.S_IRWXG | stat.S_IRWXO):
        warnings.warn(
            f"proxy file {path} is readable by group or others; use chmod 600",
            stacklevel=3,
        )


def load_proxies(path: Path) -> list[Proxy]:
    """Load proxies from a newline-delimited text file."""
    _warn_if_world_readable(path)
    return parse_proxies_text(
        path.read_text(encoding="utf-8"),
        source_label=str(path),
    )


def parse_proxies_text(raw: str, *, source_label: str = "input") -> list[Proxy]:
    """Parse newline-delimited proxy lines from pasted text or file contents."""
    proxies: list[Proxy] = []
    for line_no, line in enumerate(raw.splitlines(), start=1):
        try:
            proxy = Proxy.parse(line)
        except ValueError as exc:
            raise ValueError(f"{source_label}:{line_no}: {exc}") from exc
        if proxy is not None:
            proxies.append(proxy)
    return proxies


def resolve_proxies_for_run(
    *,
    enabled: bool,
    proxies_text: str | None = None,
    fallback_path: Path | None = None,
) -> list[Proxy] | None:
    """Resolve proxy list from pasted text or an optional on-disk fallback file."""
    if not enabled:
        return None

    text = (proxies_text or "").strip()
    if text:
        proxies = parse_proxies_text(text, source_label="proxies")
        if not proxies:
            raise ValueError("Añade al menos un proxy válido")
        return proxies

    if fallback_path is not None and fallback_path.exists():
        proxies = load_proxies(fallback_path)
        if not proxies:
            raise ValueError(f"no proxies found in {fallback_path}")
        return proxies

    raise ValueError(
        "Pega tus proxys (uno por línea) o sube un archivo .txt con formato "
        "host:port:user:pass"
    )


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
