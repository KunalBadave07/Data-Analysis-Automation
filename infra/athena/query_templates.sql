-- Query 1: Basic row count from processed table
SELECT COUNT(*) AS row_count
FROM analytics_raw.processed;

-- Query 2: Sample recent records (replace event_time with actual timestamp column)
SELECT *
FROM analytics_raw.processed
ORDER BY event_time DESC
LIMIT 100;

-- Query 3: Null quality checks (replace columns as needed)
SELECT
    SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_customer_id,
    SUM(CASE WHEN revenue IS NULL THEN 1 ELSE 0 END) AS null_revenue
FROM analytics_raw.processed;
