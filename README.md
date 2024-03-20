**Detecting Extreme Rainfall Events**

This repository introduces an app to visualize extreme rainfall events between years 1994 and 2014.

**Data source**

The main data source used in this case is NASA’s Earth Exchange Global Daily Downscaled Projections (NEX-GDDP-CMIP6) which contains daily raw climate data to a 1/4° spatial resolution (~25km).

The dataset that was extracted from the following S3 bucket:

[NEX-GDDP-CMIP6 | Data Browse (amazonaws.com)](https://nex-gddp-cmip6.s3.us-west-2.amazonaws.com/index.html#NEX-GDDP-CMIP6/ACCESS-CM2/historical/r1i1p1f1/pr/)


<br>

**Main Goals**

The app’s main goals can be summarized as follows:

1- Determine extreme rainfall thresholds in grid level and visualize top events (with highest precipitation levels) worldwide per year.

2- Determine the return-period of the rainfall events per country and visualize.

3- Visualize yearly distribution of extreme rainfall events per country and visualize.

4- Determine countries with the most extreme events per year and report.

<br>

**Setup**

To run the app, you should install docker. After installing docker, please follow the below steps:

```git clone https://github.com/SerhadS/precipitation_app.git extreme_rainfall```

```cd extreme_rainfall```

```docker-compose up```

The series of commands above will create a postgres database, download necessary files from S3 bucket, process the files to write aggregated data for analysis, and finally start a web-app to visualize the processed data.

The dashboard (web-app) can be reached through ```localhost:4255```.

If required, the files can be executed manually to be able to start app in your own environment following the below steps. Please note that this repo is tested in Python 3.11. Execution is not guaranteed in other python versions:

```git clone https://github.com/SerhadS/precipitation_app.git extreme_rainfall```

```cd extreme_rainfall/src```

```<CREATE OR SWITCH TO YOUR OWN PYTHON ENV>```

```pip install requirements.txt```

```python write_data_to_db.py```

```python get_country_city_names.py```

```python get_daily_maximum.py```

```python visualization.py```

<br>

**Repo Structure**

    | - src

        | - mevpy /

        | - get_country_city_names.py

        | - get_daily_maximum.py

        | - requirements.txt

        | - visualization.py

        | - write_data_to_db.py 

    | - data

    | - Dockerfile

    | - docker-compose.yaml


<br>

**File definitions:**



* write_data_to_db.py: includes methods to download necessary files from S3 bucket, process them, identify extreme rainfall thresholds for each grid, and identify events for each grid which are above the defined thresholds.
* get_country_city_names.py: Maps each grid to the closest country and city.
* get_daily_maximum.py: Aggregated precipitation data at the country level to identify maximum rainfall for each day in order to calculate the return period of rainfall events.
* visualization.py: Creates and serves the dashboard.
* mevpy: external package

<br>

**High-level Design:**


![alt_text](data/image1.jpg "image1")

<br>


**Data Model**

The data model is given in ./data/DataModel.xlsx

<br>


**The Dashboard**
The dashboard consists of four fields
- World Map, showing 99th percentile of extreme rainfall events for a selected year.
- A table showing countries with most distinct events for a selected year.
- Distribution of precipitation levels in mm for events over grid threshold for a given country for the selected year.
- Return period plot for the selected country.

![alt_text](data/image2.png "Image2")

<br>


**Determination of extreme rainfall thresholds**

The logic for determination of thresholds for each grid was simple. It is basically the mean of maximum precipitation levels attained in years under investigation. These mean values for each grid are then used to identify extreme rainfall events. The only assumption made during the calculation of thresholds is ‘filtering out the precipitation levels lower than 1mm’ to avoid left-skewed distributions and noise build up. 

In the visualization (world-map), only the events that make up to 99th percentile (most extreme in a given year) are plotted to keep the dashboard clean and easily comprehensible.

<br>

**Determination of return values per country:**

For each day, the maximum precipitation within a country is identified and recorded for the period of the study (21 years). Therefore, it was possible to calculate the discrete return period of the events aggregated at the country level. Models can be fit to this data to mathematical modelling of these return periods. However, for this case study, the graphs are plotted using only the observed data.