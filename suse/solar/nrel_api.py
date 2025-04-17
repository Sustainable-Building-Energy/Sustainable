from urllib.parse import urlencode

import pandas as pd


def download_solar_data(
    *,
    api_key,
    wkt,
    email,
    year,
    show_url=False,
    attributes="dhi,ghi,dni,alpha,solar_zenith_angle",
    url="https://developer.nrel.gov/api/nsrdb/v2/solar/nsrdb-GOES-conus-v4-0-0-download.csv?"
):
    query = {"api_key": api_key, "wkt": wkt, "attributes": attributes, "names": year, "email": email}
    request_url = url + urlencode(query)

    if show_url:
        print(request_url)
    df = pd.read_csv(request_url, skiprows=2).rename(columns={'DNI':"DNI (W/m^2)", 'GHI':"GHI (W/m^2)"})
    df["Datetime"] = df[["Year", "Month", "Day", "Hour", "Minute"]].apply(
        lambda row: pd.Timestamp(
            year=row["Year"], month=row["Month"], day=row["Day"], hour=row["Hour"], minute=row["Minute"]
        ),
        axis=1,
    )
    return df
