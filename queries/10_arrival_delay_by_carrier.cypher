// Average arrival delay per carrier in minutes (negative means early), 2014-2016
MATCH ()-[r:ROUTE]->()
WITH r.carrier AS code, sum(r.arr_delay_sum) AS total, sum(r.arr_delay_n) AS n
MATCH (c:Carrier {code: code})
RETURN code, c.name AS name, round(total / n, 1) AS avg_arr_delay, n AS flights
ORDER BY avg_arr_delay DESC
