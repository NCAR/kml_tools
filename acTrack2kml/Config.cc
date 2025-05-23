

#include "Config.hh"
#include <stdlib.h>  // getenv()

#include <iostream>
#include <sstream>
#include <algorithm>
#include <iterator>

using std::cerr;
using std::endl;
using std::string;

// Output directories for .xml & .kml files.  Ground.
static const string grnd_flightDataDir = "/net/www/docs/flight_data";
static const string grnd_flightDataURL =
  // use relative urlpath to serve images from same host as the kml is served from,
  // mediates against unannounced and flaky host/cname changes,
  // allows catalog-maps to serve its own images
  "/flight_data";

  // OLDER: "http://www.eol.ucar.edu/flight_data";
  // OLD: "https://www.eol.ucar.edu/flight_data";
  // NO, NOT SUPPORTED, WILL DISAPPEAR: "https://archive.eol.ucar.edu/flight_data";
  // NEW: "https://field.eol.ucar.edu/flight_data";
  // NO, DON'T BE FOOLED: "https://flight.eol.ucar.edu/flight_data";

// Output directories for .xml & .kml files.  Onboard.
static const string onboard_flightDataDir = "/var/www/html/flight_data";
static const string onboard_flightDataURL =
  // use relative urlpath to serve images from same host as the kml is served from,
  // allows viewing via wired network hostnames like hyper.raf-guest.ucar.edu
  "/flight_data";
  // CANONICAL: "http://acserver.raf.ucar.edu/flight_data";

/**
 * KML's from netCDF files for post flight distribution need an absolute URL
 * for image files (e.g. wind barbs).
 */
static const string absolute_flightDataURL = "https://field.eol.ucar.edu/flight_data";


string
Config::
defaultGroundFlightDataURL()
{
  return grnd_flightDataURL;
}

string
Config::
defaultOnboardFlightDataURL()
{
  return onboard_flightDataURL;
}


Config::
Config() :
  TimeStep(15),
  HeadingStep(1.0),
  TimeBetweenFlights(12),
  TrackLength(0),	// 0 means all data.
  path_method("headingstep"),
  TAS_CutOff(20.0),
  ts_Freq(2000),
  barb_Freq(5),
  altMode("absolute"),
  compressKML(false),
  convertToFeet(1.0),
  onboard(false),
  verbose(0),
  showstats(false),
  update_interval_secs(30),
  position_interval_secs(3),
  run_once(false),
  check(false)
{
}


static const char* platform_names_array[] =
  {
    "GV",	// NCAR GV
    "C130",	// NCAR C130
    "N42RF",	// NOAA AOC P3 - Kermit
    "N43RF",	// NOAA AOC P3 - Miss Piggy
    "N46RF",	// NOAA Twin Otter
    "N49RF",	// NOAA AOC G4
    "DC8",	// NASA DC-8
    "WB57",	// NASA WB-57
    "GH",	// NASA Globalhawk
    "WKA",	// Wyoming King Air
    "B146",	// UK BAE146
    "LEAR",	// SPEC LEAR
    "CONVAIR",	// Canada
    "N762JT",	// 
    "VV256",	// NPS CIRPAS Twin Otter
    "DLR",	// DLR Falcon.  Keep for tests
    "WYSP"	// Wyoming Sprinter Van
  };


std::vector<std::string>
Config::
getPlatformNames()
{
  std::vector<std::string> names;
  const char** begin = platform_names_array;
  const char** end = begin +
    sizeof(platform_names_array)/sizeof(platform_names_array[0]);
  std::copy(begin, end, std::back_inserter(names));
  return names;
}


bool
Config::
setPlatform(const std::string& platname)
{
  std::vector<std::string> names = getPlatformNames();

  std::vector<std::string>::iterator it =
    std::find(names.begin(), names.end(), platname);

  if (it != names.end())
  {
    platform = platname;
    return true;
  }
  else
  {
    cerr << "\n\tplatform must be: ";
    std::ostream_iterator<std::string> out_it(cerr, ", ");
    std::copy(names.begin(), names.end(), out_it);
    cerr << "\n\n";
  }
  return false;
}


bool
Config::
realtimeMode()
{
  // We are in 'real-time mode' if connecting to a database and runonce is
  // disabled.
  return netCDFinputFile.empty() and !run_once;
}


/// Set @p parameter to @p dfault if @p parameter is empty.
static void
set_default(std::string& parameter, const std::string& dfault)
{
  if (parameter.empty())
  {
    parameter = dfault;
  }
}


void
Config::
fillDefaults()
{
  Config &cfg = *this;

  if (! cfg.netCDFinputFile.empty())
  {
    set_default(cfg.flightDataURL, absolute_flightDataURL);

    // This is not real-time, so there is no more real-time setup.
  }
  else if (cfg.onboard)
  {
    // Derive the database name according to the platform setting.
    dbname = "real-time";
    set_default(cfg.flightDataURL, onboard_flightDataURL);

    // It's possible to run onboard but for a platform other than the host
    // platform.  So if platform is set, it implies using the
    // platform-specific forms of database name and GE path.
    if (cfg.flightDataDir.empty())
    {
      if (cfg.platform.empty())
      {
	cfg.flightDataDir = onboard_flightDataDir;
      }
      else
      {
	cfg.flightDataDir = onboard_flightDataDir + "/" + cfg.platform;
      }
    }
    // If platform is set, then use the platform-specific database name and
    // pull the track points from the database server on the ground.
    if (! cfg.platform.empty())
    {
      cfg.dbname = "real-time-" + cfg.platform;

      // On the plane PGHOST is always set, so we must preempt it to pull
      // from the ground database.
      set_default(cfg.database_host, "eol-rt-data.eol.ucar.edu");
    }
    else
    {
      // We're onboard with no platform set, so the default is the
      // local server database.
      set_default(cfg.database_host, "localhost");
    }
  }
  else if (cfg.platform.length() > 0)
  {
    // Real-time on the ground.
    cfg.dbname = "real-time-" + cfg.platform;
    set_default(cfg.flightDataDir, grnd_flightDataDir + "/" + cfg.platform);
  }

  // If the flight_data URL still hasn't been set, then it defaults to
  // the ground web site.
  set_default(cfg.flightDataURL, defaultGroundFlightDataURL());

  // If the output prefix is provided, it overrides the output file paths
  // generated by default for the real-time case below.
  if (cfg.outputPrefix.size())
  {
    cfg.outputKML = cfg.outputPrefix + "real-time.kml";
    cfg.outputAnimatedKML = cfg.outputPrefix + "animated-track.kml";
    cfg.outputPositionKML = cfg.outputPrefix + "current_pos.kml";
    cfg.outputPositionJSON = cfg.outputPrefix + "position.json";
  }

  // If not using netcdf input, then output goes to the "real-time"
  // destination directories by default, and it gets compressed.
  if (cfg.netCDFinputFile.empty())
  {
    cfg.compressKML = true;

    set_default(cfg.outputKML, cfg.flightDataDir + "/GE/real-time.kml");
    set_default(cfg.outputAnimatedKML,
		cfg.flightDataDir + "/GE/animated-track.kml");
    set_default(cfg.outputPositionKML,
		cfg.flightDataDir + "/GE/current_pos.kml");
    set_default(cfg.outputPositionJSON, cfg.flightDataDir + "/position.json");
  }
}


/*
 * The acTrack2kml code has always opened the postgresql database
 * connection with a connection string in this form:
 *
 *    sprintf(conn_str, "host='%s' dbname='%s' user ='ads'",
 *	    cfg.database_host.c_str(), cfg.dbname.c_str());
 *
 * Even though it looks like the host is being specified explicitly, in
 * fact the psql library will accept an empty host name and then default to
 * 'localhost'.  So it is possible to connect to the real-time database on
 * the aircraft server without setting PGHOST and without setting the host
 * on the command line.  This is how it worked for a long time, since the
 * PGHOST and other environment settings were not actually being passed to
 * the acTrack2kml process when it was started by cron.  Is it better to
 * set an explicit default of 'localhost' in the Config class, or allow
 * database_host to be empty in the psql connection string when in "onboard
 * real-time mode"?  In light of confusion about why the PGHOST setting was
 * not working for cron processes, the Config code now sets 'localhost' as
 * the explicit default, but it also allows the database_host setting to be
 * empty when in onboard real-time mode.
 */
bool
Config::
verifyDatabaseHost()
{
  if (database_host.empty())
  {
    // It is not strictly necessary to copy PGHOST into database_host,
    // since the psql library will use PGHOST if the host specifier in the
    // connect string is empty.  However, this allows the database host to
    // be logged, and it means database_host must be non-empty in modes
    // where a database is required.
    char *p = getenv("PGHOST");
    if (p)
    {
      database_host = p;
    }
  }
  return !database_host.empty() || (onboard && platform.empty());
}


std::string
Config::
dump()
{
  std::ostringstream out;
  out << "       flight_data dir: " << flightDataDir << "\n";
  out << " google earth data dir: " << flightDataDir + "/GE" << "\n";
  out << "       flight_data URL: " << flightDataURL << "\n";
  out << "    Platform selection: " << platform << "\n";
  out << "          Onboard mode: " << onboard << "\n";
  out << "    KML updates (secs): " << update_interval_secs << "\n";
  out << "   JSON updates (secs): " << position_interval_secs << "\n";
  out << "   path algorithm spec: " << path_method << "\n";
  out << "      Time step (secs): " << TimeStep << "\n";
  out << "    Heading step (deg): " << HeadingStep << "\n";
  out << "    Flight gap (hours): " << TimeBetweenFlights << "\n";
  out << "Track Length (minutes): " << TrackLength << "\n";
  out << "            TAS cutoff: " << TAS_CutOff << "\n";
  out << " Time stamps (minutes): " << ts_Freq << "\n";
  out << "  Wind Barbs (minutes): " << barb_Freq << "\n";
  out << "     KML altitude mode: " << altMode << "\n";
  out << "       KML output file: " << outputKML << "\n";
  out << "          Compress KML: " << (compressKML ? "true" : "false") << "\n";
  out << "       KML track color: " << color << "\n";
  out << "    JSON position file: " << outputPositionJSON << "\n";
  out << "       netCDFinputFile: " << netCDFinputFile << "\n";
  out << "         Database host: " << database_host << "\n";
  out << "         Database name: " << dbname << "\n";
  out << "         Verbose level: " << verbose << "\n";
  out << " lat/lon/alt overrides: "
      << latVariable << "/" << lonVariable << "/" << altVariable << "\n";
  return out.str();
}



void
Config::
setAltitudeUnits(const string& units)
{
  convertToFeet = 1.0;
  if (units == "m")
  {
    convertToFeet = 3.2808; // feet per meter
  }
  if (verbose)
  {
    cerr << "cfg.alt: " << altVariable
	 << " units: " << units << endl;
    cerr << "cfg.convertToFeet: " << convertToFeet << endl;
  }
}


std::string
Config::
getLatitudeVariable(const std::string& sourcename)
{
  if (latVariable.empty())
  {
    latVariable = sourcename;
  }
  return latVariable;
}

std::string
Config::
getLongitudeVariable(const std::string& sourcename)
{
  if (lonVariable.empty())
  {
    lonVariable = sourcename;
  }
  return lonVariable;
}

std::string
Config::
getAltitudeVariable(const std::string& sourcename)
{
  if (altVariable.empty())
  {
    altVariable = sourcename;
  }
  return altVariable;
}
