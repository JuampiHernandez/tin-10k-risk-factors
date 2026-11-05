"""Fetch the latest 10-K Item 1A (Risk Factors) for each ticker through the sec-gov provider in Firecrawl Alexandria.

Usage: FIRECRAWL_API_KEY=... python src/fetch.py [--force] [--ticker NVDA --ticker JPM]

Each call to sec-gov/filings/sections costs 5 Firecrawl credits. Raw responses are saved to
data/raw/<TICKER>.json and tickers that already have a file are skipped, so the repo can be
re-run without spending credits.
"""
import argparse
import json
import pathlib

from alexandria import call, credits

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
ap = argparse.ArgumentParser()
ap.add_argument("--force", action="store_true", help="refetch tickers that already have a file")
ap.add_argument("--ticker", action="append", help="fetch only this ticker (repeatable)")
args = ap.parse_args()
force = args.force

total = 0
for ticker in args.ticker or [t.strip() for t in (ROOT / "tickers.txt").read_text().split() if t.strip()]:
    out = RAW / f"{ticker}.json"
    if out.exists() and not force:
        print(f"skip {ticker} (data/raw/{ticker}.json exists)")
        continue
    options = {"ticker": ticker, "form": "10-K", "items": ["1A"], "max_chars": 200000}
    try:
        response = call("sec-gov", "filings/sections", options)
    except RuntimeError as e:
        print(f"FAILED {ticker}: {e}")
        continue
    response.pop("scrape_id", None)
    out.write_text(json.dumps({"request": options, "response": response}, indent=1))
    total += credits(response)
    print(f"fetched {ticker}")
print(f"firecrawl_credits_used_this_run {total}")
