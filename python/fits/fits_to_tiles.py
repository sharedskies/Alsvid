#!/usr/local/bin/python3

# Convert a fits image to png tiles
# Adapted from https://stackoverflow.com/questions/45950124/creating-image-tiles-mn-of-original-image-using-python-and-numpy

import os
import sys
import numpy as np
import astropy.io.fits as pyfits
import scipy
import scipy.misc
import math as m

from time import gmtime, strftime  # for utc

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_to_tiles.py infile.fits outfile_base [minval maxval]")
  print(" ")
  sys.exit("Convert a fits image to png tiles\n") 
elif len(sys.argv) ==3:
  infile = sys.argv[1]
  outfile_base = sys.argv[2]
  minmaxflag = False
elif len(sys.argv) ==5:
  # Minimum and maximum
  infile = sys.argv[1]
  outfile_base = sys.argv[2]
  minval = float(sys.argv[3])
  maxval = float(sys.argv[4])
  if minval >= maxval:
    sys.exit("The specified minimum must be less than the maximum\n")
  minmaxflag = True   
else:
  print(" ")
  print("Usage: fits_to_tiled_png.py infile.fits outfile_base [minval maxval")
  print(" ")
  sys.exit("Convert a fits image to png tiles\n")
 
# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwriteflag = True  

# Open the fits file and create an hdulist

inlist = pyfits.open(infile) 

# Assign image data to a numpy array

fitsimage =  inlist[0].data.astype('float32')

# Scale the image data linearly
if minmaxflag:
  pass
else:  
  minval = float(np.min(fitsimage))
  maxval = float(np.max(fitsimage))

delta = maxval - minval
scaled_image = 255.0*(fitsimage - minval)/(delta)
scaled_image[scaled_image > 255.] = 255.
scaled_image[scaled_image < 0.] = 0.

# Flip the image so that it will appear in the png as it does in ds9

inimage = np.flipud(scaled_image)
 
inimage_shape = inimage.shape
tile_size = (256, 256)
offset = (256, 256)

for i in range(int(m.ceil(inimage_shape[0]/(offset[1] * 1.0)))):
    for j in range(int(m.ceil(inimage_shape[1]/(offset[0] * 1.0)))):
        cropped_image = inimage[offset[1]*i:min(offset[1]*i+tile_size[1], inimage_shape[0]), offset[0]*j:min(offset[0]*j+tile_size[0], inimage_shape[1])]
        scipy.misc.imsave(outfile_base +"_"+ str(i) + "_" + str(j) + ".png", cropped_image)

exit()
