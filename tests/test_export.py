"""Tests for web export helpers."""

from rss_archiveorg.io import results_to_csv_text, results_to_json_text


def test_results_to_json_text_serializes_list():
    payload = [{"site": "https://example.com", "status": "ok", "social": {}}]
    text = results_to_json_text(payload)
    assert '"https://example.com"' in text


def test_results_to_csv_text_includes_emails_and_social():
    payload = [
        {
            "site": "https://example.com",
            "status": "ok",
            "social": {"twitter": ["https://twitter.com/example"]},
            "corporate_emails": ["info@example.com"],
            "all_emails": ["info@example.com", "hello@gmail.com"],
            "snapshot": {"timestamp": "20200101", "url": "http://web.archive.org/..."},
            "error": None,
        }
    ]
    csv_text = results_to_csv_text(payload)
    assert "twitter" in csv_text
    assert "info@example.com" in csv_text
    assert "hello@gmail.com" in csv_text
