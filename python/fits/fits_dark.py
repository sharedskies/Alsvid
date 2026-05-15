#!/usr/local/bin/python3

# Dark subtract a fits CCD 2D image with 32-bit float output

import os
import sys
import numpy as np
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_dark.py infile.fits darkfile.fits outfile.fits ")
  print(" ")
  sys.exit("Subtract a dark image from a fits image of the same exposure \n")
elif len(sys.argv) == 4:
  infile = sys.argv[1]
  darkfile = sys.argv[2]
  outfile = sys.argv[3]
else:
  print(" ")
  print("Usage: fits_dark.py infile.fits darkfile.fits outfile.fits ")
  print(" ")
  sys.exit("Subtract a dark image from a fits image of the same exposure \n")

# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwriteflag = True  

# Open the fits files readonly by default and create an input hdulist

inlist = pyfits.open(infile) 
darklist = pyfits.open(darkfile)

# Assign the input header in case it is needed later

inhdr = inlist[0].header

# Assign image data to numpy arrays

inimage =  inlist[0].data.astype('float32')
indark = darklist[0].data.astype('float32')

# Test for match of shapes

if inimage.shape != indark.shape:
  inlist.close()
  darklist.close()
  sys.exit("Image and dark files are of unequal sizes")
  

# Create a dark-subtracted image

outimage = inimage - indark

# Create an output list from the new image and the input header
# Use float32 for output type 

outlist = pyfits.PrimaryHDU(outimage.astype('float32'),inhdr)

# Provide a new date stamp

file_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

# Update the header

outhdr = outlist.header
outhdr['DATE'] = file_time
outhdr['history'] = 'Dark subtracted by fits_dark'
outhdr['history'] = 'Image file ' + infile
outhdr['history'] = 'Dark file ' + darkfile

# Write the fits file

outlist.writeto(outfile, overwrite = overwriteflag)

# Close the list and exit

inlist.close()
darklist.close()

exit()

