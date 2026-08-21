from pathlib import Path

import pytest

from rss_archiveorg.proxy import Proxy, ProxyPool, load_proxies


def test_proxy_parse_with_auth():
    proxy = Proxy.parse("31.59.20.176:6754:loykprsf:fjneokaotzmc")
    assert proxy == Proxy(
        host="31.59.20.176",
        port=6754,
        username="loykprsf",
        password="fjneokaotzmc",
    )


def test_proxy_parse_without_auth():
    proxy = Proxy.parse("127.0.0.1:8080")
    assert proxy == Proxy(host="127.0.0.1", port=8080)


def test_proxy_parse_skips_comments_and_blanks():
    assert Proxy.parse("# comment") is None
    assert Proxy.parse("") is None


def test_proxy_requests_dict_includes_credentials():
    proxy = Proxy.parse("31.59.20.176:6754:user:pass")
    assert proxy is not None
    proxies = proxy.requests_dict()
    assert proxies["http"] == "http://user:pass@31.59.20.176:6754"
    assert proxies["https"] == proxies["http"]


def test_load_proxies_from_file(tmp_path: Path):
    path = tmp_path / "proxies.txt"
    path.write_text(
        "# header\n"
        "31.59.20.176:6754:loykprsf:fjneokaotzmc\n"
        "\n"
        "127.0.0.1:8080\n",
        encoding="utf-8",
    )
    proxies = load_proxies(path)
    assert len(proxies) == 2
    assert proxies[0].host == "31.59.20.176"
    assert proxies[1].port == 8080


def test_proxy_pool_rotates_round_robin():
    pool = ProxyPool(
        [
            Proxy(host="1.1.1.1", port=1),
            Proxy(host="2.2.2.2", port=2),
            Proxy(host="3.3.3.3", port=3),
        ]
    )
    assert pool.current.host == "1.1.1.1"
    assert pool.rotate().host == "2.2.2.2"
    assert pool.rotate().host == "3.3.3.3"
    assert pool.rotate().host == "1.1.1.1"


def test_proxy_pool_apply_to_session():
    class FakeSession:
        def __init__(self):
            self.proxies = {}

    session = FakeSession()
    pool = ProxyPool([Proxy(host="10.0.0.1", port=3128)])
    pool.apply_to_session(session)
    assert session.proxies["http"] == "http://10.0.0.1:3128"


def test_proxy_pool_requires_at_least_one_proxy():
    with pytest.raises(ValueError, match="at least one proxy"):
        ProxyPool([])
