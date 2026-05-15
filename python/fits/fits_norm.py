#!/usr/local/bin/python3

# Normalize a fits image using image median

import os
import sys
import numpy as np
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_norm.py infile.fits outfile.fits")
  print(" ")
  sys.exit("Normalize a fits image by median\n")
elif len(sys.argv) ==3:
  infile = sys.argv[1]
  outfile = sys.argv[2]
else:
  print(" ")
  print("Usage: fits_norm.py infile.fits outfile.fits")
  print(" ")
  sys.exit("Normalize a fits image by median\n")

# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwriteflag = True  
  
# Open the fits file readonly by default and create an input hdulist

inlist = pyfits.open(infile) 

# Assign the input header 

inhdr = inlist[0].header

# Assign image data to numpy array

inimage =  inlist[0].data.astype('float32')

# Use numpy to calculate the mean of image

immedian = np.median(inimage)

# Normalize the image to the median

outimage = inimage/immedian

# Create the fits ojbect for this image using the header of the first image
# Use float32 for output type

outlist = pyfits.PrimaryHDU(outimage.astype('float32'),inhdr)

# Provide a new date stamp

file_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

# Update the header

outhdr = outlist.header
outhdr['DATE'] = file_time
outhdr['history'] = 'Median normalized by fits_norm' 
outhdr['history'] = 'Image file '+ infile

# Write the fits file

outlist.writeto(outfile, overwrite = overwriteflag)

# Close the input  and exit

inlist.close()
exit()

