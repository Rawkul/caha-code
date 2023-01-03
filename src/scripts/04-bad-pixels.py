import ccdproc as ccdp
import astropy.units as u


filters = ["B", "V", "R"]
nights = ["4", "5", "6"]
input_path = "output/fits/calibration/night_22110"
save_path = "output/fits/calibration/"

for n in nights:
  dir = input_path + n
  imc = ccdp.ImageFileCollection(dir).filter(imagetyp = "flat", 
                                             prctype = 'calibrated',
                                             prcmeth = 'subtracted bias')
  for f in filters:
    imc_f = imc.files_filtered(filter = f)
    if len(imc_f) > 0:
      
      print("Computing camera mask for night 22110{} and filter {}...".format(n, f))
      
      ccd1 = ccdp.CCDData.read(imc_f[0])
      ccd2 = ccdp.CCDData.read(imc_f[-1])
      ratio = ccd2.divide(ccd1)
      rmask = ccdp.ccdmask(ratio)
      
      ccdmask = ccdp.CCDData(data = rmask.astype("uint8"), unit=u.dimensionless_unscaled)
      ccdmask.header["imagetyp"] = "flat mask"
      ccdmask.header["filter"] = f
      
      savename = save_path + "camera_mask_" + f + "_night_22110" + n + ".fits"
      ccdmask.write(savename)
      print("Saved on " + savename)

print(">>> END OF COMPUTING BAD PIXELS <<<")
