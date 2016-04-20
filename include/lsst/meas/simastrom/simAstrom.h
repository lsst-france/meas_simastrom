// -*- lsst-c++ -*-
#if !defined(LSST_MEAS_SIMASTROM_SIMASTROM_H)
#define LSST_MEAS_SIMASTROM_SIMASTROM_H

#include <cmath>
#include <string>
#include <vector>
#include <tuple>

#include "lsst/pex/config.h"
#include "lsst/afw/table/Source.h"
#include "lsst/afw/image/TanWcs.h"
#include "lsst/afw/image/Calib.h"
#include "lsst/afw/geom/Box.h"
#include "lsst/daf/base/PropertySet.h"

namespace lsst {
namespace meas {
namespace simastrom {
    
    struct SimAstromControl {
      LSST_CONTROL_FIELD(sourceFluxField, std::string, "name of flux field in source catalog");
      LSST_CONTROL_FIELD(centroid, std::string, "name of centroid in source catalog");
      LSST_CONTROL_FIELD(shape, std::string, "name of shape in source catalog");

      LSST_CONTROL_FIELD(linMatchCut, double, "max distance for collecting loose matches (arcsec)");
      LSST_CONTROL_FIELD(secondMatchCut, double, "max distance for collecting tight matches (arcsec)");

      LSST_CONTROL_FIELD(linMatchMinCount, int, "minimum number of matches to consider a match successfull");

      LSST_CONTROL_FIELD(distortionDegree, int, "polynomial degree used to describe distortions");

      LSST_CONTROL_FIELD(minMatchPerChip, int, "min number of matches per chip");


       SimAstromControl() :
      sourceFluxField("base_CircularApertureFlux_17_0"),centroid("base_SdssCentroid"),shape("base_SdssShape"), linMatchCut(1.5), secondMatchCut(1.), linMatchMinCount(10), distortionDegree(3), minMatchPerChip(5)
        {
            validate();
        }   
        void validate() const;

        ~SimAstromControl() {};
    };
    
class simAstrom {
public:
    
    simAstrom (
        std::vector<lsst::afw::table::SortedCatalogT< lsst::afw::table::SourceRecord> > const sourceList,
        std::vector<PTR(lsst::daf::base::PropertySet)> const metaList,
        std::vector<PTR(lsst::afw::image::TanWcs)> const wcsList,
        std::vector<lsst::afw::geom::Box2I> const bboxList,
        std::vector<std::string> const filterList,
        std::vector<PTR(lsst::afw::image::Calib)> const calibList,
        std::vector<int> const visitList,
        std::vector<int> const ccdList,
        std::vector<std::string> const cameraList,
        PTR(lsst::meas::simastrom::SimAstromControl) const control
    );
    
private:
    
    std::vector<lsst::afw::table::SortedCatalogT< lsst::afw::table::SourceRecord> > _sourceList;
    std::vector <boost::shared_ptr<lsst::daf::base::PropertySet> > _metaList;
    std::vector<PTR(lsst::afw::image::TanWcs)> _wcsList;
    std::vector<lsst::afw::geom::Box2I> _bboxList;
    std::vector<std::string> _filterList;
    std::vector<PTR(lsst::afw::image::Calib)> _calibList;
    std::vector<int> const _visitList;
    std::vector<int> const _ccdList;
    std::vector<std::string> const _cameraList;
};
    
}}}

#endif
