// Share of cancelled flights per carrier and year
MATCH ()-[r:ROUTE]->()
WITH r.year AS year, r.carrier AS code,
     sum(r.flights) AS flights, sum(r.cancelled) AS cancelled
MATCH (c:Carrier {code: code})
RETURN year, code, c.name AS name, flights, cancelled,
       round(100.0 * cancelled / flights, 2) AS cancelled_pct
ORDER BY year, cancelled_pct DESC
