// Fewest plane changes between two airports in a given year.
// Returns every route with the minimum number of legs.
MATCH (a:Airport {code: $origin}), (b:Airport {code: $dest})
MATCH p = allShortestPaths((a)-[:CONNECTS*..5]->(b))
WHERE all(c IN relationships(p) WHERE c.year = $year)
RETURN length(p) - 1 AS changes,
       [n IN nodes(p) | n.code] AS airports,
       [c IN relationships(p) | c.carriers] AS carriers
ORDER BY airports
