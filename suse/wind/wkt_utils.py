"""Utility functions for working with WKT (Well-Known Text) geometry strings."""

def extract_coordinates_from_wkt(wkt_string):
    """
    Extract coordinates from a WKT (Well-Known Text) geometry string.
    
    Args:
        wkt_string: A WKT geometry string (e.g., "POINT (-122.5 36.5)")
        
    Returns:
        tuple: (longitude, latitude) coordinates or (None, None) if parsing fails
    """
    if not isinstance(wkt_string, str):
        return None, None
        
    try:
        if wkt_string.startswith('POINT'):
            # Parse POINT format: "POINT (lon lat)"
            coords = wkt_string.replace('POINT (', '').replace(')', '').split()
            if len(coords) >= 2:
                return float(coords[0]), float(coords[1])
        elif wkt_string.startswith('POLYGON'):
            # For future implementation - parse POLYGON format
            pass
    except (ValueError, IndexError):
        pass
        
    return None, None

def create_point_wkt(lon, lat):
    """
    Create a WKT POINT string from longitude and latitude coordinates.
    
    Args:
        lon: Longitude coordinate
        lat: Latitude coordinate
        
    Returns:
        str: WKT POINT string
    """
    return f"POINT ({lon} {lat})"