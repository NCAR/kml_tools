# README acTrack2kml

## Testing

There is a google test module, [test_track.cc](test_track.cc), and tests which
compare output with expected output files, both of which are run by the scons
alias 'test'.  There are also python tests, but they only run with the
'pytests' alias.

```shell
scons test
```

The tests are run with sanitized versions of `acTrack2kml` and `actrackx`, but
only the normal build of `acTrack2kml` is installed.

See [Image Comparison](#image-comparison) for information about generating
snapshot images from web browser renderings of the KML files.

### Generating KML image dumps

The flight_data web page and javascript code first had to be downloaded from
the web site.  Retrieve the full web page source with the substitutions for
the platform, and call that output `flight_data.html`:

```sh
wget --no-cookies --header "Cookie: platform=GV" http://www.eol.ucar.edu/cgi-bin/flight_data/osm_index.pl
```

Change the `osm.js` href in `flight_data.html` to point to a local copy.

### Running renderkml.py

The python script `renderkml.py` uses the javascript code to render a KML
flight track file over Open Street Maps, similar to how it's done for the
real-time web site.  It uses the python bindings for the
[selenium](https://www.selenium.dev/) WebDriver API.

The easiest way to setup the python requirements are with Conda or Mamba:

```shell
mamba install selenium selenium-manager
```

It is no longer necessary to use the PhantomJS browser.  Modern browsers
provide an API and headless operation, and `selenium-manager` knows how to
invoke their agents.

The script generates a special file, `flight_data/flight_data.js`, which
contains the list of kml files to render and the bounding box, then it uses
the selenium webdriver to load the `flight_data.html` web page into the
browser.  Because of security policies for cross-origin resource sharing
(CORS) in modern browsers, a browser cannot render flight_data.html and also
run the javascript when they are loaded directly from the filesystem.  So
testing setups must serve the files [through a local web
server](https://developer.mozilla.org/en-US/docs/Learn/Common_questions/Tools_and_setup/set_up_a_local_testing_server).
The `renderkml.py` script runs the simple http server built into python to
serve the local files.

A browser can also open `flight_data.html` to view the KML files
interactively, but it must also use a web server.  For example, to generate
`flight_data.js` for the combined winter flights and then browse the tracks:

```shell
scons winter
python -m http.server 8000
firefox http://localhost:8000/flight_data.html
```

Most of the javascript code is still pulled from the web, so `renderkml.py`
and firefox cannot render the page if not online.

### Image comparison

The image dumps are generated by the `render` alias rather than the basic
`test` target.

```shell
scons render
```

This alias updates all the KML test track files and then runs `renderkml.py`
to generate PNG image dumps.  It also creates an image comparison page
`tracks.html` for easily comparing the images side-by-side.  That page can be
viewed directly in a browser:

```shell
scons render
...
firefox tracks.html
```

## Monitoring

A basic check has already been implemented in the `acTrack2kml` program, and
that check is called by `nagios` to monitor the track service for each of the
usual aircraft.  The check compares the time of the latest track point in the
database and the output file mtime is used to see if the output is current.
That check detects problems connecting to the database and problems updating
the output files when there are track points in the database, but it does not
detect when the database is not being updated but should be.  That would have
to be a separate check.

The `position.json` file does not need to be limited by airspeed, it could
just always use the latest point.  Likewise the track can include the last 15
minutes or so of position data which precede the airspeed increase, without
becoming too large.  Or maybe the Track always has all the points, but then
the KML rendering uses a "View" on the track which limits it to the window
15-minutes before takeoff to 15-minutes after landing.

## Path algorithms

A TrackPath is a subset of points selected from an AircraftTrack by various
algorithms.  First of all a TrackPath has a clipping window, which can be
specified by time, index, or by a true airspeed threshold.  Only points within
the clipping window will ever be selected by the path algorithm.  Then
different algorithms can be used to filter points within the window:

- **timestep**: Pick only one point within each interval of a specified number
  of seconds.
- **headingstep**: Pick a point only once the heading differs by some
  threshold from the previous path point.
- **pointstep**: Pick one point for every pointstep points.

There are other algorithms for simplifying a path, namely the
Ramer-Douglas-Peucker algorithm.  That might be interesting to implement, and
unlike the heading and time step algorithms it can be used to generate a path
for varying resolutions.

- [Ramer–Douglas–Peucker_algorithm](http://en.wikipedia.org/wiki/Ramer%E2%80%93Douglas%E2%80%93Peucker_algorithm)
- [shortest-distance-between-a-point-and-a-line-segment](http://stackoverflow.com/questions/849211/shortest-distance-between-a-point-and-a-line-segment)
- [Paper on simplifying Ramer](http://www.cs.ubc.ca/cgi-bin/tr/1992/TR-92-07)

The whole point to picking a subset of the points is to optimize web displays
and cut down on unnecessary points (read: indistiguishable) in the KML track.

Consider how the headingstep path differs from a ramer-douglas-peucker path in
spirals.  If the spirals were smaller than the distance tolerance (ie, the
track resolution), then they would not be in the path at all, whereas the
heading step would still include them and require a lot of points to do it.

### Path statistics and comparisons

There are a few things in place to help compare KML tracks made by different
algorithms and settings, and to help verify that the code is still generating
reasonable tracks.

There is a color option to change the default yellow/red colors of a KML
track, so two tracks can be generated with different colors and rendered on
the same web map.

The `actrackx` program is a utility to generate two alternative tracks and
also report statistics about them:

- number of points in the whole track
- number of points in the path
- time span of points
- lat/lon coordinates of whole track

The number of path points can be compared between two paths to see which
settings trimmed more points.

An obvious question is whether the search for the optimum algorithm and
parameters can be automated.  Maybe paths can be generated with a binary
search until the target is met, but what's the target?  Max absolute number of
path points?  Minimum percent reduction?

The **headingstep** algorithm fails if `thdg` is not reliable.  A simple guard
against that would be to choose some large timestep interval and merge that
path with the headingstep path, so the timestep interval is like a timeout on
waiting for the heading to change.

Consider using a binary search to optimize automatically the thdg interval.
Set a goal for percent of points to include or maximum size, then find the
thdg interval which satisfies that goal.  Could even scale the search
according the ratio of the goal.  If one thdg interval produces twice as
many points as desired, then cut the thdg interval by half and try again.
Or maybe create a histogram of thdg changes, then pick the thdg interval at
the right cutoff in the histogram to include the desired number of points.
eg, if the goal is to cut by half the number of points, then choose the thdg
interval in the histogram where half the points have a lesser thdg change.
There are probably some library routines in gsl or something to pick medians
or quartiles or even build histograms.

The thdg delta between any two points should be small.  The algo doesn't
include a point until it differs by more than the interval, so we need to bin
the thdg itself, not the deltas.  If all the thdgs are in one bin, it
flatlined.  Usually they will be evenly distributed in the histogram.  So can
we find an optimal thdg interval from that?  The interval is some number of
bins, so the number of points that will be skipped (on average) is the average
number of points in that many bins.

In real-time mode, the thdg delta does not need to computed every time.  It
could be updated periodically as the number of points increases, and it
might need to start out with some default until enough points are collected
to do an analysis.

## Still to do

If tas_cutoff is set to zero, then the ramp location will fill up with
timestamp labels.  So the timestamp path can be clipped by tas, but then
add a point for the beginning and end.  It's that or somehow limiting
labels in space.  The beginning and end should be in opposite directions so
they aren't on top of each other on the ramp, or else don't label the
beginning, just the end.  Or maybe we shouldn't label the end, but only
label the last of the timestamps. ie, without tas cutoff, find 15-minute
path.  Then mask that path with inverse of tas cutoff, and the last point
will be the one on the 15-minute interval but just before takeoff.

The TAS clipping is still needed for the coordinates paths when the path
algorithm is not headingstep.

acTrack2kml should add some indicator about the timeliness of the track and
the aircraft position, ie, change the colors, change to an alert icon, or
maybe make the track red only for the last hour of clock time instead of
last hour of flight time (but only for real-time?)
