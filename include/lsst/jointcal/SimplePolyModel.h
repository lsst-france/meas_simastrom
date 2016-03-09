#ifndef SIMPLEPOLYMODEL__H
#define SIMPLEPOLYMODEL__H

#include "memory"

#include "lsst/jointcal/Eigenstuff.h"

#include "lsst/jointcal/DistortionModel.h"
#include "lsst/jointcal/Gtransfo.h"
#include "lsst/jointcal/SimplePolyMapping.h"
#include "lsst/jointcal/Projectionhandler.h"
#include <map>

namespace lsst {
namespace jointcal {

class CcdImage;
class CcdImageList;

/* We deal here with coordinate transforms which are fitted
   and/or necessary to AstromFit. The classes SimplePolyModel 
and SimplePolyMapping implement a model where  there is one 
separate transfrom per CcdImage. One could chose other setups.

*/

//! this is the model used to fit independent CCDs, meaning that there is no instrument model.
/* This modeling of distortions can even accommodate images set mixing instruments */
class SimplePolyModel : public DistortionModel
{
  /* using ref counts here allows us to not write a destructor nor a copy
     constructor. I could *not* get it to work using std::auto_ptr. */
  typedef std::map<const CcdImage*, std::unique_ptr<SimpleGtransfoMapping> > mapType;
  mapType _myMap;
  const ProjectionHandler* _sky2TP;

public :

  //! Sky2TP is just a name, it can be anything
  SimplePolyModel(const CcdImageList &L, 
		  const ProjectionHandler* ProjH, 
		  bool InitFromWCS,
		  unsigned NNotFit=0,
          unsigned degree=3);

  // The following routines are the interface to AstromFit
  //!
  const Mapping* GetMapping(const CcdImage &) const;

  //! Positions the various parameter sets into the parameter vector, starting at FirstIndex
  unsigned AssignIndices(unsigned FirstIndex, std::string &WhatToFit);

  // dispaches the offsets after a fit step into the actual locations of parameters 
  void OffsetParams(const Eigen::VectorXd &Delta);
  
  /*! the mapping of sky coordinates (i.e. the coordinate system 
  in which fitted stars are reported) onto the Tangent plane
  (into which the pixel coordinates are transformed) */ 
  const Gtransfo* Sky2TP(const CcdImage &C) const
  { return _sky2TP->Sky2TP(C);}

  //! 
  virtual void FreezeErrorScales();

  //! Access to mappings
  const Gtransfo& GetTransfo(const CcdImage &Ccd) const;


  //! Cook up a SIP WCS.
  PTR(TanSipPix2RaDec) ProduceSipWcs(const CcdImage &Ccd) const;

  ~SimplePolyModel() {};

};

}} // end of namespaces

#endif /* SIMPLEPOLYMODEL__H */ 
