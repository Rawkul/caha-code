from pandas_ods_reader import read_ods
import glob as gb
import datetime

def get_valid_filenames():
  """
  Function that returns a dictionary with 3 elements. Each one is a list of
  filenames of each observation night with the images that are not test images.
  """
  
  filenames = {}

  for i in range(3):
    night = str(i + 4)
    to_exclude = read_ods("data/auxiliar/exclude-data.ods", sheet = "night_0" + night)
    files = gb.glob("data/22110{0}/22110{0}VIU_*.fits".format(night))
    
    for ex in to_exclude.filename:
      files[:] = [file for file in files if ex not in file]
      
    files.sort()
    filenames["night_22110" + night] = files
    
  return filenames

def is_bias(hdr):
  """
  Returns true if the fits image is a BIAS image.
  
  Arguments:
    hdr: fits header
  """
  sol = False
  bias_c1 = ("bias" in hdr["OBJECT"].lower()) or ("bias" in hdr["IMAGETYP"].lower()) or ("bias" in hdr["OBSTYPE"].lower())
  bias_c2 = not is_test(hdr)
  if bias_c1 and bias_c2:
    sol = True
  return sol

def is_flat(hdr):
  """
  Returns true if the fits image is a FLAT image.
  
  Arguments:
    hdr: fits header
  """
  sol = False
  flat_c1 = ("flat" in hdr["OBJECT"].lower()) or ("flat" in hdr["IMAGETYP"].lower()) or ("flat" in hdr["OBSTYPE"].lower())
  flat_c2 = not is_test(hdr)
  if flat_c1 and flat_c2:
    sol = True
  return sol

def is_test(hdr):
  """
  Returns true if the fits image is a TEST image.
  
  Arguments:
    hdr: fits header
  """
  sol = False
  
  test_c1 = ("test" in hdr["OBJECT"].lower()) or ("test" in hdr["IMAGETYP"].lower()) or ("test" in hdr["OBSTYPE"].lower())
  test_c2 = ("focus" in hdr["OBJECT"].lower()) or ("focus" in hdr["IMAGETYP"].lower()) or ("focus" in hdr["OBSTYPE"].lower())
  
  if test_c1 or test_c2:
    sol = True
  return sol

def is_science(hdr):
  """
  Returns true if the fits image is a SCIENCE image.
  
  Arguments:
    hdr: fits header
  """
  sol = False
  science_c1 = ("science" in hdr["OBJECT"].lower()) or ("science" in hdr["IMAGETYP"].lower()) or ("science" in hdr["OBSTYPE"].lower())
  science_c2 = not is_flat(hdr) and not is_bias(hdr) and not is_test(hdr)
  
  if science_c1 and science_c2:
    sol = True
  return sol

def get_filter(hdr, nofilter = "free"):
  """
  Returns image filter. Some images don't have the filter information in
  the "FILTER" field.
  
  Arguments:
    hdr: fits header
    nofilter: text to use when no filter is found in the image header.
  """
  
  if type(nofilter) != type("hola caracola"):
    Exception("'nofilter' must be of 'str' type.")
  
  # List of possible filters. For this study only B, V and R bands where used.
  filters = ["B", "V", "R"]
  
  # Only get the value if it's one of the possible filters list
  filter = [f for f in filters if f == hdr["FILTER"]]
  
  # If the filter is NOT in the possible filters list, then we can obtain
  # the filter from the OBJECT, because the filters are also specified in
  # the last chatacter of the OBJECT name
  if filter == []:
    # We test it again in case the filter is not present in the object name
    filter = [f for f in filters if f == hdr["OBJECT"][-1]]
    if filter == []:
      filter = [nofilter]

  return filter[0]


def add_prc_metadata(hdr, prctype, prcmeth, object=None, imagetyp=None, first_time=True):
  
  if object != None:
    hdr["object"] = object
  if imagetyp != None:
    hdr["imagetyp"] = imagetyp
  
  if first_time:
    hdr.append(
    card = ("prctype", prctype, "Data processing type")
    )
    
    hdr.append(
      card = ("prcmeth", prcmeth, "How has the processing been carried out?")
    )
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SCET")
    
    hdr.append(
      card = ("prctime", now, "Date-time of processing yyyy-mm-ddThh:mm:ssCET")
    )
    hdr.add_comment(">>> DATA PROCESSING INFO <<<", before = "prctype")
  else:
    hdr["prctype"] = prctype
    hdr["prcmeth"] = prcmeth
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SCET")
    hdr["prctime"] = now
