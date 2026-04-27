#!/bin/bash

python airportbase2kml.py
python gpsfix2kml.py
python navaid2kml.py
python combine_kmls.py
