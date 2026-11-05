import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from chunks import chunk_text, rows_from_response  # noqa: E402

RAW = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw"


def test_page_noise_is_dropped_and_bullets_are_kept():
    text = "Intro paragraph " + "x" * 600 + "\n12\nTable of Contents\n•Summary bullet\nSecond paragraph " + "y" * 600
    joined = " ".join(chunk_text(text))
    assert "Table of Contents" not in joined
    assert " 12 " not in joined
    assert "•Summary bullet" in joined


def test_no_text_is_lost_and_paragraphs_are_not_split():
    paragraphs = ["word " * 90 for _ in range(30)]
    chunks = list(chunk_text("\n".join(paragraphs)))
    assert sum(len(c.split()) for c in chunks) == 30 * 90
    assert all(len(c.split()) % 90 == 0 for c in chunks)


def test_every_shipped_filing_yields_fully_provenanced_rows():
    files = sorted(RAW.glob("*.json"))
    assert files, "data/raw is empty"
    for path in files:
        rows = list(rows_from_response(path.stem, json.loads(path.read_text())))
        assert len(rows) > 20
        for r in rows:
            assert r["source_url"].startswith("https://www.sec.gov/Archives/")
            assert r["provider"] == "sec-gov" and r["capability"] == "filings/sections"
            assert r["retrieved_at"].tzinfo is not None
            assert len(r["content_sha256"]) == 64
            assert r["item"] == "1A" and r["body"].strip()
