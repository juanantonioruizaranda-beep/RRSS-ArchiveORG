"""Tests for corporate email extraction."""

from rss_archiveorg.extractors.corporate_email import extract_emails


def test_extract_corporate_email_from_mailto():
    html = """
    <html><body>
      <a href="mailto:info@example.com">Contact</a>
      <a href="mailto:hello@gmail.com">Personal</a>
      <a href="mailto:other@different.com">Other</a>
    </body></html>
    """
    corporate, all_emails = extract_emails(html, "example.com")
    assert corporate == ["info@example.com"]
    assert all_emails == ["info@example.com"]


def test_extract_obfuscated_email():
    html = "<html><body>Write to sales [at] example [dot] com today.</body></html>"
    corporate, all_emails = extract_emails(html, "example.com")
    assert corporate == ["sales@example.com"]
    assert all_emails == ["sales@example.com"]


def test_extract_accepts_subdomain_email():
    html = '<html><body><a href="mailto:info@mail.example.com">Contact</a></body></html>'
    corporate, all_emails = extract_emails(html, "example.com")
    assert corporate == ["info@mail.example.com"]
    assert all_emails == ["info@mail.example.com"]


def test_extract_rejects_wrong_domain_suffix():
    html = '<html><body>Reach us at info@notexample.com or @example.com</body></html>'
    corporate, all_emails = extract_emails(html, "example.com")
    assert corporate == []
    assert all_emails == []


def test_extract_rejects_bare_at_sign_fragments():
    html = "<html><body>Follow @example.com on social media</body></html>"
    corporate, all_emails = extract_emails(html, "example.com")
    assert corporate == []
    assert all_emails == []
