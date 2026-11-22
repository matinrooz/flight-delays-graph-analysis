// Total distance flown per year (cancelled flights not counted), in miles
MATCH ()-[r:ROUTE]->()
RETURN r.year AS year, toInteger(round(sum(r.flown_distance))) AS miles
ORDER BY year
