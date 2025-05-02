import pandas as pd
import numpy as np
import simplekml
import argparse
nav_fix = pd.read_csv('FAA_data_20250123/FIX_BASE.csv')
alt_dict = {'low':'ENROUTE LOW', 'high':'ENROUTE HIGH'}

def dms_to_decimal(degrees, minutes, seconds, hemisphere):
    decimal = degrees + minutes / 60 + seconds / 3600
    if hemisphere in ['S', 'W']:
        decimal = -decimal
    return decimal
def write_fix_kml(kml,height,nav_fix, lat_min, lat_max, lon_min, lon_max):
    blue_style = simplekml.Style()
    blue_style.iconstyle.color = simplekml.Color.blue
    blue_style.iconstyle.scale = 1.0
    blue_style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/pushpin/blue-pushpin.png'
    # Add the style to the KML document
    #Add yellow style
    yellow_style = simplekml.Style()
    yellow_style.iconstyle.color = simplekml.Color.yellow
    yellow_style.iconstyle.scale = 1.0
    yellow_style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png'
    df = nav_fix[nav_fix['CHARTS'].str.contains(alt_dict[height], na=False)]
    for index, row in df.iterrows():
        lat = dms_to_decimal(row['LAT_DEG'], row['LAT_MIN'], row['LAT_SEC'], row['LAT_HEMIS'])
        lon = dms_to_decimal(row['LONG_DEG'], row['LONG_MIN'], row['LONG_SEC'], row['LONG_HEMIS'])
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:

            description = (
                f"Charts: {row['CHARTS']}<br>"
                f"State: {row['STATE_CODE']}<br>"
            )
            pnt = kml.newpoint(name=row['FIX_ID'],
                            coords=[(lon, lat)],)
            pnt.description = description
            if height == 'low':
                pnt.style = yellow_style
            else:
                pnt.style = blue_style
def main():
    parser = argparse.ArgumentParser(description='Generate KML files for GPS fixes.')
    parser.add_argument('lat_min', type=float, help='Minimum latitude')
    parser.add_argument('lat_max', type=float, help='Maximum latitude')
    parser.add_argument('lon_min', type=float, help='Minimum longitude')
    parser.add_argument('lon_max', type=float, help='Maximum longitude')
    args = parser.parse_args()

    nav_fix = pd.read_csv('FAA_data_20250123/FIX_BASE.csv')
    low_fix = simplekml.Kml()
    low_fix.document.name = 'GPS Fix Low'
    write_fix_kml(low_fix, 'low', nav_fix, args.lat_min, args.lat_max, args.lon_min, args.lon_max)

    low_fix.save('low_fix.kml')

    high_fix = simplekml.Kml()
    high_fix.document.name = 'GPS Fix High'
    write_fix_kml(high_fix, 'high', nav_fix, args.lat_min, args.lat_max, args.lon_min, args.lon_max)
    high_fix.save('high_fix.kml')

if __name__ == "__main__":
    main()
