from __future__ import division, absolute_import
#
# LSST Data Management System
# Copyright 2008, 2009, 2010, 2011, 2012 LSST Corporation.
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
#

import numpy as np

import lsst.pex.config as pexConfig
import lsst.coadd.utils as coaddUtils
import lsst.pipe.base as pipeBase
import lsst.afw.image as afwImage
import lsst.afw.table as afwTable

from lsst.afw.fits import FitsError
from lsst.pipe.tasks.selectImages import WcsSelectImagesTask, SelectStruct
from lsst.coadd.utils import CoaddDataIdContainer
from lsst.pipe.tasks.getRepositoryData import DataRefListRunner

from .simastromLib import test, test2, simAstrom, SimAstromControl

__all__ = ["SimAstromConfig", "SimAstromTask"]

class SimAstromConfig(pexConfig.Config):
    """Config for SimAstromTask
    """

# Keep this config parameter as a place holder
    doWrite = pexConfig.Field(
        doc = "persist SimAstrom output...",
        dtype = bool,
        default = True,
    )
    
    sourceFluxField = pexConfig.Field(
        doc = "Type of source flux",
        dtype = str,
        default = "base_CircularApertureFlux_5",   # base_CircularApertureFlux_17_0 in recent stack version 
    )
    centroid = pexConfig.Field(
        doc = "Centroid type for position estimation",
        dtype = str,
        default = "base_SdssCentroid", 
    )
    shape = pexConfig.Field(
        doc = "Shape for error estimation",
        dtype = str,
        default = "base_SdssShape", 
    )
class SimAstromTask(pipeBase.CmdLineTask):
 
    ConfigClass = SimAstromConfig
    RunnerClass = DataRefListRunner
    _DefaultName = "simAstrom"
    
    def __init__(self, *args, **kwargs):
        pipeBase.Task.__init__(self, *args, **kwargs)
#        self.makeSubtask("select")

# We don't need to persist config and metadata at this stage. In this way, we don't need to put a specific entry in the
# camera mapper policy file
    def _getConfigName(self):
        return None
        
    def _getMetadataName(self):
        return None
        
    @classmethod
    def _makeArgumentParser(cls):
        """Create an argument parser
        """
        parser = pipeBase.ArgumentParser(name=cls._DefaultName)

        parser.add_id_argument("--id", "calexp", help="data ID, e.g. --selectId visit=6789 ccd=0..9")
        return parser

    @pipeBase.timeMethod
    def run(self, ref):
        
#        sourceCat = test2()
        
        srcList = []
        metaList = []
        wcsList = []
        bboxList = []
        filterList = []
        calibList = []
        visitList = []
        ccdList = []
        cameraList = []
        
        configSel = StarSelectorConfig()
        ss = StarSelector(configSel, self.config.sourceFluxField, self.config.centroid, self.config.shape)
        
        print self.config.sourceFluxField
        astromControl = SimAstromControl()
        astromControl.sourceFluxField = self.config.sourceFluxField
        astromControl.centroid = self.config.centroid
        astromControl.shape = self.config.shape

        for dataRef in ref :
            src = dataRef.get("src", immediate=True)
            calexp = dataRef.get("calexp", immediate=True)
            tanwcs = afwImage.TanWcs.cast(calexp.getWcs())
            bbox = calexp.getBBox()
            md = dataRef.get("calexp_md", immediate=True)
            calib = afwImage.Calib(md)
            filt = calexp.getFilter().getName()
            
            newSrc = ss.select(src, calib)
            if len(newSrc) == 0 :
                print "no source selected in ", dataRef.dataId["visit"], dataRef.dataId["ccd"]
                continue
            print "%d sources selected in visit %d - ccd %d"%(len(newSrc), dataRef.dataId["visit"], dataRef.dataId["ccd"])
            
        # Should call a source selector here in order to send a list
        # of reasonable star to the fitter.
            srcList.append(newSrc)
            
            metaList.append(md)
            wcsList.append(tanwcs)
            bboxList.append(bbox)
            filterList.append(filt)
            calibList.append(calib)
            visitList.append(dataRef.dataId['visit'])
            ccdList.append(dataRef.dataId['ccd'])
            cameraList.append(dataRef.getButler().mapper.getCameraName())
            
        simA = simAstrom(srcList, metaList, wcsList, bboxList, filterList, calibList, visitList, ccdList, cameraList, astromControl)

class StarSelectorConfig(pexConfig.Config):
    
    badFlags = pexConfig.ListField(
        doc = "List of flags which cause a source to be rejected as bad",
        dtype = str,
        default = [ "base_PixelFlags_flag_saturated", 
                    "base_PixelFlags_flag_cr",
                    "base_PixelFlags_flag_interpolated",
                    "base_SdssCentroid_flag",
                    "base_SdssShape_flag"],
    )

class StarSelector(object) :
    
    ConfigClass = StarSelectorConfig

    def __init__(self, config, sourceFluxField, centroid, shape):
        """Construct a star selector
        
        @param[in] config: An instance of StarSelectorConfig
        """
        self.config = config
        self.sourceFluxField = sourceFluxField
        self.centroid=centroid
        self.shape=shape


    def select(self, srcCat, calib):
# Return a catalog containing only reasonnable stars

        schema = srcCat.getSchema()
        newCat = afwTable.SourceCatalog(schema)
        fluxKey = schema[self.sourceFluxField+"_flux"].asKey()
        fluxErrKey = schema[self.sourceFluxField+"_fluxSigma"].asKey()
        parentKey = schema["parent"].asKey()
        flagKeys = []
        for f in self.config.badFlags :
            key = schema[f].asKey()
            flagKeys.append(key)
        fluxFlagKey = schema[self.sourceFluxField+"_flag"].asKey()
        flagKeys.append(fluxFlagKey)
        
        for src in srcCat :
            # Reject galaxies
#            if src.get("base_ClassificationExtendedness_value") > 0.5 :
#                continue
            # Do not consider sources with bad flags
            for f in flagKeys :
                rej = 0
                if src.get(f) :
                    rej = 1
                    break
            if rej == 1 :
                continue
            # Reject negative flux
            flux = src.get(fluxKey)
            if flux < 0 :
                continue
            # Reject objects with too large magnitude
            fluxErr = src.get(fluxErrKey)
            mag, magErr = calib.getMagnitude(flux, fluxErr)
            if mag > 22.5 or magErr > 0.1 or flux/fluxErr < 10 :
                continue
            # Reject blends
            if src.get(parentKey) != 0 :
                continue
            footprint = src.getFootprint()
            if footprint is not None and len(footprint.getPeaks()) > 1 :
                continue
            
            vx = np.square(src.get(self.centroid + "_xSigma"))
            vy = np.square(src.get(self.centroid + "_ySigma"))
            mxx = src.get(self.shape + "_xx")  
            myy = src.get(self.shape + "_yy")
            mxy = src.get(self.shape + "_xy") 
            vxy = mxy*(vx+vy)/(mxx+myy);

            if vx < 0 or vy< 0 or (vxy*vxy)>(vx*vy) or np.isnan(vx) or np.isnan(vy):
                continue
            
            newCat.append(src)
            
#        print len(srcCat), len(newCat)
        
        return newCat
