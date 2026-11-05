"""Turn an Alexandria sec-gov/filings/sections response into provenance-tagged chunks."""
import datetime as dt
import hashlib
import re

MIN_CHARS = 500
MAX_CHARS = 1800
PAGE_NOISE = re.compile(r"^(\d{1,3}|Table of Contents|Index to Financial Statements)$", re.I)


def paragraphs(text: str):
    for line in text.split("\n"):
        line = line.strip()
        if not line or PAGE_NOISE.match(line):
            continue
        yield line


def chunk_text(text: str):
    """Group consecutive paragraphs into chunks of at least MIN_CHARS, without splitting a paragraph.

    A chunk closes once it holds MIN_CHARS or the next paragraph would push it past MAX_CHARS, so one
    long paragraph can make a chunk longer than MAX_CHARS. Only page-number lines are dropped. A short
    tail of fewer than 200 characters joins the previous chunk.
    """
    chunks = []
    buf = []
    size = 0
    for p in paragraphs(text):
        if size and size + len(p) > MAX_CHARS:
            chunks.append(" ".join(buf))
            buf, size = [], 0
        buf.append(p)
        size += len(p)
        if size >= MIN_CHARS:
            chunks.append(" ".join(buf))
            buf, size = [], 0
    if buf:
        tail = " ".join(buf)
        if chunks and len(tail) < 200:
            chunks[-1] += " " + tail
        else:
            chunks.append(tail)
    return chunks


def rows_from_response(ticker: str, saved: dict):
    """Return one row dict per chunk, with the provenance columns filled from the response."""
    item = saved["response"]["data"]["alexandria"][0]
    data = item["data"]
    filing = data["filing"]
    retrieved_at = dt.datetime.fromtimestamp(data["observed_at_ms"] / 1000, dt.timezone.utc)
    for section in data["sections"]:
        sha = hashlib.sha256(section["text"].encode()).hexdigest()
        for n, body in enumerate(chunk_text(section["text"]), start=1):
            yield {
                "ticker": ticker,
                "company": data["company"]["name"],
                "cik": data["company"]["cik"],
                "accession": filing["accession_number"],
                "form": filing["form"],
                "item": section["item"],
                "filed_on": filing["filing_date"],
                "chunk_no": n,
                "body": body,
                "source_url": data["document_url"],
                "filing_index_url": filing["filing_index_url"],
                "provider": item["provider"],
                "capability": item["capability"],
                "retrieved_at": retrieved_at,
                "content_sha256": sha,
            }
