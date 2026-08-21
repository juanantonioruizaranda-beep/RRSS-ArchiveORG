from pathlib import Path

import pytest

from rss_archiveorg.proxy import Proxy, ProxyPool, load_proxies, parse_proxies_text, resolve_proxies_for_run


def test_proxy_parse_with_auth():
    proxy = Proxy.parse("203.0.113.10:8080:proxy_user:proxy_pass")
    assert proxy == Proxy(
        host="203.0.113.10",
        port=8080,
        username="proxy_user",
        password="proxy_pass",
    )


def test_proxy_parse_without_auth():
    proxy = Proxy.parse("127.0.0.1:8080")
    assert proxy == Proxy(host="127.0.0.1", port=8080)


def test_proxy_parse_password_with_colons():
    proxy = Proxy.parse("203.0.113.10:8080:user:pa:ss:word")
    assert proxy is not None
    assert proxy.password == "pa:ss:word"


def test_proxy_parse_skips_comments_and_blanks():
    assert Proxy.parse("# comment") is None
    assert Proxy.parse("") is None


def test_proxy_parse_rejects_invalid_port():
    with pytest.raises(ValueError, match="invalid proxy port"):
        Proxy.parse("203.0.113.10:70000")


def test_proxy_requests_dict_includes_credentials():
    proxy = Proxy.parse("203.0.113.10:8080:user:pass")
    assert proxy is not None
    proxies = proxy.requests_dict()
    assert proxies["http"] == "http://user:pass@203.0.113.10:8080"
    assert proxies["https"] == proxies["http"]


def test_proxy_repr_masks_password():
    proxy = Proxy(host="203.0.113.10", port=8080, username="user", password="secret")
    assert "secret" not in repr(proxy)
    assert "password='***'" in repr(proxy)


def test_proxy_display_host():
    proxy = Proxy(host="203.0.113.10", port=8080, username="user", password="secret")
    assert proxy.display_host() == "203.0.113.10:8080"


def test_load_proxies_from_file(tmp_path: Path):
    path = tmp_path / "proxies.txt"
    path.write_text(
        "# header\n"
        "203.0.113.10:8080:proxy_user:proxy_pass\n"
        "\n"
        "127.0.0.1:8080\n",
        encoding="utf-8",
    )
    proxies = load_proxies(path)
    assert len(proxies) == 2
    assert proxies[0].host == "203.0.113.10"
    assert proxies[1].port == 8080


def test_load_proxies_reports_line_number(tmp_path: Path):
    path = tmp_path / "proxies.txt"
    path.write_text("bad-line\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r":1:"):
        load_proxies(path)


def test_parse_proxies_text():
    proxies = parse_proxies_text(
        "# comment\n203.0.113.10:8080:user:pass\n\n127.0.0.1:3128\n",
        source_label="proxies",
    )
    assert len(proxies) == 2
    assert proxies[0].host == "203.0.113.10"


def test_resolve_proxies_for_run_uses_pasted_text():
    proxies = resolve_proxies_for_run(
        enabled=True,
        proxies_text="203.0.113.10:8080:user:pass",
    )
    assert len(proxies) == 1


def test_resolve_proxies_for_run_uses_fallback_file(tmp_path: Path):
    path = tmp_path / "proxies.txt"
    path.write_text("203.0.113.10:8080:user:pass\n", encoding="utf-8")
    proxies = resolve_proxies_for_run(
        enabled=True,
        proxies_text="",
        fallback_path=path,
    )
    assert len(proxies) == 1


def test_resolve_proxies_for_run_requires_input_without_fallback():
    with pytest.raises(ValueError, match="Pega tus proxys"):
        resolve_proxies_for_run(enabled=True, proxies_text="", fallback_path=None)


def test_resolve_proxies_for_run_disabled():
    assert resolve_proxies_for_run(enabled=False, proxies_text="203.0.113.10:8080") is None


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
