import glob as gb
import numpy as np
from astropy.stats import mad_std
import os
import ccdproc as ccdp
from src.functions.utils import add_prc_metadata

input_path = "output/fits/calibration/"
output_path = "output/fits/final-calibration/"

# Necessary for scaling flats. We'll scale with the median as in
# http://www.astropy.org/ccd-reduction-and-photometry-guide/v/dev/notebooks/05-04-Combining-flats.html
def inv_median(a):
    return 1 / np.median(a)

# The used filters
filters = ["B", "V", "R"]

# Hay que hacerlo diferente para cada noche porque varía bastante la iluminación

for i in range(3):
  night = input_path + "night_22110" + str(i + 4)
  all_fits_files = gb.glob(night + "/*")
  im_collection = ccdp.ImageFileCollection(filenames = all_fits_files,
                                           keywords = ["imagetyp", "filter", "prctype", "prcmeth"])
  master_flat = {}
  # Combine flats by filter
  print("START COMBINING FLAT IMAGES FOR NIGHT 0{}/11/2022...".format(i + 4))
  
  for f in filters:
    # Take flats of filter f
    to_combine = im_collection.files_filtered(imagetyp = "flat",
                                              prctype = "calibrated",
                                              prcmeth = "subtracted bias",
                                              filter = f,
                                              include_path = True)
    if to_combine != []: # Some night don't have certain flats with some filters
      
      master_flat[f] = ccdp.combine(to_combine,
                                    method='average', scale = inv_median,
                                    sigma_clip=True, sigma_clip_low_thresh=5, sigma_clip_high_thresh=5,
                                    sigma_clip_func = np.ma.median, sigma_clip_dev_func = mad_std,
                                    mem_limit=8e9
                                   )
      
      master_flat[f].data += 1e-19 # Avoids later division by 0
      
      add_prc_metadata(master_flat[f].header, 
                       object="master flat",
                       imagetyp="master flat", 
                       prctype= master_flat[f].header["prctype"] + "& scaled+combined",
                       prcmeth= master_flat[f].header["prcmeth"] + "& scalad with median + average with 5sigma clipping",
                       first_time=False)
      
      master_name = input_path + "master_flat_" + f + "_night_22110" + str(i + 4) + ".fits"
      master_flat[f].write(master_name, overwrite = True)
      
      print("Computed master flat for filter " + f + " and night 0{}/11/2022".format(i+4) + ". Saved in " + master_name)

  print(">>> END OF COMBINING FLAT IMAGES FOR NIGHT 0{}/11/2022<<<<".format(i + 4))
  print("START CALIBRATING SCIENCE IMAGES WITH FLAT FOR NIGHT 0{}/11/2022...".format(i+5))
  
  # Create directories if they are not present
  subfolders = [file.replace(os.path.basename(file), "") for file in all_fits_files]
  subfolders = np.unique(subfolders)
  subfolders = [dir.replace(input_path, output_path) for dir in subfolders]
  _ = [os.makedirs(dir) for dir in subfolders if not os.path.exists(dir)]
  
  # Funciona porque imagetyp es de una sola noche y sabemos que en cada noche
  # hay un flat de ese filtro.
  for ccd, filename in im_collection.ccds(imagetyp = "science",
                                                    prctype = "calibrated",
                                                    prcmeth = "subtracted bias",
                                                    return_fname = True):
    f = ccd.header["filter"]
    ccd = ccdp.flat_correct(ccd, master_flat[f])
    add_prc_metadata(ccd.header,
                   prctype= "final calibration",
                   prcmeth= "subtracted bias and divided flat",
                   first_time = False)
    filename = [file for file in im_collection.files if filename in file][0]
    output_filename = filename.replace(input_path, output_path)
    ccd.write(output_filename, overwrite = True)
    print("Corrected flat in filter {} for image {} and saved in file {}".format(f, filename, output_filename))
    
  print(">>> END ALL CALIBRATIONS OF IMAGES FOR NIGHT 0{}/11/22022 <<< ".format(i+4))

print(">>> END ALL CALIBRATIONS OF IMAGES :D <<< ")
