"""Tests for web app SEO headers."""

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
    assert response.headers.get("X-Robots-Tag") == "noindex, nofollow"
