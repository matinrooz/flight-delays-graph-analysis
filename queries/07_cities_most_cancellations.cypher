// Cities with the most cancelled departures, top 3 per year
MATCH (a:Airport)-[r:ROUTE]->()
WITH r.year AS year, a.city AS city, sum(r.cancelled) AS cancelled
ORDER BY year, cancelled DESC
WITH year, collect({city: city, cancelled: cancelled})[0..3] AS top
UNWIND top AS t
RETURN year, t.city AS city, t.cancelled AS cancelled
