#!/usr/local/bin/python3

# Read an AIJ data table

import sys
import csv 
import numpy as np


if len(sys.argv) != 3:
  print (" ")
  print ("Usage: aij_table_reader.py  data.tbl output.dat")
  print (" ")
  sys.exit("Read a tab-delimited AIJ data table\n ")
elif len(sys.argv) == 3:
  aij_file = sys.argv[1]
  out_file = sys.argv[2]
else:
  print (" ")
  print ("Usage: aij_table_reader.py  data.tbl output.dat")
  print (" ")
  sys.exit("Read and parse an AIJ table\n  ")
  
keyword = "Source-Sky"

# Use csv to read the table into a list of lists

with open(aij_file, "r") as aij_fp:
  aij_table = csv.reader(aij_fp, delimiter = "\t")
  aij_lists = list(aij_table)
  
# Print  the column headers

ncols = len(aij_lists[0])
nrows = len(aij_lists)
nobs = nrows - 1
nstars = 0

print("Found an AIJ table with ", ncols, " columns and ", nrows, "rows.")

for i in range(ncols):
  if keyword in aij_lists[0][i]:
    print(i, aij_lists[0][i])
    nstars = nstars + 1

print("Found ", nstars, " measured stars in the table.")

# Create a numpy arrays to hold the measurements
# The array will entries [i,j] where i is the time slice and j is the star
source = np.zeros((nrows-1,nstars))
stars = np.zeros((nrows-1,nstars))
   
print("Creating an array to hold the photometry measurements ", source.shape)

m = 0
n = 0

for i in range(ncols):
  if keyword in aij_lists[0][i]:
    for m in range(0,nobs):
      source[m,n] = float(aij_lists[m+1][i])
    n = n + 1

# Create a numpy array to hold the total calibration for each time slice

calibration = np.ones(nrows-1)

for i in range(ncols):
  if "tot_C" in aij_lists[0][i]:
    for m in range(0,nobs):
      calibration[m] = float(aij_lists[m+1][i])
    break
    

# Normalize the calibration fluxes

cal_mean = calibration.mean()

# Define the normalized array of photometric data
# Is there a numpy one-liner for this?

for n in range(0,nstars):
  for m in range(0,nobs):
    stars[m,n] = cal_mean*source[m,n]/calibration[m]
    
# Find the standard deviation of the time series for all stars

stars_sigma = stars.std(0)

# Find the average of the time series for all stars

stars_mean = stars.mean(0)

# Export the data for all stars

dataout = np.column_stack((stars_mean,stars_sigma)) 
np.savetxt(out_file, dataout) 

exit()
  
