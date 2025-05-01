import os
from pathlib import Path

import pandas as pd
from dotenv import dotenv_values, load_dotenv

from suse.wind.wind_calc import compute_environmental_params
from suse.wind.nrel_api import download_offshore_ca_wind_data

load_dotenv()
NREL_KEY = os.environ.get("NREL_API_KEY")
EMAIL = os.environ.get("EMAIL")

DATA_DIR = r'G:\My Drive\UT_Austin_MSSD\Semester 2\03 Sustainable Energy for Built Env\34 Final project\Sustainable\data\wind'

# Input options
lat = 36.5
lon = -122.5
year = "2019"  # Change this value to fetch data for different years
wind_file = f'{DATA_DIR}/wind_data_{year}.parquet'

geometry = f"POINT ({lon} {lat})"

try:
    Path(DATA_DIR).mkdir(parents=True,exist_ok=True)
    df = pd.read_parquet(wind_file)
except:
    df = download_offshore_ca_wind_data(year=year,wkt=geometry,email=EMAIL,api_key=NREL_KEY)
    df.to_parquet(wind_file)

df = compute_environmental_params(df,lon=lon,lat=lat)
print(df)