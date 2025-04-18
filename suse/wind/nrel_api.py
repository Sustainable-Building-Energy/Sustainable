from urllib.parse import urlencode
import requests
import pandas as pd
from io import StringIO


def download_offshore_ca_wind_data(
    *,
    api_key,
    wkt,
    email,
    year,
    show_url=False,
    attributes="wind_speed,wind_direction",
    interval=5,
    utc=True,
    leap_day=False,
    full_name="Aritro De",
    affiliation="University of Texas at Austin",
    reason="Graduate Research",
    url="https://developer.nrel.gov/api/wind-toolkit/v2/wind/offshore-ca-download.csv?"
):
    """
    Downloads wind data from the NREL Offshore California Wind Toolkit API.
    
    Args:
        api_key: NREL API key
        wkt: Well-Known Text representation of geometry
        email: Email address for API usage
        year: Year of data to fetch (can be string or integer)
        show_url: Whether to print the request URL
        attributes: Comma-separated list of attributes to fetch
        interval: Data interval in minutes
        utc: Whether to use UTC time
        leap_day: Whether to include leap day
        full_name: Full name for API usage
        affiliation: Affiliation for API usage
        reason: Reason for API usage
        url: API endpoint URL
        
    Returns:
        pandas.DataFrame: DataFrame containing wind data
    """

    query = {
        "api_key": api_key,
        "wkt": wkt,
        "attributes": attributes,
        "names": year,
        "email": email,
        "interval": interval,
        "utc": str(utc).lower(),
        "leap_day": str(leap_day).lower(),
        "full_name": full_name,
        "affiliation": affiliation,
        "reason": reason
    }

    request_url = url + urlencode(query)

    if show_url:
        print("Request URL:", request_url)

    try:
        response = requests.get(request_url)
        response.raise_for_status()

        # Read CSV from text response
        df = pd.read_csv(StringIO(response.text), skiprows=2)

        # Create a datetime column if time info is present
        time_columns = ["Year", "Month", "Day", "Hour", "Minute"]
        if all(col in df.columns for col in time_columns):
            df["Datetime"] = pd.to_datetime(df[time_columns])
        else:
            print("Time columns not found. Skipping 'Datetime' creation.")

        return df

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except pd.errors.ParserError as e:
        print(f"CSV parsing failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    return None
