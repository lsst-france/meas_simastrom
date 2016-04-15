#ifndef EXPOSURECATALOG__H
#define EXPOSURECATALOG__H

#include <string>
#include <vector>

#include "lsst/meas/simastrom/ChipArrangement.h"
#include "lsst/meas/simastrom/Point.h"
#include "lsst/meas/simastrom/BaseStar.h"
#include "lsst/meas/simastrom/Frame.h"
//#include "lsst/meas/simastrom/StarList.h"
#include "lsst/afw/table/Source.h"

namespace lsst {
namespace meas {
namespace simastrom {


class Gtransfo;
class Frame;



//! just a container for both the coordinates in the tangent plane and the original measured object. 
class ExposureStar : public BaseStar
{
 public:
  int chip; // chip ID;
  const BaseStar *original; // the untransformed object (i.e. the object as read in the calexp catalog)

  //!
 ExposureStar(const BaseStar* S, const int Chip) : BaseStar(*S),  chip(Chip), original(S) {};

};


typedef StarList<ExposureStar> ExposureStarList;

//! Assembles a catalog (with coordinates in the tangent plane) from a multi-chip camera. See the comments at the end of tools/matchexposure.cc for the grand sceme.
class ExposureCatalog
{
  std::vector<int> chips;
  std::vector<BaseStarList> catalogs;
  const ChipArrangement* arrangement;

 public:
  //!
  ExposureCatalog(const ChipArrangement *A);

  //!
  void AddCalexp(const lsst::afw::table::SortedCatalogT<lsst::afw::table::SourceRecord> &Cat, const int Chip);

  //! Assembles the exposure catalog (coordinates in degrees in TP)
  void TangentPlaneCatalog(ExposureStarList &Catalog);

  //! the catalog (in pixel coordinates) of a single chip as read (and possibly selected).
  const BaseStarList *ChipCatalog(const int Chip) const;

  //! ChipArrangement mostly contains the mappings from pixels to tangent plane
  const ChipArrangement& Arrangement() const { return *arrangement;}

  //! in the order of the contructor arguments (and ImageNames()).
  const std::vector<int>& Chips() const {return chips;}

};

}}} // end of namespaces

#endif /* EXPOSURECATALOG__H */
