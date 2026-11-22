// Flights cancelled because of weather (cancellation code B), per calendar month, 2014-2016 together
MATCH ()-[r:ROUTE]->()
RETURN r.month AS month,
       sum(r.weather_cancelled) AS weather_cancelled,
       round(100.0 * sum(r.weather_cancelled) / sum(r.flights), 2) AS weather_cancelled_pct
ORDER BY month
