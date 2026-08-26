"""Tests for web app SEO headers."""

from unittest.mock import patch

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
    labels = {item["label"] for item in payload["primary_social_filters"]}
    assert "Twitter / X" in labels
    assert "Instagram" in labels
    assert response.headers.get("X-Robots-Tag") == "noindex, nofollow"


def test_landing_includes_proxy_textarea():
    response = client.get("/")
    assert response.status_code == 200
    assert 'id="proxies"' in response.text
    assert "Proxys (uno por línea)" in response.text
    assert 'id="progress-data-count"' in response.text
    assert "resultados con datos encontrados" in response.text


def test_extract_requires_proxies_when_enabled_without_source():
    response = client.post(
        "/api/extract",
        json={
            "urls_text": "https://example.com",
            "use_proxies": True,
        },
    )
    assert response.status_code == 400
    assert "proxy" in response.json()["detail"].lower()


def test_extract_accepts_inline_proxies_text():
    with patch("rss_archiveorg.web.app.run_sites_batch") as run_batch:
        response = client.post(
            "/api/extract",
            json={
                "urls_text": "https://example.com",
                "use_proxies": True,
                "proxies_text": "203.0.113.10:8080:user:pass",
            },
        )
    assert response.status_code == 200
    run_batch.assert_called_once()
    _, kwargs = run_batch.call_args
    assert kwargs["proxies"] is not None
    assert len(kwargs["proxies"]) == 1
    assert kwargs["proxies_path"] is None
