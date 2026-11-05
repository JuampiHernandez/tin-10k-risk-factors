-- Count checks behind the numbers quoted in the article. Run: psql "$DATABASE_URL" -f sql/counts.sql
SELECT 'supply chain NEAR/6 disruption OR shortage OR constraint' AS query, count(*) FROM risk_chunks WHERE body ==> '"supply chain" NEAR/6 (disruption OR shortage OR constraint)';
SELECT 'export THEN/5 controls' AS query, ticker, count(*) FROM risk_chunks WHERE body ==> 'export THEN/5 controls' GROUP BY ticker ORDER BY ticker;
SELECT 'artificial intelligence boosted AND regulation' AS query, count(*) FROM risk_chunks WHERE body ==> '"artificial intelligence"^2 AND regulation';
SELECT 'all chunks' AS query, count(*) FROM risk_chunks;
