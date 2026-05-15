#!/usr/local/bin/python3

# Convert a text image file to fits
# The text file is a series of ascii lines
# Each line is a sequence of space-delimited or tab-delimited numerical entries
# Lines become image rows 
# Each line should be contain the same count of entries 

import os
import sys
import argparse
import numpy as np
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc

parser= argparse.ArgumentParser(description = 'Create a fits image from text data')

if len(sys.argv) == 1:
  print("\n")
  print("Convert a file of ascii numbers into a fits image ")
  print("The file should have one data row for each image row ")
  print("Pixels are space- or tab- delimited in a row ")
  print("\n")
  sys.exit("Usage: fits_from_text infile.txt outfile.fits ")
elif len(sys.argv) == 3:
  infile = sys.argv[1]
  outfile = sys.argv[2]
else:
  sys.exit("Usage: fits_from_text infile.txt outfile.fits ")

# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwriteflag = True  
  
# Set data type for output

newdatatype = np.float32  

# Import the data as a numpy array

inimage = np.loadtxt(infile)

print('Input file %s is ' %(infile,) , inimage.shape)

outlist = pyfits.PrimaryHDU(inimage.astype(newdatatype))

# Provide a new date stamp

file_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

# Update the header

outhdr = outlist.header
outhdr['DATE'] = file_time
outhdr['history'] = 'Image data loaded by fits_from_text'
outhdr['history'] = 'Image file ' + infile

# Create, write, and close the output fits file

outlist.writeto(outfile, overwrite = overwriteflag)


exit()
