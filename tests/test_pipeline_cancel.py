"""Tests for batch cancellation."""

from unittest.mock import patch

import pytest

from rss_archiveorg.models import SiteResult
from rss_archiveorg.pipeline import BatchCancelled, run_sites_batch


def test_run_sites_batch_raises_when_cancelled_before_start():
    with pytest.raises(BatchCancelled):
        run_sites_batch(
            ["https://example.com"],
            should_cancel=lambda: True,
        )


def test_run_sites_batch_stops_after_first_result_when_cancelled():
    calls = {"count": 0}

    def fake_process_site(client, site, timestamp):
        calls["count"] += 1
        return SiteResult(site=site, social={"twitter": ["https://twitter.com/example"]})

    with patch("rss_archiveorg.pipeline.process_site", side_effect=fake_process_site):
        with pytest.raises(BatchCancelled):
            run_sites_batch(
                ["https://a.example", "https://b.example", "https://c.example"],
                delay=0,
                should_cancel=lambda: calls["count"] >= 1,
            )

    assert calls["count"] == 1
