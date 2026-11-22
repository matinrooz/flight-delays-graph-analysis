"""Turn the raw BTS on-time files into the CSV files that are loaded into Neo4j.

The raw data has one row per flight (about 17 million rows for 2014-2016).
That is too much to load as single relationships on a laptop with 8 GB of RAM,
so flights are grouped by (year, month, carrier, origin, destination). Each group
becomes one ROUTE relationship that keeps counts and sums, so that averages can
still be computed exactly in Cypher (sum / count).

Usage:
    python src/prepare_data.py
"""

import csv
import glob
import os
import zipfile

import pandas as pd

RAW_DIR = "data/raw"
OUT_DIR = "data/import"

COLUMNS = [
    "Year", "Month", "Reporting_Airline", "Tail_Number",
    "Origin", "OriginCityName", "OriginState",
    "Dest", "DestCityName", "DestState",
    "DepDelay", "ArrDelay", "TaxiIn",
    "Cancelled", "CancellationCode", "Diverted",
    "ActualElapsedTime", "Distance",
]

# Carrier codes that appear in 2014-2016. The BTS lookup table was not
# reachable when I built this, so the names are filled in by hand.
CARRIER_NAMES = {
    "AA": "American Airlines",
    "AS": "Alaska Airlines",
    "B6": "JetBlue Airways",
    "DL": "Delta Air Lines",
    "EV": "ExpressJet Airlines",
    "F9": "Frontier Airlines",
    "FL": "AirTran Airways",
    "HA": "Hawaiian Airlines",
    "MQ": "Envoy Air",
    "NK": "Spirit Airlines",
    "OO": "SkyWest Airlines",
    "UA": "United Air Lines",
    "US": "US Airways",
    "VX": "Virgin America",
    "WN": "Southwest Airlines",
}


def read_month(path):
    with zipfile.ZipFile(path) as z:
        name = [n for n in z.namelist() if n.endswith(".csv")][0]
        with z.open(name) as f:
            return pd.read_csv(f, usecols=COLUMNS, low_memory=False)


def summarise_routes(df):
    df = df.assign(Cancelled=df["Cancelled"].astype(int), Diverted=df["Diverted"].astype(int))
    flew = df["Cancelled"] == 0
    df = df.assign(
        weather_cancelled=(df["CancellationCode"] == "B").astype(int),
        flown_distance=df["Distance"].where(flew, 0.0),
    )
    keys = ["Year", "Month", "Reporting_Airline", "Origin", "Dest"]
    g = df.groupby(keys)
    out = pd.DataFrame({
        "flights": g.size(),
        "cancelled": g["Cancelled"].sum(),
        "weather_cancelled": g["weather_cancelled"].sum(),
        "diverted": g["Diverted"].sum(),
        "dep_delay_sum": g["DepDelay"].sum(),
        "dep_delay_n": g["DepDelay"].count(),
        "arr_delay_sum": g["ArrDelay"].sum(),
        "arr_delay_n": g["ArrDelay"].count(),
        "taxi_in_sum": g["TaxiIn"].sum(),
        "taxi_in_n": g["TaxiIn"].count(),
        "elapsed_sum": g["ActualElapsedTime"].sum(),
        "elapsed_n": g["ActualElapsedTime"].count(),
        "distance": g["Distance"].max(),
        "flown_distance": g["flown_distance"].sum(),
    })
    return out.reset_index()


def summarise_planes(df):
    flew = df[(df["Cancelled"] == 0) & df["Tail_Number"].notna()]
    g = flew.groupby(["Year", "Reporting_Airline", "Tail_Number"]).size()
    return g.rename("flights").reset_index()


def airport_rows(df):
    a = df[["Origin", "OriginCityName", "OriginState"]]
    a.columns = ["code", "city", "state"]
    b = df[["Dest", "DestCityName", "DestState"]]
    b.columns = ["code", "city", "state"]
    return pd.concat([a, b]).drop_duplicates("code")


def airport_names():
    # OpenFlights airports.dat has no header. Column 1 is the name, column 4 the IATA code.
    names = {}
    with open(os.path.join(RAW_DIR, "airports.dat"), encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) > 4 and row[4] not in ("", "\\N"):
                names.setdefault(row[4], row[1])
    return names


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    files = sorted(glob.glob(os.path.join(RAW_DIR, "ontime_*.zip")))
    if len(files) != 36:
        print(f"warning: expected 36 monthly files, found {len(files)}")

    routes, planes, airports = [], [], []
    for path in files:
        df = read_month(path)
        routes.append(summarise_routes(df))
        planes.append(summarise_planes(df))
        airports.append(airport_rows(df))
        print(f"{os.path.basename(path)}: {len(df):,} flights")

    routes = pd.concat(routes, ignore_index=True)
    planes = (pd.concat(planes).groupby(["Year", "Reporting_Airline", "Tail_Number"])
              ["flights"].sum().reset_index())
    airports = pd.concat(airports).drop_duplicates("code").sort_values("code")

    names = airport_names()
    airports["name"] = airports["code"].map(names)
    missing = airports["name"].isna().sum()
    airports["name"] = airports["name"].fillna(airports["city"])

    carriers = pd.DataFrame({"code": sorted(routes["Reporting_Airline"].unique())})
    carriers["name"] = carriers["code"].map(CARRIER_NAMES).fillna(carriers["code"])

    routes.to_csv(os.path.join(OUT_DIR, "routes.csv"), index=False)
    planes.to_csv(os.path.join(OUT_DIR, "planes.csv"), index=False)
    airports.to_csv(os.path.join(OUT_DIR, "airports.csv"), index=False)
    carriers.to_csv(os.path.join(OUT_DIR, "carriers.csv"), index=False)

    print(f"\n{routes['flights'].sum():,} flights in {len(routes):,} route groups")
    print(f"{len(airports)} airports ({missing} without a name in OpenFlights), "
          f"{len(carriers)} carriers, {planes['Tail_Number'].nunique():,} planes")


if __name__ == "__main__":
    main()
