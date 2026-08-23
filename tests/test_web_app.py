"""Tests for web app SEO headers."""

from pathlib import Path

from fastapi.testclient import TestClient

from rss_archiveorg.web.app import app

client = TestClient(app)


def test_landing_has_noindex_meta_and_header():
    response = client.get("/")
    assert response.status_code == 200
    assert 'name="robots" content="noindex, nofollow"' in response.text
    assert response.headers.get("X-Robots-Tag") == "noindex, nofollow"


def test_robots_txt_disallows_all():
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert "Disallow: /" in response.text
    assert response.headers.get("X-Robots-Tag") == "noindex, nofollow"


def test_api_config_exposes_social_networks():
    response = client.get("/api/config")
    assert response.status_code == 200
    payload = response.json()
    assert "facebook" in payload["social_networks"]
    assert "proxies_file_available" in payload
    assert payload["proxy_format"] == "host:port:user:pass"
    labels = {item["label"] for item in payload["primary_social_filters"]}
    assert "Twitter / X" in labels
    assert "Instagram" in labels
    assert response.headers.get("X-Robots-Tag") == "noindex, nofollow"


def test_extract_requires_proxies_when_enabled_without_source(monkeypatch, tmp_path: Path):
    missing = tmp_path / "missing-proxies.txt"
    monkeypatch.setattr(
        "rss_archiveorg.web.app.DEFAULT_PROXIES_PATH",
        missing,
    )
    response = client.post(
        "/api/extract",
        json={
            "urls_text": "https://example.com",
            "use_proxies": True,
            "proxies_text": "",
        },
    )
    assert response.status_code == 400
    assert "proxys" in response.json()["detail"].lower()
