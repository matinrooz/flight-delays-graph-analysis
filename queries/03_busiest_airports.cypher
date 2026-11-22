// Airports with the most departures (flights that actually left), 2014-2016
MATCH (a:Airport)-[r:ROUTE]->()
RETURN a.code AS code, a.name AS name, a.city AS city,
       sum(r.flights - r.cancelled) AS departures
ORDER BY departures DESC
LIMIT 10
