# SCRIPT TO COMPUTE MASTER BIAS
from ccdproc import ImageFileCollection, combine
import glob as gb
import numpy as np
from astropy.stats import mad_std
import os
import ccdproc
from src.functions.utils import add_prc_metadata

input_path = "output/fits/fixed-headers/"
output_path = "output/fits/calibration/"

all_fits_files =  gb.glob(input_path + "night_22110*/*.fits")

im_collection = ImageFileCollection(filenames=all_fits_files, 
                                    keywords=["imagetyp", "exptime", "ccdbinx", "ccdbiny"])
# Apparently there are 2x2 binned bias, discard them. Only 1x1 science images!!
# We also do that in ALL images just in case there is some other 2x2 binned
im_collection = im_collection.filter(ccdbinx = 1, ccdbiny = 1)

bias_collection = im_collection.filter(imagetyp="bias")

print("For all BIAS images 'EXPTIME = 0.0s'? :", 
       all(bias_collection.summary["exptime"] == 0.0))
       
print("START COMBINING ALL BIAS IMAGES INTO MASTER BIAS...")
# We do master bias by averaging and sigma clipping values
# as described in http://www.astropy.org/ccd-reduction-and-photometry-guide/v/dev/notebooks/02-04-Combine-bias-images-to-make-master.html
# We 5-sigma clipping with median average deviation (MAD)
master_bias = combine(
  bias_collection.files,
  method='average',
  sigma_clip=True, sigma_clip_low_thresh=5, sigma_clip_high_thresh=5,
  sigma_clip_func = np.ma.median, sigma_clip_dev_func = mad_std,
  mem_limit=8e9
  )

# Adds the info of the processing to the header
add_prc_metadata(master_bias.header, 
                 object="master bias",
                 imagetyp="master bias", 
                 prctype="combined", 
                 prcmeth="average with 5sigma clipping")


if not os.path.exists(output_path):
  os.makedirs(output_path)

master_bias.write(output_path + "master_bias.fits", overwrite = True)

print("Master bias saved in ", output_path + "master_bias.fits")
print(">> END OF COMPUTING MASTER BIAS <<")
print("START CALIBRATING FLATS & SCIENCE IMAGES WITH MASTER BIAS...")

# Create directories if they are not present
subfolders = [file.replace(os.path.basename(file), "") for file in all_fits_files]
subfolders = np.unique(subfolders)
subfolders = [dir.replace(input_path, output_path) for dir in subfolders]
_ = [os.makedirs(dir) for dir in subfolders if not os.path.exists(dir)]

# Choose all science and flat images (non bias)
# nonbias_files = [file for file in all_fits_files if file not in bias_collection.files]
# Loop ober nonbias objects
for ccd, filename in im_collection.ccds(regex_match=True, 
                                        imagetyp = "flat|science", # NONBIAS
                                        return_fname = True
                                        ):
  
  ccd = ccdproc.subtract_bias(ccd, master_bias)
  add_prc_metadata(ccd.header, 
                 prctype="calibrated", 
                 prcmeth="subtracted bias")
  
  # Filename is only the fits file name, NOT the full path. Reconvert it
  # to full name and then replace input path with output path.
  filename = [file for file in im_collection.files if filename in file][0]
  output_filename = filename.replace(input_path, output_path)
  ccd.write(output_filename, overwrite = True)
  print("Subtracted master bias on {}, saved it into {}".format(filename, output_filename))
  
print(">> END OF SUBTRACTING BIAS FROM FLATS & SCIENCE IMAGES <<")
