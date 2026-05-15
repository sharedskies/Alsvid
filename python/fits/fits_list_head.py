#!/usr/local/bin/python3

# List the fits file primary header 

import os
import sys
import numpy as np
import astropy.io.fits as pyfits

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_list_head.py infile.fits ")
  print(" ")
  sys.exit("List the fits file primary header\n")
elif len(sys.argv) == 2:
  infile = sys.argv[1]
else:
  print(" ")
  print("Usage: fits_list_head.py infile.fits ")
  print(" ")
  sys.exit("List the fits file header\n")

# Open the fits file readonly by default and create an input hdulist

inlist = pyfits.open(infile) 

# Assign the input header in case it is needed later

inhdr = inlist[0].header

# List the header = and spaces for formatting

for key, value in list(inhdr.items()):
   print(key, ' = ', value)

# Close the list and exit

inlist.close()

exit()

