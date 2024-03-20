import xarray as xr
import os
import pandas as pd
import numpy as np
import traceback
import mevpy as mev
import pickle
from utils import get_db_engine


def get_daily_maximum_per_country(engine, year_start = 1994, year_end = 2014, target_folder = '../data'):
    """Calculates and Writes the daily maximum per country

    Args:
        engine (sqlalchemy engine): Engine
        year_start (int, optional): Start year for the analysis. Defaults to 1994.
        year_end (int, optional): End year for the analysis. Defaults to 2014.
        target_folder (str, optional): Data folder. Defaults to '../data'.

    Returns:
        pd.DataFrame: Partial result
    """
    
    print('Getting map_coord_to_loc')
    country_coord = pd.read_sql("SELECT * FROM map_coord_to_loc", engine).sort_values(by=['lat', 'lon'])
    country_coord = country_coord.drop(columns = ['lat', 'lon', 'closest_city'])
    
    temp_file = os.path.join(target_folder, '{year}.nc')
    for year in range(year_start, year_end+1):
        print(f'Calculating maximum daily precipitation in {year} for each country')

        ds = xr.open_dataset(temp_file.format(year=year))
        # Extract the variable you want to visualize (e.g., temperature)
        pr_data = (ds['pr']*86400) # direction given in the task
        pr_data = pr_data.to_numpy()
        #get rid of nan values for heal
        # the matrix operations
        pr_data[np.isnan(pr_data)] = 0

        res = pd.DataFrame()
        for i, date in enumerate(ds['time'].to_numpy()):
            print(f'Calculating for {date}')
            df = country_coord.copy()
            df['pr_mm'] = pr_data[i].flatten()
            df['datetime']= date
            df = df.groupby(['closest_country', 'datetime'])['pr_mm'].max().reset_index()

            res = pd.concat([res,df], ignore_index = True)
        print(f'Writing to max_daily_pr_country table for {year}')
        res.to_sql('max_daily_pr_country', con=engine, index=False, if_exists='append')


    engine.dispose()

    return res

def calculate_return_period(engine, year_start = 1994, year_end = 2014, target_folder = '../data/', overwrite=True):
    """Calculate necessary data points to plot return period

    Args:
        engine (sqlalchemy engine): Engine
        year_start (int, optional): Start year for the analysis. Defaults to 1994.
        year_end (int, optional): End year for the analysis. Defaults to 2014.
        target_folder (str, optional): Data folder. Defaults to '../data'.
        overwrite (bool, optional): True if want to overwrite the file. Defaults to True.

    Returns:
        dict: calculated traces to plot the return period
    """

    df = pd.read_sql('''
    SELECT *, DATE_PART('YEAR', datetime) as year FROM max_daily_pr_country
    WHERE datetime BETWEEN '{}-01-01' AND '{}-01-01'
    '''.format(year_start, year_end+1), engine)

    df = df.sort_values(by=['datetime', 'closest_country'])
    df = df.rename(columns = {'year':'YEAR', 'pr_mm':'PRCP'})


    res = {}

    for country in df.closest_country.unique():
        if country!='':
            print(f'calculating return values for {country}')
            temp = df[df.closest_country==country]
            temp = temp.sort_values(by = ['datetime', 'PRCP'], ascending = [True, False]).drop_duplicates(subset = ['datetime'], keep='first')
            XI,Fi,TR     = mev.tab_rain_max(temp)
            tr_min = 1
            tr_mask      = TR > tr_min
            TR_val       = TR[tr_mask]
            XI_val       = XI[tr_mask]
            Fi_val       = Fi[tr_mask]

            res[country] = {
                'TR_val':TR_val,
                'XI_val':XI_val,
                'Fi_val':Fi_val
            }
    
    if overwrite:
        with open(os.path.join(target_folder, 'country_pr_return_periods.pickle'), 'wb') as f:
            pickle.dump(res, f)

    return res
 


def main():
    """Main method
    """


    engine = get_db_engine()

    get_daily_maximum_per_country(engine)
    calculate_return_period(engine)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'Error in the pipeline {traceback.format_exc()}')

