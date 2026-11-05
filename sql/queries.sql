-- name: 1. Phrase with proximity: supply disruption language
SELECT ticker, filed_on, tin.score(ctid) AS score, tin.highlight(body) AS excerpt, source_url
FROM risk_chunks
WHERE body ==> '"supply chain" NEAR/6 (disruption OR shortage OR constraint)'
ORDER BY score DESC, id
LIMIT 3;

-- name: 2. Exact counts per company: cybersecurity next to third parties
SELECT ticker, count(*) AS matching_chunks
FROM risk_chunks
WHERE body ==> 'cybersecurity AND "third parties"'
GROUP BY ticker
ORDER BY matching_chunks DESC, ticker;

-- name: 3. Ordered span: export then controls within five words
SELECT ticker, tin.score(ctid) AS score, tin.highlight(body) AS excerpt, source_url
FROM risk_chunks
WHERE body ==> 'export THEN/5 controls'
ORDER BY score DESC, id
LIMIT 3;

-- name: 4. Boosted term: artificial intelligence weighted double, regulation required
SELECT ticker, tin.score(ctid) AS score, tin.highlight(body) AS excerpt, source_url
FROM risk_chunks
WHERE body ==> '"artificial intelligence"^2 AND regulation'
ORDER BY score DESC, id
LIMIT 3;

-- name: 5. Provenance audit: every filing, where it came from and when it was retrieved
SELECT ticker, accession, filed_on, provider || '/' || capability AS source, retrieved_at::date AS retrieved, left(content_sha256, 10) AS sha, count(*) AS chunks
FROM risk_chunks
GROUP BY ticker, accession, filed_on, provider, capability, retrieved_at, content_sha256
ORDER BY ticker;
