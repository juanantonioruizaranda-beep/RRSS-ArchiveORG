from rss_archiveorg.extractor import extract_social_links

SAMPLE_HTML = """
<html><body>
  <a href="https://www.facebook.com/example">Facebook</a>
  <a href="https://twitter.com/example">Twitter</a>
  <a href="https://x.com/example2">X</a>
  <a href="/web/20200101000000/https://instagram.com/example">IG (wayback)</a>
  <a href="https://youtu.be/abc123">YouTube</a>
  <a href="https://example.com/about">Not social</a>
  <a href="mailto:hi@example.com">Email</a>
</body></html>
"""


def test_extract_detects_networks():
    result = extract_social_links(SAMPLE_HTML)
    assert result["facebook"] == ["https://www.facebook.com/example"]
    assert set(result["twitter"]) == {
        "https://twitter.com/example",
        "https://x.com/example2",
    }
    assert result["youtube"] == ["https://youtu.be/abc123"]


def test_extract_unwraps_wayback_links():
    result = extract_social_links(SAMPLE_HTML)
    assert result["instagram"] == ["https://instagram.com/example"]


def test_extract_ignores_non_social():
    result = extract_social_links(SAMPLE_HTML)
    assert "example.com" not in result
    all_links = [link for links in result.values() for link in links]
    assert "mailto:hi@example.com" not in all_links


def test_extract_empty():
    assert extract_social_links("<html></html>") == {}
