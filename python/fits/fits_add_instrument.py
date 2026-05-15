#!/usr/local/bin/python3

# Add an instrument to an image header 
# Useful for photometry on a uniformily cadenced stack lacking keywords
#
#   DATE-OBS
#   EXPOSURE
#   INSTRUME
#
# Required by AIJ for TESS photometry


import os
import sys
import numpy as np
import astropy.io.fits as pyfits
import time
from datetime import datetime


if len(sys.argv) >= 3:
  instrument= sys.argv[1]
  infiles = sys.argv[2:]
else:
  print(" ")
  print("Usage: fits_add_instrument.py instrument file1.fits file2.fits ...")
  print(" ")
  sys.exit("Add an instrument to headers of fits files. \n")

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
    
  # Update the header entry and value from the command line
  
  outhdr["INSTRUME"] = instrument
  
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

