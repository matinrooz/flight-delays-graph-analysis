// Airports with the longest average taxi-in time (landing to gate), in minutes.
// Only airports with at least 20,000 arrivals, small airports are too noisy.
MATCH ()-[r:ROUTE]->(b:Airport)
WITH b, sum(r.taxi_in_sum) AS total, sum(r.taxi_in_n) AS n
WHERE n >= 20000
RETURN b.code AS code, b.name AS name, round(total / n, 1) AS avg_taxi_in, n AS arrivals
ORDER BY avg_taxi_in DESC
LIMIT 10
