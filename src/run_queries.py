"""Run every query in queries/, save the results as CSV and draw the figures.

Usage:
    python src/run_queries.py
"""

import glob
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from db import connect

# Parameters for the travel queries (12 and 13). Each trip is run for 2016.
TRIPS = [
    {"origin": "BGR", "dest": "KOA"},   # Bangor, Maine -> Kona, Hawaii
    {"origin": "ASE", "dest": "BTV"},   # Aspen, Colorado -> Burlington, Vermont
    {"origin": "BOS", "dest": "SFO"},   # one that has direct flights, as a reference
]
YEAR = 2016
MAX_LEGS = 3


def run(session, path, params=None):
    with open(path) as f:
        query = f.read()
    return pd.DataFrame([r.data() for r in session.run(query, **(params or {}))])


def plot_cancellations(df):
    pivot = df.pivot(index="code", columns="year", values="cancelled_pct")
    pivot = pivot.loc[pivot.mean(axis=1).sort_values(ascending=False).index]
    ax = pivot.plot(kind="bar", figsize=(9, 4), width=0.8)
    ax.set_ylabel("cancelled flights (%)")
    ax.set_xlabel("carrier")
    ax.set_title("Cancellation rate per carrier")
    plt.tight_layout()
    plt.savefig("figures/cancellation_rate_by_carrier.png", dpi=120)
    plt.close()


def plot_weather(df):
    fig, ax = plt.subplots(figsize=(8, 3.5))
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    ax.bar(months, df["weather_cancelled"])
    ax.set_ylabel("flights cancelled")
    ax.set_title("Weather cancellations per month (2014-2016 together)")
    plt.tight_layout()
    plt.savefig("figures/weather_cancellations_by_month.png", dpi=120)
    plt.close()


def plot_taxi_in(df):
    df = df.sort_values("avg_taxi_in")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(df["code"], df["avg_taxi_in"])
    ax.set_xlabel("average taxi-in time (min)")
    ax.set_title("Longest taxi-in, airports with 20k+ arrivals")
    plt.tight_layout()
    plt.savefig("figures/taxi_in.png", dpi=120)
    plt.close()


def main():
    os.makedirs("results", exist_ok=True)
    os.makedirs("figures", exist_ok=True)

    driver = connect()
    with driver.session() as s:
        results = {}
        for path in sorted(glob.glob("queries/*.cypher")):
            name = os.path.basename(path).replace(".cypher", "")
            if name.startswith(("12_", "13_")):
                frames = []
                for trip in TRIPS:
                    params = {**trip, "year": YEAR, "max_legs": MAX_LEGS}
                    df = run(s, path, params)
                    df.insert(0, "trip", f"{trip['origin']}-{trip['dest']}")
                    frames.append(df)
                df = pd.concat(frames, ignore_index=True)
            else:
                df = run(s, path)
            df.to_csv(f"results/{name}.csv", index=False)
            results[name] = df
            print(f"\n## {name}\n")
            print(df.to_string(index=False))
    driver.close()

    plot_cancellations(results["06_cancellation_rate_by_carrier"])
    plot_weather(results["08_weather_cancellations_by_month"])
    plot_taxi_in(results["09_taxi_in"])
    print("\nfigures written to figures/")


if __name__ == "__main__":
    main()
