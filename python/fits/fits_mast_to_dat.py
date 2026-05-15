#!/usr/local/bin/python3

# Extract data from a spectral FITS table downloaded from MAST
# Requires prior knowledge of column names
# Does not use pandas

import os
import sys
import numpy as np
import astropy.io.fits as pyfits

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_mast_to_dat.py infile.fits row wavelength_key flux_key outfile.dat  ")
  print(" ")
  sys.exit("Extract data from MAST spectral fits table file \n")
elif len(sys.argv) == 6:
  mastfile = sys.argv[1]
  mastrow = int(float(sys.argv[2]))
  wlkey = sys.argv[3]
  flkey = sys.argv[4]
  outfile = sys.argv[5]
else:
  print(" ")
  print("Usage: fits_mast_to_dat.py infile.fits row wavelength_key flux_key outfile.dat  ")
  print(" ")
  sys.exit("Extract data MAST spectral fits  table file \n")


  
# Open the fits files readonly by default and create an input hdulist

try:
  mastlist = pyfits.open(mastfile) 

except:
  print(" ")
  sys.exit("Could not open the input fits file.\n")


# What do we have?

print("The file ", mastfile, "contains:\n")
mastlist.info()
print("\n")

# Select the bintable which should followthe header mastlist[0]

mastdata = mastlist[1].data

# What is in the data?

print(mastdata.dtype.names)
print("\n")

# An alternative approach would be to use pandas dataframe.from_records(data)

# Get the data as a numpy array from this numpy record by key

wl = mastdata[wlkey]
flux = mastdata[flkey]

# Make a row array for each data set to be saved

xdata = wl[mastrow,:]
ydata = flux[mastrow,:]

# Organize the data to generate a text file

dataout = np.column_stack((xdata,ydata))
np.savetxt(outfile, dataout)
exit()


