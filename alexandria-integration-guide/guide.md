---
title: "Load data from Firecrawl Alexandria into PlanetScale Postgres"
author: "Juan Pablo Hernandez"
description: "Run a Firecrawl Alexandria call, store each record in a PlanetScale Postgres table with its source, and refresh it without duplicates."
---

# Load data from Firecrawl Alexandria into PlanetScale Postgres

Firecrawl Alexandria is Firecrawl's catalogue of data providers. One API call returns structured records from a provider, together with the source URL and the time the data was retrieved. This guide loads those records into a PlanetScale Postgres table, so you can query, join and search them next to the rest of your data.

The example uses the sec-gov provider and its `filings/daily_index_changes` capability, which lists the filings added to the SEC EDGAR index on a given day. The same pattern works for other Alexandria providers. Only the options and the column mapping change.

## Requirements

- A PlanetScale Postgres database
- Access to your branch's default role
- A Firecrawl account and API key
- Python 3.9 or newer

## Network access

If your database uses IP restrictions, add the address of the machine that runs the loader to the allowlist before you connect. IP restrictions are set per database.

## Create the table

Connect as the default role on port `5432`. PlanetScale routes connections by branch, so the username carries your branch ID, for example `postgres.<branch_id>`. Use `sslmode=require`.

```
export DATABASE_URL='postgresql://postgres.<branch_id>:<password>@<host>:5432/postgres?sslmode=require'
```

The table keeps the typed columns you query and the full record as `jsonb`. The accession number is the primary key, so loading the same filing twice updates the row.

```sql
CREATE TABLE IF NOT EXISTS alexandria_filings (
  accession      text PRIMARY KEY,
  cik            text        NOT NULL,
  company_name   text        NOT NULL,
  form           text        NOT NULL,
  filed          date        NOT NULL,
  source_url     text        NOT NULL,
  provider       text        NOT NULL,
  capability     text        NOT NULL,
  retrieved_at   timestamptz NOT NULL,
  loaded_at      timestamptz NOT NULL DEFAULT now(),
  record         jsonb       NOT NULL
);

CREATE INDEX IF NOT EXISTS alexandria_filings_filed_idx ON alexandria_filings (filed DESC);
```

## Call Alexandria and load the records

Set your keys and run the loader (`load.py`, below). Each call to this capability costs 5 Firecrawl credits and returns one published day.

```
pip install -r requirements.txt
export FIRECRAWL_API_KEY=<your key>
python load.py --since 2026-10-28
```

The loader posts one request to the Firecrawl API with an `alexandria` body, saves the response to `last-response.json`, and upserts every record:

```python
body = {"alexandria": {
    "provider": "sec-gov",
    "capability": "filings/daily_index_changes",
    "options": {"since": "2026-10-28", "until": "2026-10-28", "forms": ["10-K"], "join": "none", "page_size": 100},
}}
```

Alexandria reports provider errors inside an HTTP 200 response, so the loader checks the `error` field of the result and not only the status code. The Python SDK makes the same call with `Firecrawl(api_key=...).scrape(alexandria={...})`, the Node.js SDK with `fc.scrape({ alexandria: {...} })`, the Firecrawl CLI with `firecrawl scrape sec-gov/filings/daily_index_changes --options '{...}'`, and the Firecrawl MCP server with the `firecrawl_scrape` tool and an `alexandria` argument. The request object is the same in each.

To load a saved response without spending credits, pass it as a file:

```
python load.py --from-file last-response.json
```

## Verify the load

```sql
SELECT accession, company_name, filed, source_url, retrieved_at
FROM alexandria_filings
ORDER BY company_name;
```

Every row links to the filing on sec.gov and says when Alexandria retrieved it. Running the loader a second time with the same day leaves the row count unchanged.

## Keep the table current

Run the loader once a day for the previous day, from a scheduler you already use. The upsert makes a repeated or overlapping run safe. This capability lists additions only, so removals and corrections are not reflected in the table.

## Next steps

- Add a TIN index on a text column to search the loaded text with phrase and proximity queries. See the [search documentation](https://planetscale.com/docs/postgres/search) and the companion guide on searching 10-K risk factors.
- Use the `record` column to keep fields you have not mapped yet, then promote them to columns when you need them.

## Code

### requirements.txt

```
requests>=2.31
psycopg[binary]>=3.1
```

### load.py

```python
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
```

## What was tested

The loader and the table ran against Postgres 18 with Lead, PlanetScale's TIN-compatible local Postgres image, on November 4, 2026. One live Alexandria call for October 28, 2026 returned five 10-K filings, which loaded as five rows; a second run from the saved response left the count at five. A call for November 2, 2026 returned no 10-K filings and loaded zero rows without error. The same Alexandria request also ran through the Python SDK, the Node.js SDK, the Firecrawl CLI and the Firecrawl MCP server on the same day, and all four returned the five filings. The loader has not been run on a PlanetScale cluster, so the connection steps follow the Artie integration page for connection format and have not been checked against a live branch.
