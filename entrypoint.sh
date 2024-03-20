#!/bin/bash

# Start PostgreSQL in the background
# echo "STARTING POSTGRES"
# service postgres start

# Run Python scripts sequentially
cd src
echo "DOWNLOADING FILES AND CALCULATING AVG MAX PR AND WRITE"
python write_data_to_db.py
echo "COUNTRY MAPPING"
python get_country_city_names.py
echo "CALCULATE DAILY MAXIMUMS AND WRITE"
python get_daily_maximum.py
echo "START APP"
python visualization.py
