// The quickest options from $origin to $dest with at most $max_legs legs.
// Only legs with at least one flight a week on average (52 per year) are used.
// Expected time = sum of the average flight times of the legs (time on the ground
// between flights is not in the data, so it is left out).
// Expected delay = average arrival delay of the last leg, since that is the delay
// you have when you arrive.
MATCH (a:Airport {code: $origin}), (b:Airport {code: $dest})
MATCH p = (a)-[:CONNECTS*1..3]->(b)
WHERE length(p) <= $max_legs
  AND all(c IN relationships(p) WHERE c.year = $year AND c.flights >= 52)
  AND all(i IN range(0, length(p) - 1) WHERE NOT nodes(p)[i] IN nodes(p)[i + 1..])
RETURN [n IN nodes(p) | n.code] AS airports,
       [c IN relationships(p) | c.carriers] AS carriers,
       toInteger(round(reduce(t = 0.0, c IN relationships(p) | t + c.avg_time))) AS expected_minutes,
       round(last(relationships(p)).avg_arr_delay, 1) AS expected_delay,
       reduce(m = 1000000, c IN relationships(p) | CASE WHEN c.flights < m THEN c.flights ELSE m END) AS min_leg_flights
ORDER BY expected_minutes
LIMIT 5
