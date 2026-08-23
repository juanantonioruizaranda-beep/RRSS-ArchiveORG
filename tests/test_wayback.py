import gzip

from rss_archiveorg.wayback import WaybackClient, Snapshot


class FakeResponse:
    def __init__(self, content: bytes, encoding="utf-8"):
        self.content = content
        self.encoding = encoding
        self.apparent_encoding = encoding

    @property
    def text(self):
        return self.content.decode(self.encoding, errors="replace")


def test_decode_body_plain_html():
    resp = FakeResponse(b"<html><body>hi</body></html>")
    assert "hi" in WaybackClient._decode_body(resp)


def test_decode_body_gzip_without_header():
    original = "<html><body>social</body></html>"
    resp = FakeResponse(gzip.compress(original.encode("utf-8")))
    assert WaybackClient._decode_body(resp) == original


def test_raw_url_uses_id_modifier():
    snap = Snapshot(
        original_url="https://example.com",
        archived_url="http://web.archive.org/web/20260821040028/https://example.com/",
        timestamp="20260821040028",
        status="200",
    )
    assert WaybackClient._raw_url(snap) == (
        "http://web.archive.org/web/20260821040028id_/https://example.com/"
    )
