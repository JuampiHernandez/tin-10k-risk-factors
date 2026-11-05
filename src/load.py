"""Load data/raw/*.json into Postgres (PlanetScale Postgres with TIN, or local Postgres with Lead).

Usage: DATABASE_URL=postgresql://... python src/load.py
Safe to re-run: a company's chunks for that form and item are replaced in one transaction, committed per filing, so a newer 10-K replaces the older one.
"""
import json
import os
import pathlib

import psycopg

from chunks import rows_from_response

ROOT = pathlib.Path(__file__).resolve().parent.parent
COLUMNS = [
    "ticker", "company", "cik", "accession", "form", "item", "filed_on", "chunk_no", "body",
    "source_url", "filing_index_url", "provider", "capability", "retrieved_at", "content_sha256",
]

INSERT = f"INSERT INTO risk_chunks ({', '.join(COLUMNS)}) VALUES ({', '.join(['%s'] * len(COLUMNS))})"

with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
    cur.execute((ROOT / "sql" / "schema.sql").read_text())
    total = 0
    for path in sorted((ROOT / "data" / "raw").glob("*.json")):
        saved = json.loads(path.read_text())
        rows = list(rows_from_response(path.stem, saved))
        cur.execute(
            "DELETE FROM risk_chunks WHERE cik = %s AND form = %s AND item = %s",
            (rows[0]["cik"], rows[0]["form"], rows[0]["item"]),
        )
        cur.executemany(INSERT, [[r[c] for c in COLUMNS] for r in rows])
        print(f"{path.stem}: {len(rows)} chunks from {rows[0]['accession']}")
        conn.commit()
        total += len(rows)
    cur.execute("ANALYZE risk_chunks")
print(f"loaded {total} chunks")
