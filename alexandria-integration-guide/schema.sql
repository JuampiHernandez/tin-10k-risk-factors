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
