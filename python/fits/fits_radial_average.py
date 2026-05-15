#!/usr/local/bin/python3

# Average a circularly symmetric file to make a radial section
# Coordinates input are in pixels from (1,1)

import os
import sys
import math
import numpy as np
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_radial_average.py x_center y_center r_max infile.fits outmarker.fits outdata.dat  ")
  print(" ")
  sys.exit("Average a circularly symmetric file to make a radial section\n")
elif len(sys.argv) == 7:
  ncx = int(float(sys.argv[1])) - 1
  ncy = int(float(sys.argv[2])) - 1
  ncr = int(float(sys.argv[3]))
  infile = sys.argv[4]
  outmarkerfile = sys.argv[5]
  outdatafile = sys.argv[6]
else:
  print(" ")
  print("Usage: fits_radial_average.py x_center y_center r_max infile.fits outmarker.fits outdata.dat  ")
  print(" ")
  sys.exit("Average a circularly symmetric file to make a radial section\n")

# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwriteflag = True  
  
# Open the fits files readonly by default and create an input hdulist

inlist = pyfits.open(infile) 

# Assign image data to numpy arrays

inimage =  inlist[0].data.astype('float32')

# Note that first index of a numpy image array is y and second is x
# The array index is the pixel number less 1
# ncx and ncy are numpy addresses corresponding to pixel count that is 1 greater

    
inimage_ysize, inimage_xsize = inimage.shape

if ( (ncx > inimage_xsize - 1) or (ncy > inimage_ysize -1 ) or (ncx < 0) or (ncy < 0) ):
  print('Center of sample zone is outside image boundary.')
  
  # Close the input image file and exit

  inlist.close()  
  exit()
  
  
# Set maximum  radius count for this image size and central point
# Use rcount as the ring number starting at zero so max r is rcount - 1 

rcount = min([ncr, inimage_xsize - ncx, ncx, inimage_ysize - ncy, ncy])

if ( rcount != ncr ):
  print( "  ")
  print( "Sample radius count reduced to %d for this image size\n" % (rcount,) )
 
# Set the boundaries for the average centered on pixel (ncx+1,ncy+1) or numpy (ncy, ncx) 

xmin = ncx - rcount
xmax = ncx + rcount
ymin = ncy - rcount
ymax = ncy + rcount

if (xmin < 0):
  xmin = 0
if (xmax > inimage_xsize - 1):
  xmax = inimage_xsize -1
if (ymin < 0):
  ymin = 0
if (ymax > inimage_ysize - 1):
  ymax = inimage_ysize -1
    

# Set initial values

pixcount = [0] * (rcount)
pixtotal = [0.] * (rcount)
pixavg = [0.] * (rcount)
radius = [0.] * (rcount)

# Generate the data

for i in range (rcount):
  pixcount[i] = 0
  pixtotal[i] = 0.
  rmin = float(i - 1)
  if rmin < 0. :
    rmin = 0.
  rmax = float(i + 1)
  if rmax > rcount :
    rmax = rcount
  for j in range(xmin, xmax):
    for k in range(ymin, ymax):
      xdist2 = (j - ncx)*(j - ncx)
      ydist2 = (k - ncy)*(k - ncy)
      dist = math.sqrt(xdist2 + ydist2)
      if dist <= rmax and dist >= rmin:
        pixcount[i] = pixcount[i] + 1   
        pixtotal[i] = pixtotal[i] + inimage[k, j]
  pixavg[i] = pixtotal[i]/pixcount[i] 
  radius[i] = float(i)
dataout = np.column_stack((radius,pixavg))  
np.savetxt(outdatafile, dataout)

# Mark the center of symmetry and 4 reference points on the original numpy image

outimage = inimage
outimage[ncy][ncx]   = 10000.
outimage[ymin][xmin] = 10000.
outimage[ymin][xmax] = 10000.
outimage[ymax][xmin] = 10000.
outimage[ymax][xmax] = 10000.

outlist = pyfits.PrimaryHDU(outimage.astype('float32'))

# Create, write, and close the output marker fits file

outlist.writeto(outmarkerfile, overwrite = overwriteflag)


# Close the input image file

inlist.close()

exit ()


