#!/usr/local/bin/python3

# Add an incremental time stamp to an image header 
# Useful for photometry on a uniformily cadenced stack lacking keyword
#
#   DATE-OBS
#   EXPOSURE


import os
import sys
import numpy as np
import astropy.io.fits as pyfits
import time
from datetime import datetime


if len(sys.argv) >= 3:
  exposure = float(sys.argv[1])
  infiles = sys.argv[2:]
else:
  print(" ")
  print("Usage: fits_add_datetime.py exposure file1.fits file2.fits ...")
  print(" ")
  sys.exit("Add an exposure time and incremental date to headers of fits files. \n")



# Provide a new starting time  

start_time = time.time()
image_time = start_time - exposure  

for infile in infiles:
  
  # Open the fits file readonly by default and create an input hdulist

  inlist = pyfits.open(infile) 
  
  # Assign the input header 
  
  inhdr = inlist[0].header
  
  # Assign input and out image data to  numpy arrays

  inimage =  inlist[0].data
  outimage = inimage
  
  # Assign the image header
  
  inhdr = inlist[0].header
  outhdr = inhdr
  
  # Increment the image time and date_obs string
  
  image_time = image_time + exposure
  ymd_str = str(datetime.fromtimestamp(image_time).strftime("%Y-%m-%d"))
  hms_str = str(datetime.fromtimestamp(image_time).strftime("%H:%M:%S.%f"))
  date_obs_str = ymd_str+"T"+hms_str
  
  # Update the header entry and value from the command line
  
  outhdr["EXPOSURE"] = exposure
  outhdr["DATE-OBS"] = date_obs_str
  
  # Create an output list from the new image and the edited header
  
  outlist = pyfits.PrimaryHDU(outimage,outhdr)
  
  # Update the header
  
  outhdr = outlist.header
    
  # Write the fits file back with the same name

  outfile = infile
  outlist.writeto(outfile, overwrite = True)

  # Close the list and exit

  inlist.close()

exit()

