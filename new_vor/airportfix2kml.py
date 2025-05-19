import pandas as pd
import numpy as np
import simplekml
import argparse

def dms_to_decimal(degrees, minutes, seconds, hemisphere):
    decimal = degrees + minutes / 60 + seconds / 3600
    if hemisphere in ['S', 'W']:
        decimal = -decimal
    return decimal

def write_approach_fix_kml(kml, nav_fix, lat_min, lat_max, lon_min, lon_max):
    # Create a single style for all approach fixes
    fix_style = simplekml.Style()
    fix_style.iconstyle.color = simplekml.Color.orange  # Using orange for all approach fixes
    fix_style.iconstyle.scale = 1.0
    fix_style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png'
    # Create pattern to match any of SID, STAR, or IAP
    pattern = 'SID|STAR|IAP'
    
    # Filter for fixes that contain any of the procedure types
    df = nav_fix[nav_fix['CHARTS'].str.contains(pattern, na=False, regex=True)]
    
    # Process each fix
    for index, row in df.iterrows():
        lat = dms_to_decimal(row['LAT_DEG'], row['LAT_MIN'], row['LAT_SEC'], row['LAT_HEMIS'])
        lon = dms_to_decimal(row['LONG_DEG'], row['LONG_MIN'], row['LONG_SEC'], row['LONG_HEMIS'])
        
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            # Create description with procedure types highlighted
            description = (
                f"Charts: {row['CHARTS']}<br>"
                f"State: {row['STATE_CODE']}<br>"
            )
            
            # Create the point
            pnt = kml.newpoint(name=row['FIX_ID'], coords=[(lon, lat)])
            pnt.description = description
            
            # Apply the single style to all points
            pnt.style = fix_style

def main():
    parser = argparse.ArgumentParser(description='Generate KML file for approach fixes (SID, STAR, IAP).')
    parser.add_argument('lat_min', type=float, help='Minimum latitude')
    parser.add_argument('lat_max', type=float, help='Maximum latitude')
    parser.add_argument('lon_min', type=float, help='Minimum longitude')
    parser.add_argument('lon_max', type=float, help='Maximum longitude')
    args = parser.parse_args()

    # Read the navigation fix data
    nav_fix = pd.read_csv('FAA_data_20250123/FIX_BASE.csv')
    
    # Create a single KML file for all approach fixes
    approach_fixes = simplekml.Kml()
    approach_fixes.document.name = 'GPS Fixes Airports'
    
    # Write all the approach fixes to the KML file
    write_approach_fix_kml(approach_fixes, nav_fix, args.lat_min, args.lat_max, args.lon_min, args.lon_max)
    
    # Save the KML file
    approach_fixes.save('approach_fixes.kml')
    print(f"Created KML file with SID, STAR, and IAP fixes within the specified boundaries.")

if __name__ == "__main__":
    main()