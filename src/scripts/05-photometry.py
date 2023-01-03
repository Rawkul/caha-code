import pandas as pd
import numpy as np
import ccdproc as ccdp
import astropy.units as u
from photutils import ApertureStats, CircularAnnulus, CircularAperture
from astropy.stats import SigmaClip
from photutils.background import Background2D
from photutils import make_source_mask
from photutils.utils import calc_total_error

OUTPUT_FILE = "output/photometry.csv"

# Sigma clip for background calculation
# 3-sigma and not 5 because background is weaker
sigclip = SigmaClip(sigma=3.0, maxiters=10)

def get_coords(file, astrometry_data):
  aux = astrometry_data.loc[astrometry_data.file == file][["obj", "x", "y"]]
  aux.x -= 1
  aux.y -= 1
  return (aux.obj, aux[["x", "y"]])

# Astrometry data
astdata = pd.read_csv("data/auxiliar/astrometry.csv")

def get_mag(flux, zmag):
  -2.5 * np.log10(flux) + zmag
  
def get_err_mag(flux, fluxerr):
  -2.5 / (flux * np.log(10)) * fluxerr

# Different radius to test 1 to 30
radii = list(range(1, 31))
# Circular annulus deviation from aperture circunference (in pixels)
ring_dev = +6
# Width of the ring annulus
ring_w = 10

filters = ["B", "V", "R"]
nights = ["4", "5", "6"]

input_path = "output/fits/final-calibration/night_22110"

phot_data = pd.DataFrame({
  "filename" : [""],
  "object" : [""],
  "date_start" : [""],
  "date_end" : [""],
  "exp_time" : [np.nan],
  "filter" : [""],
  "local_flux" : [np.nan],
  "local_err_flux" : [np.nan],
  "general_flux" : [np.nan],
  "general_err_flux" : [np.nan],
  "airmass" : [np.nan],
  "aperture" : [np.nan],
  "local_fwhm" : [np.nan],
  "general_fwhm" : [np.nan]
})

masks = {}
for n in nights:
  masks["night_22110" + n] = {}
  for f in filters:
    fname = "output/fits/calibration/camera_mask_{}_night_22110{}.fits".format(f, n)
    try:
      masks["night_22110" + n][f] = ccdp.CCDData.read(fname, unit=u.dimensionless_unscaled)
      masks["night_22110" + n][f].data = masks["night_22110" + n][f].data.astype('bool')
    except:
      continue
    print("END OF " + f)    


for n in nights:
  print("START WITH NIGHT 22110" + n + "...")
  dir = input_path + n
  imc = ccdp.ImageFileCollection(dir).filter(imagetyp = "science", 
                                             prctype = 'final calibration',
                                             prcmeth = 'subtracted bias and divided flat')
  for f in filters:
    
    for ccd, filename in imc.ccds(filter = f, return_fname = True):
      print("READING & PROCESING " + filename + "...")
      objs, coords = get_coords(filename, astdata)
      night = "night_22110" + n
      mask = masks[night][f]
      
      source_mask = make_source_mask(ccd.data, nsigma = 3, npixels = 4)
      source_mask = source_mask | mask
      general_bkgr = Background2D(ccd.data, (64, 64), mask = source_mask, filter_size = (3, 3), sigma_clip = sigclip)
      error = calc_total_error(ccd.data, general_bkgr.background_rms, ccd.header["GAIN"])
      
      print("Background estimated, now doing photometry on " + filename + "...")
      for r in radii:
        aper = CircularAperture(coords, r = r)
        bkgr = CircularAnnulus(coords, r_in = r + ring_dev, r_out=r + ring_dev + ring_w)
        bkgr_stats = ApertureStats(ccd.data, bkgr, mask = mask, sigma_clip = sigclip, error = error)
        aper_stats = ApertureStats(ccd.data, aper, mask = mask, local_bkg = bkgr_stats.median, error = error)
        general_stats = ApertureStats(ccd.data - general_bkgr.background, aper, mask = mask, error = error)
        
        # Add data
        auxfd = pd.DataFrame({
          "filename" : filename,
          "object" : objs,
          "date_start" : ccd.header["DATE-OBS"],
          "date_end" : ccd.header["DATE"],
          "exp_time" : ccd.header["EXPTIME"],
          "filter" : f,
          "local_flux" : aper_stats.sum,
          "local_err_flux" : aper_stats.sum_err,
          "general_flux" : general_stats.sum,
          "general_err_flux" : general_stats.sum_err,
          "airmass" : ccd.header["AIRMASS"],
          "aperture" : r,
          "local_fwhm" : aper_stats.fwhm,
          "general_fwhm" : general_stats.fwhm
          })
        phot_data = phot_data.merge(auxfd, how = "outer")
        phot_data.to_csv(OUTPUT_FILE) # Store it as soon as it's computed!
      print(">> ENDED DOING PHOTOMETRY ON " + filename + " <<")
  print(">>> ENDED DOING PHOTOMETRY ON NIGHT 22110" + n + " <<<")

phot_data = phot_data.iloc[1:] # Remove the first row which is useless
phot_data.to_csv(OUTPUT_FILE)

print("Data stored in " + OUTPUT_FILE)
print(" (:< END!!!!!  >:D")

import os
os.system("poweroff")