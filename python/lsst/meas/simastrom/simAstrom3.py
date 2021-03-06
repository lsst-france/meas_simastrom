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

import os
import numpy as np

import lsst.utils
import lsst.pex.config as pexConfig
import lsst.coadd.utils as coaddUtils
import lsst.pipe.base as pipeBase
import lsst.afw.image as afwImage
import lsst.afw.table as afwTable
import lsst.afw.geom as afwGeom
import lsst.afw.coord as afwCoord
import lsst.pex.exceptions as pexExceptions

from lsst.afw.fits import FitsError
from lsst.pipe.tasks.selectImages import WcsSelectImagesTask, SelectStruct
from lsst.coadd.utils import CoaddDataIdContainer
from lsst.pipe.tasks.getRepositoryData import DataRefListRunner
from lsst.meas.astrom.loadAstrometryNetObjects import LoadAstrometryNetObjectsTask
from lsst.meas.astrom import AstrometryNetDataConfig

from .dataIds import PerTractCcdDataIdContainer

from lsst.meas.simastrom.simastromLib import SimAstromControl, simAstrom, Associations, ProjectionHandler , AstromFit, SimplePolyModel, OneTPPerShoot, CcdImage, GtransfoToTanWcs

__all__ = ["SimAstromConfig", "SimAstromTask"]

class SimAstromRunner(pipeBase.TaskRunner):
    """Subclass of TaskRunner for SimAstromTask (copied from the HSC MosaicRunner)

    SimAstromTask.run() takes a number of arguments, one of which is a list of dataRefs
    extracted from the command line (whereas most CmdLineTasks' run methods take
    single dataRef, are are called repeatedly).  This class transforms the processed
    arguments generated by the ArgumentParser into the arguments expected by
    MosaicTask.run().

    See pipeBase.TaskRunner for more information, but note that the multiprocessing
    code path does not apply, because MosaicTask.canMultiprocess == False.
    """

    @staticmethod
    def getTargetList(parsedCmd, **kwargs):
        # organize data IDs by tract
        refListDict = {}
        for ref in parsedCmd.id.refList:
            refListDict.setdefault(ref.dataId["tract"], []).append(ref)
        # we call run() once with each tract
        return [(refListDict[tract],
                 tract
                 ) for tract in sorted(refListDict.keys())]

    def __call__(self, args):
        task = self.TaskClass(config=self.config, log=self.log)
        result = task.run(*args)


class SimAstromConfig(pexConfig.Config):
    """Config for SimAstromTask
    """

# Keep this config parameter as a place holder
    doWrite = pexConfig.Field(
        doc = "persist SimAstrom output...",
        dtype = bool,
        default = True,
    )
    posError = pexConfig.Field(
        doc = "Constant term for error on position (in pixel unit)",
        dtype = float,
        default = 0.02, 
    )
    polyOrder = pexConfig.Field(
        doc = "Polynomial order for fitting distorsion",
        dtype = int,
        default = 3,
    )
    sourceFluxField = pexConfig.Field(
        doc = "Type of source flux",
        dtype = str,
        default = "base_CircularApertureFlux_17_0",   # base_CircularApertureFlux_17_0 in recent stack version 
    )
    maxMag = pexConfig.Field(
        doc = "Maximum magnitude for sources to be included in the fit",
        dtype = float,
        default = 22.5, 
    )
    coaddName = pexConfig.Field(
        doc = "Mandatory for getSkymap",
        dtype = str,
        default = "deep",
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
    RunnerClass = SimAstromRunner
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

        parser.add_id_argument("--id", "calexp", help="data ID, e.g. --selectId visit=6789 ccd=0..9",
                                ContainerClass=PerTractCcdDataIdContainer)
        return parser

    @pipeBase.timeMethod
    def run(self, ref, tract):
        
        configSel = StarSelectorConfig()
        ss = StarSelector(configSel, self.config.sourceFluxField, self.config.maxMag,self.config.centroid,self.config.shape)
        
        print self.config.sourceFluxField,self.config.shape
        astromControl = SimAstromControl()
        astromControl.sourceFluxField = self.config.sourceFluxField
        astromControl.centroid = self.config.centroid
        astromControl.shape = self.config.shape
        

        assoc = Associations()
        
#        for dataRef in ref :
#            print dataRef.dataId
#            print dataRef.dataId["tract"]
#            print dataRef
#            print dir(dataRef)
            
#        return    
        
        for dataRef in ref :
            
            print dataRef.dataId
            
            src = dataRef.get("src", immediate=True)
            md = dataRef.get("calexp_md", immediate=True)
            tanwcs = afwImage.TanWcs.cast(afwImage.makeWcs(md))
            lLeft = afwImage.getImageXY0FromMetadata(afwImage.wcsNameForXY0, md)
            uRight  = afwGeom.Point2I(lLeft.getX() + md.get("NAXIS1")-1, lLeft.getY() + md.get("NAXIS2")-1)
            bbox = afwGeom.Box2I(lLeft, uRight)
            calib = afwImage.Calib(md)
            filt = dataRef.dataId['filter']
            
            newSrc = ss.select(src, calib)
            if len(newSrc) == 0 :
                print "no source selected in ", dataRef.dataId["visit"], dataRef.dataId["ccd"]
                continue
            print "%d sources selected in visit %d - ccd %d"%(len(newSrc), dataRef.dataId["visit"], dataRef.dataId["ccd"])
            
            assoc.AddImage(newSrc, tanwcs, md, bbox, filt, calib,
                           dataRef.dataId['visit'], dataRef.dataId['ccd'],
                           dataRef.getButler().mapper.getCameraName(), 
                           astromControl)
        
        matchCut = 3.0
        assoc.AssociateCatalogs(matchCut)
        
        # Use external reference catalogs handled by LSST stack mechanism
        # Get the bounding box overlapping all associated images
        # ==> This is probably a bad idea to do it this way <== To be improved
        bbox = assoc.GetRaDecBBox()
        center = afwCoord.Coord(bbox.getCenter(), afwGeom.degrees)
        corner = afwCoord.Coord(bbox.getMax(), afwGeom.degrees)
        radius = center.angularSeparation(corner).asRadians()
        
        # Get astrometry_net_data path
        anDir = lsst.utils.getPackageDir('astrometry_net_data')
        if anDir is None:
            raise RuntimeError("astrometry_net_data is not setup")

        andConfig = AstrometryNetDataConfig()
        andConfigPath = os.path.join(anDir, "andConfig.py")
        if not os.path.exists(andConfigPath):
            raise RuntimeError("astrometry_net_data config file \"%s\" required but not found" %andConfigPath)
        andConfig.load(andConfigPath)
        
        task = LoadAstrometryNetObjectsTask.ConfigClass()
        loader = LoadAstrometryNetObjectsTask(task)
        
        # Determine default filter associated to the catalog
        filt, mfilt = andConfig.magColumnMap.items()[0]
        print "Using", filt, "band for reference flux"

        refCat = loader.loadSkyCircle(center, afwGeom.Angle(radius, afwGeom.radians), filt).refCat
        #print refCat.getSchema().getOrderedNames()
        
        # assoc.CollectRefStars(False) # To use USNO-A catalog 

        assoc.CollectLSSTRefStars(refCat, filt)
        assoc.SelectFittedStars()
        assoc.DeprojectFittedStars() # required for AstromFit
        sky2TP = OneTPPerShoot(assoc.TheCcdImageList())
        spm = SimplePolyModel(assoc.TheCcdImageList(), sky2TP, True, 0, self.config.polyOrder)

        fit = AstromFit(assoc, spm, self.config.posError)
        fit.Minimize("Distortions")
        chi2 = fit.ComputeChi2()
        print chi2
        fit.Minimize("Positions")
        chi2 = fit.ComputeChi2()
        print chi2
        fit.Minimize("Distortions Positions")
        chi2 = fit.ComputeChi2()
        print chi2

        for i in range(20) :
            r = fit.Minimize("Distortions Positions",5) # outliers removal at 5 sigma.
            chi2 = fit.ComputeChi2()
            print chi2
            if r == 0 :
                print "fit has converged - no more outliers"
                break
            elif r == 2 :
                print "minimization failed"
            elif r == 1 :
                print "still some ouliers but chi2 increases - retry"
            else :
                break
                print "unxepected return code from Minimize"
        
#        for i in range(80): 
#            nout = fit.RemoveOutliers(5.) # 5 sigma
#            fit.Minimize("Distortions Positions")
#            chi2 = fit.ComputeChi2()
            
#            print chi2
#            if (nout == 0) : break
            
        # Fill reference and measurement n-tuples for each tract
        tupleName = "res_" + str(dataRef.dataId["tract"]) + ".list"
        fit.MakeResTuple(tupleName)
        
        # Build an updated wcs for each calexp
        imList = assoc.TheCcdImageList()

        for im in imList :
            tanSip = spm.ProduceSipWcs(im)
            frame = im.ImageFrame()
            tanWcs = afwImage.TanWcs.cast(GtransfoToTanWcs(tanSip, frame, False))
            
            name = im.Name()
            visit, ccd = name.split('_')
            for dataRef in ref :
                if dataRef.dataId["visit"] == int(visit) and dataRef.dataId["ccd"] == int(ccd) :
                    print "Updating WCS for visit: %d, ccd%d"%(int(visit), int(ccd))
                    exp = afwImage.ExposureI(0,0)
                    exp.setWcs(tanWcs)
                    try:
                        dataRef.put(exp, 'wcs')
                    except pexExceptions.Exception as e:
                        self.log.warn('Failed to write updated Wcs: ' + str(e))
                    break 



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

    def __init__(self, config, sourceFluxField, maxMag,centroid,shape):
        """Construct a star selector
        
        @param[in] config: An instance of StarSelectorConfig
        """
        self.config = config
        self.sourceFluxField = sourceFluxField
        self.maxMag = maxMag
        self.centroid=centroid
        self.shape=shape
    
    def select(self, srcCat, calib):
# Return a catalog containing only reasonnable stars / galaxies

        schema = srcCat.getSchema()
        #print schema.getOrderedNames()
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
            if mag > self.maxMag or magErr > 0.1 or flux/fluxErr < 10 :
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
            
        return newCat
