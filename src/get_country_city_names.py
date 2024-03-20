import xarray as xr
import os
import pandas as pd
import numpy as np
import traceback
import reverse_geocode
from utils import get_db_engine


def write_country_names_on_coordinates(coordinates):
    """Get the city and country names for a given set of coordinates
    and write it to postgres table

    Args:
        coordinates (pd.DataFrame): A pandas dataframe which has coordinates in 'lat' and 'lon' columns
    """
    engine = get_db_engine()
    

    coord = [tuple(row) for index, row in coordinates[['lat', 'lon_adapted']].iterrows()]
    x = reverse_geocode.search(coord)

    coordinates['closest_city'] = [y['city'] for y in x]
    coordinates['closest_country'] = [y['country'] for y in x]
    cols = ['lat', 'lon', 'closest_country', 'closest_city']

    coordinates[cols].to_sql('map_coord_to_loc', con=engine, index=False, if_exists='replace')

    engine.dispose()

    return 1

def main():
    """Main Function

    """

    temp_file = '../data/2000.nc'
    ds = xr.open_dataset(temp_file)

    df = pd.DataFrame()
    df['lat'] = np.tile(ds['lat'].to_numpy(), ds['lon'].shape[0])
    df['lon'] = np.repeat(ds['lon'].to_numpy(), ds['lat'].shape[0])
    df['lon_adapted'] = df['lon'].apply(lambda x:x-360 if x>180 else x)
    df.to_parquet('serhad.parquet')

    write_country_names_on_coordinates(df)

    return 1

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'Error in the pipeline {traceback.format_exc()}')

