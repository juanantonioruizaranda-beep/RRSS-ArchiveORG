from pathlib import Path

import pytest

from rss_archiveorg.io import normalize_site_url, read_sites, write_csv, write_json
from rss_archiveorg.models import SiteResult, SnapshotInfo


def test_normalize_site_url_accepts_http_and_https():
    assert normalize_site_url("https://example.com") == "https://example.com"
    assert normalize_site_url("http://example.com/path") == "https://example.com/path"


def test_normalize_site_url_accepts_bare_domain():
    assert normalize_site_url("omicshealth.es") == "https://omicshealth.es"
    assert normalize_site_url("www.example.com/about") == "https://www.example.com/about"


def test_normalize_site_url_rejects_other_schemes():
    with pytest.raises(ValueError, match="invalid site URL"):
        normalize_site_url("file:///etc/passwd")


def test_read_sites_validates_each_line(tmp_path: Path):
    path = tmp_path / "sites.txt"
    path.write_text("https://example.com\nftp://bad.example\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r":2:"):
        read_sites(path)


def test_write_json_roundtrip(tmp_path: Path):
    results = [
        SiteResult(
            site="https://example.com",
            social={"twitter": ["https://twitter.com/example"]},
            snapshot=SnapshotInfo(url="http://web.archive.org/web/1/", timestamp="1"),
        )
    ]
    output = tmp_path / "out.json"
    with output.open("w", encoding="utf-8") as handle:
        write_json(results, handle)
    payload = output.read_text(encoding="utf-8")
    assert "https://twitter.com/example" in payload


def test_write_csv_includes_error_column(tmp_path: Path):
    results = [SiteResult(site="https://example.com", error="boom")]
    output = tmp_path / "out.csv"
    with output.open("w", encoding="utf-8", newline="") as handle:
        write_csv(results, handle)
    text = output.read_text(encoding="utf-8")
    assert "boom" in text
