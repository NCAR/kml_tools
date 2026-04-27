# FAA NASR → KML

This subdirectory turns the FAA's published navigation data into KML files that can be opened in Google Earth (or any other KML-aware viewer). The source data is the FAA Aeronautical Information Services [28-Day NASR Subscription](https://www.faa.gov/air_traffic/flight_info/aeronav/aero_data/NASR_Subscription/); the relevant CSV data sets are downloaded periodically and kept in `latest_data/`. Field definitions for the CSVs are in the `NAV DATA LAYOUT.pdf` that ships with the NASR data.

## Inputs

The scripts read three CSV files under `latest_data/`. `APT_BASE.csv` contains airport records (one row per airfield, heliport, seaplane base, etc., with location, identifiers, and metadata). `FIX_BASE.csv` contains GPS fix records, each tagged with the chart series it appears on (low en-route, high en-route, SID, STAR, IAP, and so on). `NAV_BASE.csv` contains ground-based navaids — VORs, TACANs, VOR/DMEs, VORTACs, NDBs, etc. — along with their frequencies and altitude-class codes.

## Scripts and their outputs

All KML output lands in `kmls/`. Each script creates that directory if it doesn't already exist.

`navaid2kml.py` reads `NAV_BASE.csv`, filters for VOR-class navaids (`VOR`, `TACAN`, `VOR/DME`, `VORTAC`), and writes `kmls/vor_stations.kml`. The single output file contains two folders, "High Altitude VOR Stations" and "Low Altitude VOR Stations", split by the navaid's `ALT_CODE` (`H`/`VH` vs `L`/`VL`). All points use a yellow `placemark_circle.png` icon. The placemark name is the `NAV_ID` and the description includes altitude code, magnetic deviation, city/state, and frequency.

`gpsfix2kml.py` reads `FIX_BASE.csv` and writes `kmls/gps_fixes.kml`. It emits three folders: "Approach Fixes (SID/STAR/IAP)", "High Altitude En-Route Fixes", and "Low Altitude En-Route Fixes". All three use the same blue `placemark_circle.png` icon; the folders themselves are how the categories stay distinguishable (and individually toggleable in Google Earth). The same fix often appears in multiple chart series — for example, SPAMY's `CHARTS` field is `CONTROLLER,ENROUTE HIGH,ENROUTE LOW,STAR` — so each fix is classified into exactly one folder using the priority order Approach > High > Low to avoid duplicate placemarks. The full chart list is preserved in the description so the other contexts a fix is used in remain visible when the placemark is clicked. The placemark name is the `FIX_ID`. This script replaces the older `navfix2kml.py` and `airportfix2kml.py`, which produced two separate KMLs with overlapping fixes.

`airportbase2kml.py` reads `APT_BASE.csv` and writes `kmls/airport.kml`. The output has two folders: "Airports with ICAO ID" (full-size red circles, named by `ICAO_ID`, with location in the description) and "Smaller Airports (no ICAO ID)" (the same red circle at scale 0.7, named by FAA `ARPT_ID`, with the airport name and location in the description).

`combine_kmls.py` merges the three files above into a single `kmls/all_nav_points.kml`. The defaults read the three files produced by the other scripts, but `--inputs` and `--output` flags are available if you want to combine a different set or change the filename.


## Generating all KMLs

`gen_all_kmls.bash` runs the full pipeline end-to-end: it invokes each generator and then the combiner. To regenerate every KML, run `bash gen_all_kmls.bash` from this directory. None of the generators filter geographically — every point in the source CSVs ends up in the output.

## KML Bounding

`bound_kml.py` takes a lat/lon bounding box as input, reads in `kmls/all_nav_points.kml`, and outputs a bounded kml file
that only includes placemarkers within the bounding box. Useful if the area of interest is small and a smaller kml file
is needed for the application using it.

## Dependencies

The scripts use `pandas`, `numpy`, and `simplekml`; `combine_kmls.py` uses only the Python standard library. Install with `pip install pandas numpy simplekml` or ensure these packages are included in your conda environment.

## Output summary

After a full run you'll find four files under `kmls/`: `vor_stations.kml` (every VOR-class navaid in the dataset), `gps_fixes.kml` (every fix in `FIX_BASE.csv`, split into approach/high/low folders with each fix appearing in exactly one), `airport.kml` (every airport in `APT_BASE.csv`, split into ICAO and non-ICAO folders), `all_nav_points.kml`, the merged file containing all three as separate folders, and `all_nav_points_bounded.kml` if the `bound_kml.py` script was used.
