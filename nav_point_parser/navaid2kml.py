import os
import pandas as pd
import numpy as np
import simplekml

KML_OUTPUT_DIR = 'kmls'
alt_dict = {'low': ['L', 'VL'], 'high': ['H', 'VH']}


def dms_to_decimal(degrees, minutes, seconds, direction):
    decimal = degrees + minutes / 60 + seconds / 3600
    if direction in ['S', 'W']:
        decimal = -decimal
    return decimal


def write_kml(container, height, vor):
    yellow_style = simplekml.Style()
    yellow_style.iconstyle.color = simplekml.Color.yellow
    # 0.7 matches the "smaller airports" scale in airportbase2kml.py; ICAO
    # airports stay at the default 1.0 so they remain visually prominent.
    yellow_style.iconstyle.scale = 0.7
    yellow_style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png'
    # Hide the name label next to the icon by default; the name still shows in
    # the popup balloon when the placemark is clicked.
    yellow_style.labelstyle.scale = 0

    df = vor[vor['ALT_CODE'].isin(alt_dict[height])]
    for index, row in df.iterrows():
        lat = dms_to_decimal(row['LAT_DEG'], row['LAT_MIN'], row['LAT_SEC'], row['LAT_HEMIS'])
        lon = dms_to_decimal(row['LONG_DEG'], row['LONG_MIN'], row['LONG_SEC'], row['LONG_HEMIS'])
        mag_deviation = f"{row['MAG_VARN_HEMIS']}{int(row['MAG_VARN'])}\u00b0"
        description = (
            f"Altitude Code: {row['ALT_CODE']}<br>"
            f"Magnetic Deviation: {mag_deviation}<br>"
            f"City: {row['CITY']}, {row['STATE_CODE']}<br>"
            f"Frequency: {row['FREQ']} MHz"
        )
        pnt = container.newpoint(name=row['NAV_ID'], coords=[(lon, lat)])
        pnt.description = description
        pnt.style = yellow_style


def main():
    # Open NAV_BASE file
    nav_base = pd.read_csv('latest_data/NAV_BASE.csv')
    # Filter dataframe by NAV_TYPE
    vor = nav_base[nav_base['NAV_TYPE'].isin(['VOR', 'TACAN', 'VOR/DME', 'VORTAC'])]

    # Single KML containing both high and low altitude VOR stations
    kml = simplekml.Kml()
    kml.document.name = 'VOR Stations (High and Low Altitude)'

    # Folders keep the high and low navaids visually grouped within the single file
    high_folder = kml.newfolder(name='High Altitude VOR Stations')
    low_folder = kml.newfolder(name='Low Altitude VOR Stations')

    write_kml(high_folder, 'high', vor)
    write_kml(low_folder, 'low', vor)

    os.makedirs(KML_OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(KML_OUTPUT_DIR, 'vor_stations.kml')
    kml.save(output_path)
    print(f"Created KML file with high and low altitude VOR stations: {output_path}")


if __name__ == "__main__":
    main()
