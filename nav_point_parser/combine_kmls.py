"""Combine multiple KML files into a single all_nav_points.kml.

Each source KML's <Document> is wrapped in a <Folder> in the combined file so
its points stay grouped and its document-level name is preserved as the folder
name. Style IDs (and matching <styleUrl> references) are namespaced per source
file so duplicate IDs across the inputs don't cause points to pick up the wrong
style after merging.

Default inputs are the four KMLs produced by the other scripts in this folder:
    vor_stations.kml, gps_fixes.kml, airport.kml, approach_fixes.kml
Output defaults to all_nav_points.kml.
"""
import argparse
import os
import re
import xml.etree.ElementTree as ET

KML_NS = 'http://www.opengis.net/kml/2.2'
ET.register_namespace('', KML_NS)

KML_OUTPUT_DIR = 'kmls'


def _kml(tag):
    return f'{{{KML_NS}}}{tag}'


def _local(tag):
    return tag.split('}', 1)[-1] if '}' in tag else tag


def _prefix_ids(elem, prefix):
    """Rewrite every id="X" attribute and every <styleUrl>#X</styleUrl> in the
    subtree to use the given prefix, so this source's IDs don't collide with
    those from other source files in the merged document."""
    for node in elem.iter():
        if 'id' in node.attrib:
            node.attrib['id'] = f'{prefix}_{node.attrib["id"]}'
        if _local(node.tag) == 'styleUrl' and node.text:
            t = node.text.strip()
            if t.startswith('#'):
                node.text = f'#{prefix}_{t[1:]}'


def _safe_prefix(path):
    """Build a short, safe id prefix from a filename."""
    base = os.path.splitext(os.path.basename(path))[0]
    return re.sub(r'[^A-Za-z0-9_]', '_', base) or 'src'


def combine(source_files, output_path, document_name='All Nav Points'):
    kml_root = ET.Element(_kml('kml'))
    out_doc = ET.SubElement(kml_root, _kml('Document'))
    ET.SubElement(out_doc, _kml('name')).text = document_name

    for path in source_files:
        if not os.path.exists(path):
            print(f"Warning: {path} not found, skipping.")
            continue

        tree = ET.parse(path)
        root = tree.getroot()
        src_doc = root.find(_kml('Document'))
        if src_doc is None:
            src_doc = root  # tolerate KMLs without a wrapping <Document>

        prefix = _safe_prefix(path)
        _prefix_ids(src_doc, prefix)

        # Use the source Document's own <name> as the folder name when present.
        src_name_elem = src_doc.find(_kml('name'))
        folder_name = (src_name_elem.text or '').strip() if src_name_elem is not None else ''
        if not folder_name:
            folder_name = os.path.splitext(os.path.basename(path))[0]

        folder = ET.SubElement(out_doc, _kml('Folder'))
        ET.SubElement(folder, _kml('name')).text = folder_name

        # Move every child of the source Document into the new folder, except
        # its <name> (already handled above).
        for child in list(src_doc):
            if _local(child.tag) == 'name':
                continue
            folder.append(child)

        print(f"Added {path} as folder '{folder_name}' (prefix '{prefix}_').")

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    ET.ElementTree(kml_root).write(output_path, xml_declaration=True, encoding='utf-8')
    print(f"Wrote {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Combine multiple KML files into a single all_nav_points.kml.'
    )
    default_inputs = [
        os.path.join(KML_OUTPUT_DIR, name)
        for name in ('vor_stations.kml', 'gps_fixes.kml', 'airport.kml')
    ]
    default_output = os.path.join(KML_OUTPUT_DIR, 'all_nav_points.kml')
    parser.add_argument(
        '--inputs', nargs='+',
        default=default_inputs,
        help='Input KML files (default: the four files produced by the other scripts in kmls/).',
    )
    parser.add_argument('--output', default=default_output,
                        help='Output combined KML filename (default: kmls/all_nav_points.kml).')
    parser.add_argument('--name', default='All Nav Points',
                        help='Top-level <Document> name for the combined KML.')
    args = parser.parse_args()
    combine(args.inputs, args.output, document_name=args.name)


if __name__ == '__main__':
    main()
