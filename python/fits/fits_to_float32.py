#!/usr/local/bin/python3

"""
  Convert a fits image to float32

  Intended to take an integer FITS file and convert it to floating point
  Looks for and removes the PEDESTAL if it exists
  Exports the new file with the original values after removing a pedestal

  Input:
    input file name
    output file name
  
  Output:
    floating point fits file with the original header and the pedestal removed

"""      

import os
import sys
import numpy as np
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_to_float32.py infile.fits outfile.fits ")
  print(" ")
  sys.exit("Convert a fits image to float32 while removing a pedestal\n")
elif len(sys.argv) == 3:
  infile = sys.argv[1]
  outfile = sys.argv[2]
else:
  print(" ")
  print("Usage: fits_to_float32.py infile.fits outfile.fits ")
  print(" ")
  sys.exit("Convert a fits image to float32 while removing a pedestal\n")
 

# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwriteflag = True  
  
# Open the fits file readonly by default and create an input hdulist

inlist = pyfits.open(infile) 

# Assign the input header 

inhdr = inlist[0].header

# Assign image data to numpy array

inimage =  inlist[0].data.astype('float32')

# Look for the PEDESTAL keyword

if "PEDESTAL" in inhdr:
  pedestal = float(inhdr["PEDESTAL"])
else:
  pedestal = 0.

# Convert the image

outimage = inimage + pedestal    

# Create the fits ojbect for this image using the header of the first image
# Use float32 for output type

outlist = pyfits.PrimaryHDU(outimage.astype('float32'),inhdr)

# Provide a new date stamp

file_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

# Update the header

outhdr = outlist.header
outhdr["PEDESTAL"] = 0.
outhdr['DATE'] = file_time
outhdr['history'] = 'Converted to float32 wihtout a pedestal by fits_to_float32' 
outhdr['history'] = 'Image file '+  infile

# Write the fits file

outlist.writeto(outfile, overwrite = overwriteflag)

# Close the input  and exit

inlist.close()
exit()

