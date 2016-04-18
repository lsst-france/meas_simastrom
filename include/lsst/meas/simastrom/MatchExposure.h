#ifndef LSST_MEAS_SIMASTROM_MATCHEXPOSURE_H
#define LSST_MEAS_SIMASTROM_MATCHEXPOSURE_H


#include "lsst/meas/simastrom/ExposureCatalog.h"
#include "lsst/meas/simastrom/ChipArrangement.h"

namespace lsst {
namespace meas {
namespace simastrom {
    
  class ExposureCatalog;
  class Point;
  struct SimAstromControl;

  //! Routine to astrometrically match a whole exposure at once, relying on a ChipArrangement
  bool MatchExposure(ExposureCatalog &EC, const Point &TangentPoint, const SimAstromControl &AstromControl);
    
}}}

#endif
