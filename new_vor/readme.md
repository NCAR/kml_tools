# New VOR Parser designed to parse the csv file from the FAA Aeronautical Information Services: [28 Day NASR Subscription](https://www.faa.gov/air_traffic/flight_info/aeronav/aero_data/NASR_Subscription/). Find more information about fields in the NAV DATA LAYOUT.pdf accompanying the data.

navfix2kml.py outputs two kml files for the specified bounds of the GPS Fix bases. One file (low_fix.kml) is for the Low Enroute charts and the other is for the High Enroute charts (high_fix.kml).

parse_file.ipynb outputs the low and high altitude VOR stations. This outputs every VOR stations currently available in two files: low and high.