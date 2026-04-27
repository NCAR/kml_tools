import os
import pandas as pd
import numpy as np
import simplekml
import argparse

KML_OUTPUT_DIR = 'kmls'
nav_fix = pd.read_csv('latest_data/FIX_BASE.csv')
alt_dict = {'low':'ENROUTE LOW', 'high':'ENROUTE HIGH'}

def dms_to_decimal(degrees, minutes, seconds, hemisphere):
    decimal = degrees + minutes / 60 + seconds / 3600
    if hemisphere in ['S', 'W']:
        decimal = -decimal
    return decimal
def write_fix_kml(container, height, nav_fix, lat_min, lat_max, lon_min, lon_max):
    blue_style = simplekml.Style()
    blue_style.iconstyle.color = simplekml.Color.blue
    blue_style.iconstyle.scale = 1.0
    blue_style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png'
    # Hide the name label next to the icon by default; the name still shows in
    # the popup balloon when the placemark is clicked.
    blue_style.labelstyle.scale = 0

    df = nav_fix[nav_fix['CHARTS'].str.contains(alt_dict[height], na=False)]
    for index, row in df.iterrows():
        lat = dms_to_decimal(row['LAT_DEG'], row['LAT_MIN'], row['LAT_SEC'], row['LAT_HEMIS'])
        lon = dms_to_decimal(row['LONG_DEG'], row['LONG_MIN'], row['LONG_SEC'], row['LONG_HEMIS'])
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:

            description = (
                f"Charts: {row['CHARTS']}<br>"
                f"State: {row['STATE_CODE']}<br>"
            )
            pnt = container.newpoint(name=row['FIX_ID'],
                            coords=[(lon, lat)],)
            pnt.description = description
            pnt.style = blue_style
def main():
    parser = argparse.ArgumentParser(description='Generate a KML file for GPS fixes (high and low altitude combined).')
    parser.add_argument('lat_min', type=float, help='Minimum latitude')
    parser.add_argument('lat_max', type=float, help='Maximum latitude')
    parser.add_argument('lon_min', type=float, help='Minimum longitude')
    parser.add_argument('lon_max', type=float, help='Maximum longitude')
    args = parser.parse_args()

    nav_fix = pd.read_csv('latest_data/FIX_BASE.csv')

    # Single KML containing both high and low altitude GPS fixes
    kml = simplekml.Kml()
    kml.document.name = 'GPS Fixes (High and Low Altitude)'

    # Folders keep the two groups visually grouped within the single file
    high_folder = kml.newfolder(name='GPS Fix High')
    low_folder = kml.newfolder(name='GPS Fix Low')

    write_fix_kml(high_folder, 'high', nav_fix, args.lat_min, args.lat_max, args.lon_min, args.lon_max)
    write_fix_kml(low_folder, 'low', nav_fix, args.lat_min, args.lat_max, args.lon_min, args.lon_max)

    os.makedirs(KML_OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(KML_OUTPUT_DIR, 'gps_fixes.kml')
    kml.save(output_path)
    print(f"Created KML file with high and low altitude GPS fixes: {output_path}")

if __name__ == "__main__":
    main()
