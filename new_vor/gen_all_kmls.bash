#!/bin/bash

# Bounding box for TI3G3R2 and INSPYRE
minlat=25
maxlat=62
minlon=-140
maxlon=-66
python airportbase2kml.py ${minlat} ${maxlat} ${minlon} ${maxlon}
python airportfix2kml.py ${minlat} ${maxlat} ${minlon} ${maxlon}
python navfix2kml.py ${minlat} ${maxlat} ${minlon} ${maxlon}
python navaid2kml.py
python combine_kmls.py
