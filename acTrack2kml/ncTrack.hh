#ifndef _ncTrack_hh_
#define _ncTrack_hh_

#include "AircraftTrack.hh"
#include "Config.hh"

class NcFile;
class NcVar;

/**
 * ncTrack provides an interface for loading an AircraftTrack from a netcdf
 * file.
 **/
class ncTrack
{
public:
  ncTrack();

  ~ncTrack();

  void
  setConfig(const Config& config)
  {
    cfg = config;
  }

  bool
  open(const std::string& filepath);

  void
  close();

  /**
   * Open the given netcdf file at @p ncpath, call fillAircraftTrack(),
   * then set the status on the track accordingly.
   **/
  void
  updateTrack(AircraftTrack& track, const std::string& ncpath);

private:

  void
  fillAircraftTrack(AircraftTrack& track);

  NcVar *
  getNetcdfVariable(const std::string& var_name);

  NcFile* nc;

  Config cfg;
};



#endif // _ncTrack_hh_
