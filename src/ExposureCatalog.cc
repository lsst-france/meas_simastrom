#include "lsst/meas/simastrom/ExposureCatalog.h"
#include "lsst/meas/simastrom/Gtransfo.h"
#include "lsst/meas/simastrom/ChipArrangement.h"
#include "lsst/meas/simastrom/simAstrom.h" // for SimAstromControl


using namespace std;

namespace lsst {
namespace meas {
namespace simastrom {

ExposureCatalog::ExposureCatalog(const ChipArrangement *A)
  : arrangement(A) 
{
}

static double sq(const double &x) { return x*x;}

  void ExposureCatalog::AddCalexp(const lsst::afw::table::SortedCatalogT<lsst::afw::table::SourceRecord> &Cat, const int Chip, const SimAstromControl &Control)
{
  
  const std::string& centroid = Control.centroid;
  const std::string& fluxField = Control.sourceFluxField;
  auto xKey = Cat.getSchema().find<double>(centroid + "_x").key;
  auto yKey = Cat.getSchema().find<double>(centroid + "_y").key;
  auto fluxKey = Cat.getSchema().find<double>(fluxField + "_flux").key;
  auto xsKey = Cat.getSchema().find<float>(centroid + "_xSigma").key;
  auto ysKey = Cat.getSchema().find<float>(centroid + "_ySigma").key;
  // the chips and catalogs arrays should be strictly parallel.
  chips.push_back(Chip);
  catalogs.push_back(BaseStarList());
  BaseStarList &catalog =  catalogs.back();
  for (auto i = Cat.begin(); i !=Cat.end(); ++i)
    {
      BaseStar *s = new BaseStar();
      s->x = i->get(xKey);
      s->y = i->get(yKey);
      s->vx = sq(i->get(xsKey));
      s->vy = sq(i->get(ysKey));
      s->flux = i->get(fluxKey);
      catalog.push_back(s);
    }
  std::cout << "INFO: catalog for chip " << Chip << " has " << catalog.size() << " entries" << std::endl;
  // DEBUG
  if (Chip == 0)
    catalog.write("cat0.list");

}


void ExposureCatalog::TangentPlaneCatalog(ExposureStarList &Catalog)
{
  Catalog.clear();
  for (unsigned k=0; k<chips.size(); ++k)
    {
      int chip = chips[k];
      const Gtransfo& pix2TP = arrangement->Pix2TP(chip);
      const BaseStarList &cat = catalogs[k];
      for (auto s = cat.begin(); s != cat.end(); ++s)
	{
          ExposureStar *es = new ExposureStar((*s).get(), chip);
	  FatPoint tmp;
	  pix2TP.TransformPosAndErrors(*es, tmp); // transform to degrees in TP
	  (FatPoint &) *es = tmp;
	  Catalog.push_back(es);
	}
    }
}

const BaseStarList* ExposureCatalog::ChipCatalog(const int Chip) const
{
  for (unsigned k=0; k<chips.size(); ++k)
    if (chips[k] == Chip)
      {
	return &catalogs[k];
      }
  return NULL;
}


}}} // end of namespaces
