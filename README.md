# Search SEC risk factors in SQL with TIN on PlanetScale

This repository holds two things that belong to the same walkthrough:

- The repo root is the runnable demo: 10-K risk-factor sections loaded into Postgres and searched with a TIN-compatible index (see below). Saved output exists for Lead and for a real PlanetScale Postgres database.
- `alexandria-integration-guide/` is the standalone guide for pulling the same kind of data through Firecrawl Alexandria into Postgres: `guide.md`, `load.py`, `schema.sql`, `requirements.txt`.

Set `DATABASE_URL` and `FIRECRAWL_API_KEY` as environment variables. Nothing secret is stored in this repository.

A runnable companion to the article "Search 10-K risk factors with TIN: a sourced public-records index in PlanetScale Postgres".

It loads Item 1A (Risk Factors) from the latest 10-K of six public companies into one Postgres table, indexes the text with TIN, and searches it with TINQL. Every row keeps the provider, capability, source URL, accession number, retrieval time and a content hash. The filings come through Firecrawl Alexandria (the `sec-gov` provider). Filing text is public SEC EDGAR data, used as filed. This is a search demo, not investment advice.

The repo ships the six saved responses in `data/raw/`, so you can run everything below without a Firecrawl key or any credits.

## What you need
- Docker with Compose, and Python 3.10 or newer
- Nothing else for the local run. For a real PlanetScale cluster see "Run it on PlanetScale Postgres".

## Run it locally with Lead
Lead is PlanetScale's open source, TIN-compatible Postgres extension for development and CI (github.com/planetscale/lead). It is slow on purpose and not for production, so this run checks that the SQL is correct and says nothing about speed.

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

docker compose up -d --wait                # Postgres 18 with Lead on port 55432, waits until it is ready
export DATABASE_URL=postgresql://postgres:postgres@localhost:55432/postgres

python src/load.py                         # schema, chunks, TIN index
python src/search.py                       # five numbered queries with cited results
pytest -q                                  # 5 unit tests, plus 1 database test when DATABASE_URL is set
```

Stop the database and delete its data with `docker compose down -v`.

## What each query shows
Queries live in `sql/queries.sql`. They use the documented TIN operators: `==>`, `tin.score(ctid)`, `tin.highlight`, phrases, `NEAR/n`, `THEN/n` and boosts.

1. A phrase near a set of words, ranked by BM25 score.
2. Exact match counts per company with `GROUP BY`.
3. An ordered span: "export" followed by "controls" within five words.
4. A boosted phrase that must also sit with another term.
5. A provenance audit: filing, source, retrieval date and hash for every loaded filing. The retrieval date is the observation time Alexandria returned when the filing was fetched, saved in `data/raw`, not the time of the load.

For a count per company, use `psql "$DATABASE_URL" -c "SELECT ticker, count(*) FROM risk_chunks GROUP BY ticker ORDER BY ticker"`.

## Refresh with live data (optional, spends Firecrawl credits)
```sh
export FIRECRAWL_API_KEY=...               # never commit this
python src/fetch.py --force                # all tickers, 5 Firecrawl credits each
python src/fetch.py --force --ticker NVDA  # one ticker
python src/load.py                         # replaces each company's 10-K chunks, one transaction per company

python src/new_filings.py --since 2026-10-28          # 5 Firecrawl credits per day: 10-K filings added
python src/new_filings.py --from-file data/feed-sample.json   # same output from a saved response, no credits
```
`tickers.txt` sets the companies. A ticker whose 10-K the provider cannot find is reported and skipped.

## Run it on PlanetScale Postgres
TIN is available on PlanetScale Postgres and Neki databases.
1. Create a Postgres database in the PlanetScale dashboard (a single node cluster is enough for this data).
2. If the Clusters page shows "Cluster update available", apply it. `CREATE EXTENSION tin` fails with a superuser error until the cluster is updated.
3. Copy the connection details for your role and set the URL with SSL on the direct port:
   `export DATABASE_URL='postgresql://USER:PASSWORD@HOST:5432/postgres?sslmode=require'`
4. Run `python src/load.py` and `python src/search.py` as above. The same SQL runs, and the scores matched Lead in our run.
5. Delete the database when you are done to stop billing.

## Layout
```
data/raw/            saved sec-gov/filings/sections responses (the input)
data/feed-sample.json one saved daily_index_changes response
sql/schema.sql       table and TIN index
sql/queries.sql      the five queries
out/                 search.py output from Lead (2026-11-04) and from PlanetScale Postgres with TIN 1.0.7 (2026-11-05)
src/alexandria.py    minimal Firecrawl Alexandria client (one POST, retries reuse the request id)
src/fetch.py         live fetch into data/raw
src/chunks.py        chunking and provenance columns
src/load.py          load into Postgres
src/new_filings.py   daily change feed check
src/search.py        runs sql/queries.sql
tests/               unit tests and one database test
```

## What was and was not tested
- Tested on November 4, 2026, from an empty directory: live fetch of all six filings (30 Firecrawl credits), load of 592 chunks, the five queries and the six tests, on Postgres 18 with Lead (TIN 1.0.6). The saved output in out/ comes from that run.
- Also tested on November 5, 2026 on a single-node PlanetScale Postgres database (Postgres 18.6, TIN 1.0.7): the load and the five queries printed the same rows and scores as Lead. The saved output is out/search-output-planetscale.txt.
- Not tested: TIN query speed, other cluster sizes, and larger corpora.
- Counts such as "5 chunks" depend on the chunk size in src/chunks.py.
