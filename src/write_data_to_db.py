import xarray as xr
import os
import pandas as pd
import numpy as np
import traceback
import gc
from utils import file_download
from utils import get_db_engine


def download_nc_files_from_s3(year_start=1994, year_end=2014, target_folder = '../data'):
    """download files from s3 bucket

    Args:
        year_start (int, optional): Start year. Defaults to 1994.
        year_end (int, optional): End year. Defaults to 2014.
    """
    # URL of the public S3 bucket
    bucket_url = 'https://nex-gddp-cmip6.s3.us-west-2.amazonaws.com/NEX-GDDP-CMIP6/ACCESS-CM2/historical/r1i1p1f1/pr/'
    year = 1994
    filename_pattern = 'pr_day_ACCESS-CM2_historical_r1i1p1f1_gn_{year}.nc'
    temp_file = os.path.join(target_folder, '{year}.nc')

    for year in range(year_start,year_end+1):
        if not os.path.exists(temp_file.format(year=year)):

            print(f'Downloading {os.path.join(bucket_url,filename_pattern.format(year=year))}')
            try:
                file_download(os.path.join(bucket_url,filename_pattern.format(year=year)), temp_file.format(year=year))
                print(f'Download complete {temp_file.format(year=year)}')
            except Exception as e:
                print(f'Download failed: {traceback.format_exc()}')
    
    return None


def calculate_extreme_threshold(year_start = 1994, year_end = 2014, target_folder = '../data'):
    """Calculates extreme rain event threshold for each grid

    Args:
        year_start (int, optional): Start year. Defaults to 1994.
        year_end (int, optional): End year. Defaults to 2014.
        target_folder (str, optional): The data folder. Defaults to '../data'.

    Returns:
        mean_arr(np.array), acc_arr(np.array), acc_arr_count(np.array): mean of extreme events, accumulated pr of extreme events, number of extreme events
    """

    acc_arr = None
    acc_arr_count = None
    
    temp_file = os.path.join(target_folder, '{year}.nc')
    # temp = []
    for year in range(year_start, year_end+1):
        print(f'Calculating maximum precipitation in {year}')

        ds = xr.open_dataset(temp_file.format(year=year))
        # Extract the variable you want to visualize (e.g., temperature)
        pr_data = (ds['pr']*86400) # direction given in the task
        pr_data = pr_data.to_numpy()
        #get rid of nan values for healthy matrix operations
        pr_data[np.isnan(pr_data)] = 0
        pr_data=pr_data.max(axis=0) # find the max pr in the year
        if acc_arr is None:
            acc_arr = np.zeros_like(pr_data)
            acc_arr_count = np.zeros_like(acc_arr)
            acc_arr_count[pr_data>=1] = 1
            acc_arr = pr_data.copy()
        else:
            acc_arr_count[pr_data>=1] += 1
            acc_arr = np.add(acc_arr, pr_data)

    mean_arr = np.divide(acc_arr, acc_arr_count, out=np.zeros_like(acc_arr), where=acc_arr_count!=0)

    return mean_arr, acc_arr, acc_arr_count


def write_extreme_events_db(threshold_array, engine, year_start = 1994, year_end=2014, target_folder = '../data'):
    """Writes extreme rain events for each grid (extreme for that grid) to DB

    Args:
        threshold_array (np.array): Mean max pr for each grid. To be used as threshold for defining extreme events.
        engine (sqlalcemy conn engine): connection engine
        year_start (int, optional): Start year. Defaults to 1994.
        year_end (int, optional): End year. Defaults to 2014.
        target_folder (str, optional): The data folder. Defaults to '../data'.

    Returns:
        pd.DataFrame: partial resultant dataframe that is written to db
    """
    temp_file = os.path.join(target_folder, '{year}.nc')

    for year in range(year_start, year_end+1):
        print(f'Calculating maximum precipitation in {year}')

        ds = xr.open_dataset(temp_file.format(year=year))

        pr_data = (ds['pr']*86400) # direction given in the task
        pr_data = pr_data.to_numpy()
        x = np.where((pr_data>=1)&(pr_data>=threshold_array))

        res = pd.DataFrame()
        res['datetime'] = ds['time'][x[0]].values
        res['lat'] = ds['lat'][x[1]].values
        res['lon'] = ds['lon'][x[2]].values
        res['pr_mm'] = pr_data[x]

        del ds, pr_data
        gc.collect()
        print(f'Writing extreme rainfall events in {year} to DB')
        res.to_sql('extreme_rainfall_events', con=engine, index=False, if_exists='append')

        del res
        gc.collect()

    return res

def main():
    """Main function
    """

    # get the env params for db access

   
    engine = get_db_engine()
    
    # download files from s3 bucket
    download_nc_files_from_s3(year_start=1994, year_end=2014, target_folder = '../data')
    # get the extreme event thresholds
    # assumption made to do not count precipitation events smaller than 1 mm/day
    extreme_threshold, _, _ = calculate_extreme_threshold(target_folder = '../data', year_start= 1994, year_end = 2014)

    del _
    gc.collect()
    # write extreme events to postgres db
    write_extreme_events_db(extreme_threshold, engine, year_start = 1994, year_end=2014, target_folder = '../data')

    engine.dispose()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'Error in the pipeline {traceback.format_exc()}')

