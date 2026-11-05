"""List 10-K filings added for the tickers in data/raw, using the SEC daily change feed.

Usage:
  FIRECRAWL_API_KEY=... python src/new_filings.py --since 2026-10-28 [--until 2026-10-30]
  python src/new_filings.py --from-file data/feed-sample.json     (no credits)

sec-gov/filings/daily_index_changes returns one published day per call (5 Firecrawl credits).
It lists additions only. A filing for a tracked company means: run src/fetch.py --force for that
ticker (python src/fetch.py --force --ticker NVDA), then src/load.py, which replaces that company's 10-K chunks.
"""
import argparse
import json
import pathlib

from alexandria import call, credits
from feed import tracked_filings

ROOT = pathlib.Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--since")
ap.add_argument("--until")
ap.add_argument("--from-file")
args = ap.parse_args()

tracked = {}
for path in (ROOT / "data" / "raw").glob("*.json"):
    data = json.loads(path.read_text())["response"]["data"]["alexandria"][0]["data"]
    tracked[data["company"]["cik"]] = path.stem

if args.from_file:
    response = json.loads((ROOT / args.from_file).read_text())
else:
    if not args.since:
        raise SystemExit("Pass --since YYYY-MM-DD or --from-file")
    options = {"since": args.since, "until": args.until or args.since, "forms": ["10-K"], "join": "none", "page_size": 100}
    response = call("sec-gov", "filings/daily_index_changes", options)
    print(f"firecrawl_credits_used_this_run {credits(response)}")

data = response["data"]["alexandria"][0]["data"]
print(f"{data['total_records']} 10-K filings added on {data['date']} (publication {data['publication_id']})")
hits = tracked_filings(data["records"], tracked)
for r in hits:
    print(f"tracked: {tracked[r['cik']]} {r['company_name']} {r['accession']} {r['source_url']}")
if not hits:
    print("none of the tracked companies filed a 10-K on this day")
    print("first listed filing, for reference:", data["records"][0]["company_name"], data["records"][0]["source_url"])
