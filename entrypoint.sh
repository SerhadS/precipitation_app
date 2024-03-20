#!/bin/bash

# Start PostgreSQL in the background
echo "STARTING POSTGRES"
service postgres start

# Run Python scripts sequentially

cd src
if [ ! -f /data/scripts_executed.txt ]; then
    echo "DOWNLOADING FILES AND CALCULATING AVG MAX PR AND WRITE"
    python write_data_to_db.py
    echo "COUNTRY MAPPING"
    python get_country_city_names.py
    echo "CALCULATE DAILY MAXIMUMS AND WRITE"
    python get_daily_maximum.py

    # Create a flag file to indicate scripts execution
    touch /data/scripts_executed.txt
fi

echo "START APP"
python visualization.py
