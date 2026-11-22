"""Load the prepared CSV files into Neo4j.

Graph model:
    (:Airport {code, name, city, state})
    (:Carrier {code, name})
    (:Plane {tail})
    (:Airport)-[:ROUTE {carrier, year, month, flights, cancelled, ...}]->(:Airport)
    (:Plane)-[:FLEW_FOR {year, flights}]->(:Carrier)

The database is emptied first, so the script can be run again.

Usage:
    python src/load_graph.py
"""

import math
import time

import pandas as pd

from db import connect

IMPORT_DIR = "data/import"
BATCH = 5000


def batches(df):
    records = df.to_dict("records")
    for i in range(0, len(records), BATCH):
        chunk = records[i:i + BATCH]
        # Neo4j does not accept NaN well, use None (null) instead
        for r in chunk:
            for k, v in r.items():
                if isinstance(v, float) and math.isnan(v):
                    r[k] = None
        yield chunk


def run_batches(session, query, df, label):
    t = time.time()
    for chunk in batches(df):
        session.run(query, rows=chunk).consume()
    print(f"{label}: {len(df):,} rows in {time.time() - t:.0f} s")


def main():
    airports = pd.read_csv(f"{IMPORT_DIR}/airports.csv")
    carriers = pd.read_csv(f"{IMPORT_DIR}/carriers.csv")
    planes = pd.read_csv(f"{IMPORT_DIR}/planes.csv")
    routes = pd.read_csv(f"{IMPORT_DIR}/routes.csv")

    driver = connect()
    with driver.session() as s:
        print("emptying the database")
        s.run("MATCH (n) CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 10000 ROWS").consume()

        for stmt in [
            "CREATE CONSTRAINT airport_code IF NOT EXISTS FOR (a:Airport) REQUIRE a.code IS UNIQUE",
            "CREATE CONSTRAINT carrier_code IF NOT EXISTS FOR (c:Carrier) REQUIRE c.code IS UNIQUE",
            "CREATE CONSTRAINT plane_tail IF NOT EXISTS FOR (p:Plane) REQUIRE p.tail IS UNIQUE",
            "CREATE INDEX route_year IF NOT EXISTS FOR ()-[r:ROUTE]-() ON (r.year)",
        ]:
            s.run(stmt).consume()

        run_batches(s, """
            UNWIND $rows AS row
            CREATE (:Airport {code: row.code, name: row.name, city: row.city, state: row.state})
        """, airports, "airports")

        run_batches(s, """
            UNWIND $rows AS row
            CREATE (:Carrier {code: row.code, name: row.name})
        """, carriers, "carriers")

        run_batches(s, """
            UNWIND $rows AS row
            MATCH (c:Carrier {code: row.Reporting_Airline})
            MERGE (p:Plane {tail: row.Tail_Number})
            CREATE (p)-[:FLEW_FOR {year: row.Year, flights: row.flights}]->(c)
        """, planes, "planes")

        run_batches(s, """
            UNWIND $rows AS row
            MATCH (a:Airport {code: row.Origin}), (b:Airport {code: row.Dest})
            CREATE (a)-[:ROUTE {
                carrier: row.Reporting_Airline, year: row.Year, month: row.Month,
                flights: row.flights, cancelled: row.cancelled,
                weather_cancelled: row.weather_cancelled, diverted: row.diverted,
                dep_delay_sum: row.dep_delay_sum, dep_delay_n: row.dep_delay_n,
                arr_delay_sum: row.arr_delay_sum, arr_delay_n: row.arr_delay_n,
                taxi_in_sum: row.taxi_in_sum, taxi_in_n: row.taxi_in_n,
                elapsed_sum: row.elapsed_sum, elapsed_n: row.elapsed_n,
                distance: row.distance, flown_distance: row.flown_distance
            }]->(b)
        """, routes, "routes")

        # A second, simpler layer for travel questions: one CONNECTS relationship
        # per airport pair and year, summed over carriers and months.
        t = time.time()
        s.run("""
            MATCH (a:Airport)
            CALL (a) {
                MATCH (a)-[r:ROUTE]->(b:Airport)
                WITH a, b, r.year AS year,
                     sum(r.flights - r.cancelled) AS flown,
                     sum(r.elapsed_sum) AS elapsed_sum, sum(r.elapsed_n) AS elapsed_n,
                     sum(r.arr_delay_sum) AS delay_sum, sum(r.arr_delay_n) AS delay_n,
                     collect(DISTINCT r.carrier) AS carriers
                WHERE flown > 0 AND elapsed_n > 0
                CREATE (a)-[:CONNECTS {
                    year: year, flights: flown, carriers: carriers,
                    avg_time: elapsed_sum / elapsed_n,
                    avg_arr_delay: delay_sum / delay_n
                }]->(b)
            } IN TRANSACTIONS OF 20 ROWS
        """).consume()
        print(f"connects: built in {time.time() - t:.0f} s")

        counts = s.run("""
            MATCH (n) WITH count(n) AS nodes
            MATCH ()-[r]->() RETURN nodes, count(r) AS rels
        """).single()
        print(f"done: {counts['nodes']:,} nodes, {counts['rels']:,} relationships")
    driver.close()


if __name__ == "__main__":
    main()
