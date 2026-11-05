"""Load one Firecrawl Alexandria response into PlanetScale Postgres.

Usage:
  FIRECRAWL_API_KEY=... DATABASE_URL=postgresql://... python load.py --since 2026-11-02
  DATABASE_URL=postgresql://... python load.py --from-file sample.json     (no credits)
"""
import argparse
import json
import os
import pathlib
import uuid

import psycopg
import requests

ap = argparse.ArgumentParser()
ap.add_argument("--since")
ap.add_argument("--from-file")
args = ap.parse_args()

if args.from_file:
    response = json.loads(pathlib.Path(args.from_file).read_text())
else:
    if not args.since:
        raise SystemExit("Pass --since YYYY-MM-DD or --from-file")
    options = {"since": args.since, "until": args.since, "forms": ["10-K"], "join": "none", "page_size": 100}
    body = {"alexandria": {"provider": "sec-gov", "capability": "filings/daily_index_changes", "options": options}}
    r = requests.post(
        "https://api.firecrawl.dev/v2/scrape",
        headers={"Authorization": f"Bearer {os.environ['FIRECRAWL_API_KEY']}", "x-request-id": str(uuid.uuid4())},
        json=body,
        timeout=180,
    )
    r.raise_for_status()
    response = r.json()
    pathlib.Path("last-response.json").write_text(json.dumps(response, indent=1))

item = response["data"]["alexandria"][0]
if item.get("error"):
    raise SystemExit(f"Alexandria error: {item['error']}")
records = item["data"]["records"]

sql = """
INSERT INTO alexandria_filings (accession, cik, company_name, form, filed, source_url, provider, capability, retrieved_at, record)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (accession) DO UPDATE SET
  retrieved_at = EXCLUDED.retrieved_at, record = EXCLUDED.record, loaded_at = now()
"""
with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
    cur.execute(pathlib.Path(__file__).with_name("schema.sql").read_text())
    for rec in records:
        cur.execute(sql, (
            rec["accession"], rec["cik"], rec["company_name"], rec["form"], rec["filed"],
            rec["source_url"], item["provider"], item["capability"], rec["retrieved_at"], json.dumps(rec),
        ))
print(f"loaded {len(records)} rows, firecrawl_credits_used {item.get('creditsCost', 0)}")
