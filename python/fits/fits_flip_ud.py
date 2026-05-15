#!/usr/local/bin/python3

# Flip an image top to bottom

import os
import sys
import numpy as np
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_flip_ud.py  infile.fits outfile.fits")
  print(" ")
  sys.exit("Flip an image up for down \n")
elif len(sys.argv) == 3:
  infile = sys.argv[1]
  outfile = sys.argv[2]  
else:
  print(" ")
  print("Usage: fits_flip_ud.py  infile.fits outfile.fits")
  print(" ")
  sys.exit("Flip an image up for down \n")

# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwriteflag = True  

# Open the fits file readonly by default and create an input hdulist

inlist = pyfits.open(infile) 

# Assign the input header in case it is needed later

inhdr = inlist[0].header

# Assign image data to a numpy array

inimage =  inlist[0].data.astype('float32')

# Flip this image using numpy

outimage = np.flipud(inimage)

# Create an output list from the new image and the input header
# Retain the original datatype

outlist = pyfits.PrimaryHDU(outimage.astype('float32'),inhdr)

# Provide a new date stamp

file_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

# Update the header

outhdr = outlist.header
outhdr['DATE'] = file_time
outhdr['history'] = 'Flipped up-down by fits_flip_ud'
outhdr['history'] = 'Image file ' + infile

# Write the fits file

outlist.writeto(outfile, overwrite = overwriteflag)

# Close the list and exit

inlist.close()

exit()

