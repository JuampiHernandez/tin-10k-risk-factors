CREATE EXTENSION IF NOT EXISTS tin;

CREATE TABLE IF NOT EXISTS risk_chunks (
  id               bigserial PRIMARY KEY,
  ticker           text        NOT NULL,
  company          text        NOT NULL,
  cik              text        NOT NULL,
  accession        text        NOT NULL,
  form             text        NOT NULL,
  item             text        NOT NULL,
  filed_on         date        NOT NULL,
  chunk_no         integer     NOT NULL,
  body             text        NOT NULL,
  source_url       text        NOT NULL,
  filing_index_url text        NOT NULL,
  provider         text        NOT NULL,
  capability       text        NOT NULL,
  retrieved_at     timestamptz NOT NULL,
  content_sha256   text        NOT NULL,
  UNIQUE (accession, item, chunk_no)
);

CREATE INDEX IF NOT EXISTS risk_chunks_body_tin ON risk_chunks USING tin (body) WITH (stemmer = 'en');
