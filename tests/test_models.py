from rss_archiveorg.models import SiteResult, SnapshotInfo


def test_site_result_to_dict_without_snapshot():
    result = SiteResult(site="https://example.com", error="failed")
    payload = result.to_dict()
    assert payload["site"] == "https://example.com"
    assert payload["snapshot"] is None
    assert payload["error"] == "failed"


def test_site_result_to_dict_with_snapshot():
    result = SiteResult(
        site="https://example.com",
        snapshot=SnapshotInfo(url="http://web.archive.org/web/1/", timestamp="1"),
        social={"facebook": ["https://facebook.com/example"]},
    )
    payload = result.to_dict()
    assert payload["snapshot"]["timestamp"] == "1"
    assert payload["social"]["facebook"][0].endswith("/example")
