// How many flights were scheduled, flown and cancelled each year?
MATCH ()-[r:ROUTE]->()
RETURN r.year AS year,
       sum(r.flights) AS scheduled,
       sum(r.flights - r.cancelled) AS flown,
       sum(r.cancelled) AS cancelled
ORDER BY year
