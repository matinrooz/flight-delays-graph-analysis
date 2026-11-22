// Carriers on the market and how many flights each one scheduled, 2014-2016
MATCH ()-[r:ROUTE]->()
WITH r.carrier AS code, sum(r.flights) AS flights,
     min(r.year) AS first_year, max(r.year) AS last_year
MATCH (c:Carrier {code: code})
RETURN c.code AS code, c.name AS name, flights, first_year, last_year
ORDER BY flights DESC
