// How many different planes (tail numbers) flew at least once each year?
MATCH (p:Plane)-[f:FLEW_FOR]->(:Carrier)
RETURN f.year AS year, count(DISTINCT p) AS planes
ORDER BY year
