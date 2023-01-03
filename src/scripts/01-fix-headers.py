# This script fix headers. It standardizes the headers putting
# object and filter information in a correct way
from src.functions.utils import *
from astropy.io import fits
import os
from ccdproc import ImageFileCollection

filenames = get_valid_filenames()
output_path = "output/fits/fixed-headers/"

if output_path[-1] == "/":
  output_path = output_path[:-1]

for night in filenames.keys():
  
  subdir = output_path + "/" + night
  if not os.path.exists(subdir):
    print("Creating directoty '" + subdir + "/' as it wasn't found in the system.")
    os.makedirs(subdir)
  
  for file in filenames[night]:
    image = fits.open(file)
    hdr = image[0].header
    f = get_filter(hdr)
    
    if is_test(hdr):
      hdr["IMAGETYP"] = hdr["OBSTYPE"] = "test"
      hdr["FILTER"] = f
    elif is_bias(hdr):
      hdr["IMAGETYP"] = hdr["OBSTYPE"] = "bias"
      hdr["FILTER"] = f
    elif is_flat(hdr):
      hdr["IMAGETYP"] = hdr["OBSTYPE"] = "flat"
      hdr["FILTER"] = f
    elif is_bias(hdr):
      hdr["IMAGETYP"] = hdr["OBSTYPE"] = "bias"
      hdr["FILTER"] = f
    elif is_science(hdr):
      hdr["IMAGETYP"] = hdr["OBSTYPE"] = "science"
      if (f == "free"): # <<<---- Se ha comprobado manualmente que las imágenes 0052 a 0056 no tienen info de filtro en el cabecero, pero son de la segunda noche cuando f=B según los logs
        f = "B"
        
      hdr["FILTER"] = f
      
    hdr["BUNIT"] = "adu" # Necessary for combinning with ccdproc
    
    out_filename = subdir + "/" + os.path.basename(file)
    image.writeto(out_filename, overwrite = True)
    image.close()
    print("Fixed header of: " + out_filename)
    
print(">> END <<")
