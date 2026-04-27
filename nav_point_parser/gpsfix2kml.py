"""Generate kmls/gps_fixes.kml from latest_data/FIX_BASE.csv.

This script is the merged replacement for the old navfix2kml.py + airportfix2kml.py
pair. The previous two scripts each filtered FIX_BASE.csv against the multi-valued
CHARTS column independently, so a fix listed on more than one chart series (e.g.
SPAMY: CONTROLLER, ENROUTE HIGH, ENROUTE LOW, STAR) ended up appearing once per
matching script -- a duplicate when the outputs were combined.

Here, each fix is classified into exactly one folder using the priority order:
    Approach (SID/STAR/IAP) > En-Route High > En-Route Low
The full CHARTS string is preserved in the placemark description so the other
contexts a fix is used in remain visible on click.
"""

import os
import pandas as pd
import simplekml

KML_OUTPUT_DIR = 'kmls'

# Priority order for assigning each fix to a single folder. The first matching
# token wins; the rest of the CHARTS string is still surfaced in the description.
APPROACH_TOKENS = ('SID', 'STAR', 'IAP')
HIGH_TOKEN = 'ENROUTE HIGH'
LOW_TOKEN = 'ENROUTE LOW'


def dms_to_decimal(degrees, minutes, seconds, hemisphere):
    decimal = degrees + minutes / 60 + seconds / 3600
    if hemisphere in ['S', 'W']:
        decimal = -decimal
    return decimal


def _classify(charts):
    """Return 'approach', 'high', 'low', or None for a CHARTS string."""
    if not isinstance(charts, str):
        return None
    if any(tok in charts for tok in APPROACH_TOKENS):
        return 'approach'
    if HIGH_TOKEN in charts:
        return 'high'
    if LOW_TOKEN in charts:
        return 'low'
    return None  # CHARTS doesn't include any series we render


def _make_circle_style(color):
    style = simplekml.Style()
    style.iconstyle.color = color
    # 0.7 matches the "smaller airports" scale in airportbase2kml.py; ICAO
    # airports stay at 1.0 so they remain visually prominent.
    style.iconstyle.scale = 0.7
    style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png'
    # Hide the name label next to the icon by default; the name still shows in
    # the popup balloon when the placemark is clicked.
    style.labelstyle.scale = 0
    return style


def write_fixes(kml, nav_fix):
    approach_folder = kml.newfolder(name='Approach Fixes (SID/STAR/IAP)')
    high_folder = kml.newfolder(name='High Altitude En-Route Fixes')
    low_folder = kml.newfolder(name='Low Altitude En-Route Fixes')

    folders = {
        'approach': approach_folder,
        'high': high_folder,
        'low': low_folder,
    }
    styles = {
        'approach': _make_circle_style(simplekml.Color.blue),
        'high': _make_circle_style(simplekml.Color.blue),
        'low': _make_circle_style(simplekml.Color.blue),
    }
    counts = {'approach': 0, 'high': 0, 'low': 0, 'skipped': 0}

    for _, row in nav_fix.iterrows():
        category = _classify(row.get('CHARTS'))
        if category is None:
            counts['skipped'] += 1
            continue

        lat = dms_to_decimal(row['LAT_DEG'], row['LAT_MIN'], row['LAT_SEC'], row['LAT_HEMIS'])
        lon = dms_to_decimal(row['LONG_DEG'], row['LONG_MIN'], row['LONG_SEC'], row['LONG_HEMIS'])

        description = (
            f"Charts: {row['CHARTS']}<br>"
            f"State: {row['STATE_CODE']}<br>"
        )
        pnt = folders[category].newpoint(name=row['FIX_ID'], coords=[(lon, lat)])
        pnt.description = description
        pnt.style = styles[category]
        counts[category] += 1

    return counts


def main():
    nav_fix = pd.read_csv('latest_data/FIX_BASE.csv', low_memory=False)

    kml = simplekml.Kml()
    kml.document.name = 'GPS Fixes (Approach and En-Route)'

    counts = write_fixes(kml, nav_fix)

    os.makedirs(KML_OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(KML_OUTPUT_DIR, 'gps_fixes.kml')
    kml.save(output_path)
    print(
        f"Created KML file with GPS fixes: {output_path}\n"
        f"  approach: {counts['approach']}, high: {counts['high']}, low: {counts['low']}"
    )


if __name__ == '__main__':
    main()
