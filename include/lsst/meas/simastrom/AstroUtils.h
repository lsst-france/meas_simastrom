// This may look like C code, but it is really -*- C++ -*-
#ifndef USNOUTILS__H
#define USNOUTILS__H

#include "lsst/meas/simastrom/BaseStar.h"
#include "lsst/meas/simastrom/Frame.h"
#include "lsst/meas/simastrom/Gtransfo.h" // for TanPix2RaDec
namespace lsst {
namespace meas {
namespace simastrom {

enum UsnoColor { RColor , BColor};

  class Frame;

//!This routine reads the USNO catalog stars within the given bounds.
/*! The x and y coordinates of the given stars refer to RA and DEC respectively
expressed in  degrees. The location of the catalog should be set by the user
in the USNODIR environment variable. The catalog contains both
R and B magnitude. The Color argument has to be RColor or BColor. 
WARNING : The flux of the returned BaseStar's is in fact a magnitude. */


  int UsnoRead(const Frame &F, UsnoColor Color, BaseStarList &ApmList);


  bool UsnoCollect(const Frame &usnoFrame, const TanPix2RaDec &Wcs, BaseStarList &UsnoCat);

  //! accepts both sexagesimal and decimal values.
  double RaStringToDeg(const std::string RaString);

  double DecStringToDeg(const std::string DecString);

  class Gtransfo;
  //! Transform a Frame through a Transfo.
  Frame ApplyTransfo(const Frame& inputframe,const Gtransfo &T, 
		     const WhichTransformed W);


}}} // end of namespaces

#endif /* USNOUTILS__H */
