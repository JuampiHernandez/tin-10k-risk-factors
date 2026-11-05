"""Run the numbered TINQL queries in sql/queries.sql and print cited results.

Usage: DATABASE_URL=postgresql://... python src/search.py
"""
import os
import pathlib
import re

import psycopg

def show(value) -> str:
    """Flatten whitespace and crop long text around the first highlight mark."""
    text = " ".join(str(value).split())
    if len(text) <= 200:
        return text
    start = max(text.find("<b>") - 80, 0)
    return text[start:start + 200]


ROOT = pathlib.Path(__file__).resolve().parent.parent
blocks = re.split(r"^-- name: ", (ROOT / "sql" / "queries.sql").read_text(), flags=re.M)[1:]

with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
    for block in blocks:
        title, _, sql = block.partition("\n")
        print(f"## {title.strip()}")
        cur.execute(sql)
        cols = [d.name for d in cur.description]
        for row in cur.fetchall():
            short = [f"{c}={show(v)}" for c, v in zip(cols, row) if c not in ("excerpt", "source_url")]
            print("  " + " | ".join(short))
            for c, v in zip(cols, row):
                if c in ("excerpt", "source_url"):
                    print(f"      {c}: {show(v)}")
        print()
