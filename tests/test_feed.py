import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from feed import tracked_filings  # noqa: E402

FEED = pathlib.Path(__file__).resolve().parent.parent / "data" / "feed-sample.json"


def test_feed_sample_has_source_urls_and_accessions():
    data = json.loads(FEED.read_text())["data"]["alexandria"][0]["data"]
    assert data["total_records"] == len(data["records"]) > 0
    for r in data["records"]:
        assert r["accession"] and r["cik"] and r["form"] == "10-K"
        assert r["source_url"].startswith("https://www.sec.gov/Archives/")


def test_tracked_filings_matches_on_cik():
    records = json.loads(FEED.read_text())["data"]["alexandria"][0]["data"]["records"]
    first = records[0]["cik"]
    assert tracked_filings(records, {first: "DEMO"}) == [records[0]]
    assert tracked_filings(records, {"0000000000": "NONE"}) == []
