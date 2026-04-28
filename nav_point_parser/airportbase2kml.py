import os
import pandas as pd
import numpy as np
import simplekml

KML_OUTPUT_DIR = 'kmls'

# APT_BASE.csv SITE_TYPE_CODE values to drop from the output:
#   H = heliport
#   U = ultralight
#   G = gliderport
#   B = balloonport
#   C = seaplane base
# (Only fixed-wing airports, code 'A', are kept.)
EXCLUDED_SITE_TYPE_CODES = {'H', 'U', 'G', 'B', 'C'}

# Drop airports without an ICAO ID whose FACILITY_USE_CODE is in this set.
# 'PR' is "private use" (closed to the general public); these are mostly the
# 4-character ARPT_IDs like "AL03" and "8AL3" and add a lot of clutter without
# being useful as visual references. Set to an empty set to keep them.
EXCLUDED_SMALL_FACILITY_USE_CODES = {'PR'}


def dms_to_decimal(degrees, minutes, seconds, hemisphere):
    decimal = degrees + minutes / 60 + seconds / 3600
    if hemisphere in ['S', 'W']:
        decimal = -decimal
    return decimal


def _make_red_circle_style(scale=1.0, label_scale=0):
    """Build a red placemark_circle style. label_scale=0 hides the name label
    next to the icon (the name still appears in the popup balloon on click);
    a positive value makes the label visible at the given scale (1.0 = default)."""
    style = simplekml.Style()
    style.iconstyle.color = simplekml.Color.red
    style.iconstyle.scale = scale
    style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png'
    style.labelstyle.scale = label_scale
    return style


def write_icao_airports(container, airports):
    """Write airports that have an ICAO ID using full-size red circles. The
    ICAO identifier is hidden by default (the label is too dense at the global
    zoom level) and shows in the popup balloon when the placemark is clicked."""
    style = _make_red_circle_style(scale=1.0)

    for _, row in airports.iterrows():
        if row.get('SITE_TYPE_CODE') in EXCLUDED_SITE_TYPE_CODES:
            continue
        if not ('ICAO_ID' in row and pd.notna(row['ICAO_ID']) and row['ICAO_ID'] != ''):
            continue

        lat = dms_to_decimal(row['LAT_DEG'], row['LAT_MIN'], row['LAT_SEC'], row['LAT_HEMIS'])
        lon = dms_to_decimal(row['LONG_DEG'], row['LONG_MIN'], row['LONG_SEC'], row['LONG_HEMIS'])

        description = (
            f"ICAO ID: {row['ICAO_ID']}<br>"
            f"Location: {row['CITY']}, {row['STATE_CODE']}<br>"
        )
        pnt = container.newpoint(name=row['ICAO_ID'], coords=[(lon, lat)])
        pnt.description = description
        pnt.style = style


def write_smaller_airports(container, airports):
    """Write airports without an ICAO ID using a slightly smaller red circle so
    they're visually distinguishable from the larger ICAO-coded fields."""
    style = _make_red_circle_style(scale=0.7)

    for _, row in airports.iterrows():
        if row.get('SITE_TYPE_CODE') in EXCLUDED_SITE_TYPE_CODES:
            continue
        if 'ICAO_ID' in row and pd.notna(row['ICAO_ID']) and row['ICAO_ID'] != '':
            continue  # handled by write_icao_airports
        if row.get('FACILITY_USE_CODE') in EXCLUDED_SMALL_FACILITY_USE_CODES:
            continue

        lat = dms_to_decimal(row['LAT_DEG'], row['LAT_MIN'], row['LAT_SEC'], row['LAT_HEMIS'])
        lon = dms_to_decimal(row['LONG_DEG'], row['LONG_MIN'], row['LONG_SEC'], row['LONG_HEMIS'])

        # FAA airport identifier (e.g. "0J0") - the only airport-side ID these have.
        arpt_id = row['ARPT_ID'] if pd.notna(row['ARPT_ID']) else ''
        arpt_name = row['ARPT_NAME'] if 'ARPT_NAME' in row and pd.notna(row['ARPT_NAME']) else ''

        description_parts = [f"FAA ID: {arpt_id}<br>"]
        if arpt_name:
            description_parts.append(f"Name: {arpt_name}<br>")
        description_parts.append(f"Location: {row['CITY']}, {row['STATE_CODE']}<br>")
        description = ''.join(description_parts)

        # Fall back to the airport name if there's no FAA ID for some reason.
        placemark_name = arpt_id or arpt_name or 'airport'
        pnt = container.newpoint(name=placemark_name, coords=[(lon, lat)])
        pnt.description = description
        pnt.style = style


def main():
    # Read the airport data
    airports = pd.read_csv('latest_data/APT_BASE.csv', low_memory=False)

    # Single KML file with both groups of airports
    kml = simplekml.Kml()
    kml.document.name = 'Airports'

    # Folders keep the two groups separately toggleable in Google Earth
    icao_folder = kml.newfolder(name='Airports with ICAO ID')
    smaller_folder = kml.newfolder(name='Smaller Airports (no ICAO ID)')

    write_icao_airports(icao_folder, airports)
    write_smaller_airports(smaller_folder, airports)

    # Save the KML file
    os.makedirs(KML_OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(KML_OUTPUT_DIR, 'airport.kml')
    kml.save(output_path)
    print(f"Created KML file with all airports: {output_path}")


if __name__ == "__main__":
    main()
