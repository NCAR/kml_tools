"""Filter kmls/all_nav_points.kml to a lat/lon bounding box.

Reads a previously combined KML, drops every <Placemark> whose <Point>
falls outside the supplied bounding box, prunes any folder that ends up empty,
and writes kmls/all_nav_points_bounded.kml. Styles, folder names, and the rest
of the document structure are preserved so the bounded file can be opened in
Google Earth and look exactly like a geographically clipped slice of the
original.

Usage:
    python bound_kml.py LAT_MIN LAT_MAX LON_MIN LON_MAX
        [--input kmls/all_nav_points.kml]
        [--output kmls/all_nav_points_bounded.kml]
"""
import argparse
import os
import xml.etree.ElementTree as ET

KML_NS = 'http://www.opengis.net/kml/2.2'
ET.register_namespace('', KML_NS)

KML_OUTPUT_DIR = 'kmls'
DEFAULT_INPUT = os.path.join(KML_OUTPUT_DIR, 'all_nav_points.kml')
DEFAULT_OUTPUT = os.path.join(KML_OUTPUT_DIR, 'all_nav_points_bounded.kml')


def _kml(tag):
    return f'{{{KML_NS}}}{tag}'


def _local(tag):
    return tag.split('}', 1)[-1] if '}' in tag else tag


def _placemark_coord(placemark):
    """Return (lon, lat) for a placemark, or None if it has no Point."""
    point = placemark.find(_kml('Point'))
    if point is None:
        return None
    coords = point.find(_kml('coordinates'))
    if coords is None or not (coords.text and coords.text.strip()):
        return None
    # KML coordinates: "lon,lat[,alt]" - whitespace is permissible
    parts = coords.text.strip().split(',')
    if len(parts) < 2:
        return None
    try:
        lon = float(parts[0])
        lat = float(parts[1])
    except ValueError:
        return None
    return lon, lat


def _filter_subtree(parent, lat_min, lat_max, lon_min, lon_max, counts):
    """Drop placemarks outside the bbox from parent's children, recursing into
    folders. Empty folders are removed. Returns True if parent still contains
    any placemarks (directly or in nested folders) after filtering."""
    has_any = False
    for child in list(parent):
        tag = _local(child.tag)
        if tag == 'Placemark':
            coord = _placemark_coord(child)
            if coord is None:
                # No Point — leave it alone (e.g. unlikely, but be safe).
                has_any = True
                continue
            lon, lat = coord
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                has_any = True
                counts['kept'] += 1
            else:
                parent.remove(child)
                counts['dropped'] += 1
        elif tag in ('Folder', 'Document'):
            kept = _filter_subtree(child, lat_min, lat_max, lon_min, lon_max, counts)
            if kept:
                has_any = True
            else:
                # Don't drop the very top-level <Document>; just leave it empty.
                if tag == 'Folder':
                    parent.remove(child)
        # Other element types (Style, name, etc.) are kept untouched.
    return has_any


def bound(input_path, output_path, lat_min, lat_max, lon_min, lon_max):
    tree = ET.parse(input_path)
    root = tree.getroot()
    counts = {'kept': 0, 'dropped': 0}
    _filter_subtree(root, lat_min, lat_max, lon_min, lon_max, counts)

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    tree.write(output_path, xml_declaration=True, encoding='utf-8')
    print(
        f"Wrote {output_path}\n"
        f"  kept: {counts['kept']} placemarks, dropped: {counts['dropped']} (outside bbox)"
    )


def main():
    parser = argparse.ArgumentParser(
        description='Filter all_nav_points.kml to a lat/lon bounding box.'
    )
    parser.add_argument('lat_min', type=float, help='Minimum latitude')
    parser.add_argument('lat_max', type=float, help='Maximum latitude')
    parser.add_argument('lon_min', type=float, help='Minimum longitude')
    parser.add_argument('lon_max', type=float, help='Maximum longitude')
    parser.add_argument('--input', default=DEFAULT_INPUT,
                        help=f'Input KML (default: {DEFAULT_INPUT}).')
    parser.add_argument('--output', default=DEFAULT_OUTPUT,
                        help=f'Output KML (default: {DEFAULT_OUTPUT}).')
    args = parser.parse_args()

    if args.lat_min > args.lat_max:
        parser.error('lat_min must be <= lat_max')
    if args.lon_min > args.lon_max:
        parser.error('lon_min must be <= lon_max')

    bound(args.input, args.output, args.lat_min, args.lat_max, args.lon_min, args.lon_max)


if __name__ == '__main__':
    main()
