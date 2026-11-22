// Airports with the most direct destinations in 2016 (out-degree in the CONNECTS graph)
MATCH (a:Airport)-[c:CONNECTS {year: 2016}]->()
RETURN a.code AS code, a.name AS name, count(c) AS destinations
ORDER BY destinations DESC
LIMIT 10
