"""Tests for corporate email extraction."""

from rss_archiveorg.extractors.corporate_email import extract_emails


def test_extract_corporate_email_from_mailto():
    html = """
    <html><body>
      <a href="mailto:info@example.com">Contact</a>
      <a href="mailto:hello@gmail.com">Personal</a>
    </body></html>
    """
    corporate, all_emails = extract_emails(html, "example.com")
    assert corporate == ["info@example.com"]
    assert "hello@gmail.com" in all_emails


def test_extract_obfuscated_email():
    html = "<html><body>Write to sales [at] example [dot] com today.</body></html>"
    corporate, all_emails = extract_emails(html, "example.com")
    assert corporate == ["sales@example.com"]
    assert all_emails == ["sales@example.com"]
