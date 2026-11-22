#!/bin/bash
# Download the BTS on-time files for 2014-2016 (36 zip files, about 800 MB)
# and the OpenFlights airport list (for airport names).
set -e
mkdir -p data/raw
cd data/raw

for y in 2014 2015 2016; do
  for m in $(seq 1 12); do
    f="ontime_${y}_${m}.zip"
    [ -s "$f" ] && continue
    echo "downloading $f"
    curl -sL --retry 3 -o "$f" \
      "https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_${y}_${m}.zip"
  done
done

[ -s airports.dat ] || curl -sL -o airports.dat \
  https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat
echo "done"
