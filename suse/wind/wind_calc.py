import pandas as pd
import numpy as np

def compute_environmental_params(df, lon, lat):
    """
    Compute environmental parameters from wind data.
    
    Args:
        df: DataFrame containing wind data
        lon: Longitude coordinate
        lat: Latitude coordinate
        
    Returns:
        DataFrame with additional computed parameters
    """
    # Add basic calculations here
    # Example: Convert wind speed from m/s to km/h
    if 'wind_speed' in df.columns:
        df['wind_speed_kmh'] = df['wind_speed'] * 3.6
    
    # Add location coordinates
    df['longitude'] = lon
    df['latitude'] = lat
    
    return df