"""Check the Cypher results against the raw data.

The graph only stores sums per route and month, so a mistake in prepare_data.py
or in a query would silently give wrong numbers. This script reads the raw
files again with pandas, one flight per row, and compares a few totals with
what the queries returned.

Usage (after run_queries.py):
    python src/check_results.py
"""

import glob

import pandas as pd

from prepare_data import read_month

failures = 0


def compare(label, expected, got):
    global failures
    ok = abs(float(expected) - float(got)) <= 0.5
    failures += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {label}: raw {expected:,.0f}, graph {got:,.0f}")


def main():
    flights, cancelled, weather, distance, planes = {}, {}, {}, {}, {}
    for path in sorted(glob.glob("data/raw/ontime_*.zip")):
        df = read_month(path)
        year = int(df["Year"].iloc[0])
        month = int(df["Month"].iloc[0])
        flew = df["Cancelled"] == 0
        flights[year] = flights.get(year, 0) + len(df)
        cancelled[year] = cancelled.get(year, 0) + int(df["Cancelled"].sum())
        weather[month] = weather.get(month, 0) + int((df["CancellationCode"] == "B").sum())
        distance[year] = distance.get(year, 0) + df.loc[flew, "Distance"].sum()
        planes.setdefault(year, set()).update(df.loc[flew, "Tail_Number"].dropna())

    r1 = pd.read_csv("results/01_flights_per_year.csv").set_index("year")
    r2 = pd.read_csv("results/02_planes_per_year.csv").set_index("year")
    r5 = pd.read_csv("results/05_distance_per_year.csv").set_index("year")
    r8 = pd.read_csv("results/08_weather_cancellations_by_month.csv").set_index("month")

    for y in sorted(flights):
        compare(f"{y} scheduled flights", flights[y], r1.loc[y, "scheduled"])
        compare(f"{y} cancelled flights", cancelled[y], r1.loc[y, "cancelled"])
        compare(f"{y} planes", len(planes[y]), r2.loc[y, "planes"])
        compare(f"{y} miles flown", distance[y], r5.loc[y, "miles"])
    for m in sorted(weather):
        compare(f"month {m} weather cancellations", weather[m], r8.loc[m, "weather_cancelled"])

    print("\nall checks passed" if failures == 0 else f"\n{failures} checks failed")


if __name__ == "__main__":
    main()
