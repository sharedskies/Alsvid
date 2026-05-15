#!/usr/local/bin/python3

# Convert a png image to tiles
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
  print("Usage: tiles_from_png.py infile.png outfile_base ")
  print(" ")
  sys.exit("Convert a png image to tiles\n") 
elif len(sys.argv) ==3:
  infile = sys.argv[1]
  outfile_base = sys.argv[2]
else:
  print(" ")
  print("Usage: tiles_from_png.py infile.png outfile_base ")
  print(" ")
  sys.exit("Convert a png image to tiles\n")
 
# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwriteflag = True  
  
# Assign image data to numpy array
# Convert color images to grayscale using native flatten option
inimage = scipy.misc.imread(infile, flatten=1)

inimage_shape = inimage.shape
tile_size = (256, 256)
offset = (256, 256)

for i in range(int(m.ceil(inimage_shape[0]/(offset[1] * 1.0)))):
    for j in range(int(m.ceil(inimage_shape[1]/(offset[0] * 1.0)))):
        cropped_image = inimage[offset[1]*i:min(offset[1]*i+tile_size[1], inimage_shape[0]), offset[0]*j:min(offset[0]*j+tile_size[0], inimage_shape[1])]
        # Debugging the tiles
        scipy.misc.imsave(outfile_base +"_"+ str(i) + "_" + str(j) + ".png", cropped_image)

exit()
