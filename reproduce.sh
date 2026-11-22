#!/bin/bash
# Everything from raw data to results. Neo4j has to be running already.
set -e
./download_data.sh
python src/prepare_data.py
python src/load_graph.py
python src/run_queries.py
python src/check_results.py
