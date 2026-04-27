# FAA NASR → KML

This subdirectory turns the FAA's published navigation data into KML files that can be opened in Google Earth (or any other KML-aware viewer). The source data is the FAA Aeronautical Information Services [28-Day NASR Subscription](https://www.faa.gov/air_traffic/flight_info/aeronav/aero_data/NASR_Subscription/); the relevant CSV exports are kept in `latest_data/`. Field definitions for the CSVs are in the `NAV DATA LAYOUT.pdf` that ships with the NASR data.

## Inputs

The scripts read three CSV files under `latest_data/`. `APT_BASE.csv` contains airport records (one row per airfield, heliport, seaplane base, etc., with location, identifiers, and metadata). `FIX_BASE.csv` contains GPS fix records, each tagged with the chart series it appears on (low en-route, high en-route, SID, STAR, IAP, and so on). `NAV_BASE.csv` contains ground-based navaids — VORs, TACANs, VOR/DMEs, VORTACs, NDBs, etc. — along with their frequencies and altitude-class codes.

## Scripts and their outputs

All KML output lands in `kmls/`. Each script creates that directory if it doesn't already exist.

`navaid2kml.py` reads `NAV_BASE.csv`, filters for VOR-class navaids (`VOR`, `TACAN`, `VOR/DME`, `VORTAC`), and writes `kmls/vor_stations.kml`. The single output file contains two folders, "High Altitude VOR Stations" and "Low Altitude VOR Stations", split by the navaid's `ALT_CODE` (`H`/`VH` vs `L`/`VL`). All points use a yellow `placemark_circle.png` icon. The placemark name is the `NAV_ID` and the description includes altitude code, magnetic deviation, city/state, and frequency. There is no bounding-box argument — every qualifying navaid is included. A Jupyter notebook version, `parse_navbase.ipynb`, exists for interactive exploration and produces the same output.

`navfix2kml.py` reads `FIX_BASE.csv` and writes `kmls/gps_fixes.kml`. It accepts a bounding box on the command line (`lat_min lat_max lon_min lon_max`) and emits two folders, "GPS Fix High" and "GPS Fix Low", populated by matching rows whose `CHARTS` field contains `ENROUTE HIGH` or `ENROUTE LOW` respectively. All points use a blue `placemark_circle.png` icon. The placemark name is the `FIX_ID` and the description shows the chart list and state.

`airportbase2kml.py` reads `APT_BASE.csv` and writes `kmls/airport.kml`. It accepts the same bounding-box arguments. The output has two folders: "Airports with ICAO ID" (full-size red circles, named by `ICAO_ID`, with location in the description) and "Smaller Airports (no ICAO ID)" (the same red circle at scale 0.7, named by FAA `ARPT_ID`, with the airport name and location in the description). Splitting by ICAO ID keeps the larger fields visually prominent while still surfacing every record from the CSV — heliports, seaplane bases, and small public airfields included.

`airportfix2kml.py` reads `FIX_BASE.csv` and writes `kmls/approach_fixes.kml`. It accepts the bounding-box arguments and includes only fixes whose `CHARTS` field matches the regex `SID|STAR|IAP` — i.e., fixes used in standard instrument departures, standard terminal arrivals, and instrument approach procedures. All points use an orange `placemark_circle.png` icon. The placemark name is the `FIX_ID` and the description shows the chart list and state.

`combine_kmls.py` merges the four files above into a single `kmls/all_nav_points.kml`. Each source KML is wrapped as its own folder in the output so the original styling, names, and folder structure are preserved. Style IDs are namespaced per source (e.g. `airport_2`, `gps_fixes_4`) so duplicate IDs across the inputs don't cross-link styles after merging. The defaults read the four files produced by the other scripts, but `--inputs` and `--output` flags are available if you want to combine a different set or change the filename.

## Running everything

`gen_all_kmls.bash` runs the full pipeline end-to-end. It defines a single bounding box (currently set to the box that covers the TI3G3R2 and INSPYRE study areas — roughly latitude 25–62, longitude −140 to −66) and invokes each generator with that box, then runs the combiner. To regenerate every KML, run `bash gen_all_kmls.bash` from this directory. Adjust the four `minlat`/`maxlat`/`minlon`/`maxlon` variables at the top of the script to change the geographic extent. Note that `navaid2kml.py` does not take a bounding box and produces the same output regardless.

## Dependencies

The scripts use `pandas`, `numpy`, and `simplekml`; `combine_kmls.py` uses only the Python standard library. Install with `pip install pandas numpy simplekml` or ensure these packages are included in your conda environment.

## Output summary

After a full run with the default bounding box you'll find five files under `kmls/`: `vor_stations.kml` (yellow circles, ~760 navaids), `gps_fixes.kml` (blue circles, ~16k en-route fixes), `airport.kml` (red circles, ~18k airports split into ICAO and non-ICAO folders), `approach_fixes.kml` (orange circles, ~56k SID/STAR/IAP fixes), and `all_nav_points.kml`, the merged file containing all four as separate folders. Exact counts vary with the bounding box and with each NASR subscription update.
