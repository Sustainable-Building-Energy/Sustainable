import numpy as np
import pandas as pd

# Reimplement trig functions to accept degrees
def sin(value):
    return np.sin(np.deg2rad(value))

def cos(value):
    return np.cos(np.deg2rad(value))

def arccos(value):
    return np.rad2deg(np.arccos(value))

def to_solar_time(std_time, L_st, L_loc, n):
    B = 360 * (n - 81) / 364
    E = 9.87 * sin(2 * B) - 7.53 * cos(B) - 1.5 * sin(B)
    solar_time = std_time + pd.to_timedelta(4 * (L_st - L_loc) + E, "minutes").dt.round("min")
    return solar_time

def get_hour_angle():
    pass

def get_declination(n):
    # Represented by delta
    return 23.45 * sin(360 * (284 + n) / 365)

def get_incid_angle(*, lat, slope, declin, solar_hour):
    # Represented by theta
    return arccos(cos(lat - slope) * cos(declin) * cos(solar_hour) + sin(lat - slope) * sin(declin))

def get_solar_zenith(lat, declin, solar_hour):
    return get_incid_angle(lat=lat, slope=0, declin=declin, solar_hour=solar_hour)

def get_beam_incid(Gbn, incid_angle):
    return Gbn * cos(incid_angle)

def get_beam_horiz(Gbn, solar_zenith):
    return Gbn * cos(solar_zenith)

def get_diffuse(GHI, Gb):
    return GHI - Gb

def get_tot_incid_rad(Gbt, Gd, slope, grd_reflect, GHI):
    return Gbt + Gd * ((1 + cos(slope)) / 2) + grd_reflect * GHI * ((1 - cos(slope)) / 2)

def compute_environmental_params(df,*,lon,lat):
    L_st = round(lon/15)*15
    L_loc = lon
    # Compute stuff
    df["Solar Time"] = to_solar_time(df["Datetime"], L_st=L_st, L_loc=L_loc, n=df["Datetime"].dt.dayofyear)
    df["δ"] = get_declination(df["Datetime"].dt.dayofyear)
    df["ω"] = 15 * ((df["Solar Time"].dt.hour + df["Solar Time"].dt.minute / 60) - 12)
    df["θz"] = get_solar_zenith(lat=lat, declin=df["δ"], solar_hour=df["ω"])
    df["G_b"] = get_beam_horiz(df["DNI (W/m^2)"], df["θz"])
    df["G_d"] = get_diffuse(df["GHI (W/m^2)"], df["G_b"])
    # df["θ"] = get_incid_angle(lat=lat, slope=slope, declin=df["δ"], solar_hour=df["ω"])
    return df