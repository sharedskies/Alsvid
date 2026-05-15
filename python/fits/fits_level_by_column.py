#!/usr/local/bin/python3

# Median filter along columns within an image 
# Create and subtract a bias for a column from a median of that column
# Removes pattern noise that is constant within a single column

import os
import sys
import numpy as np
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc

if len(sys.argv) < 3:
  print(" ")
  print("Usage: fits_level_by_column.py  outprefix infile1.fits infile2.fits ...   ")
  print(" ")
  sys.exit("Remove median bias for column noise\n ")
else:
  outprefix = sys.argv[1]
  infiles = sys.argv[2:]
  

# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwriteflag = True  


i = 0
for infile in infiles:
  inlist = pyfits.open(infile)
  inimage = inlist[0].data
  inhdr = inlist[0].header
  inshape = inimage.shape

  # Median each column
  nrows = inshape[0]
  ncols = inshape[1]

  image_row_medians = np.median(inimage,axis=1)
  image_column_medians = np.median(inimage,axis=0)
  bias_image = np.outer(np.ones(nrows), image_column_medians)
  
  # print("nrows, ncols: ", nrows, ncols) 
  # print("Number of row medians: ", len(image_row_medians))
  # print("Number of column medians: ", len(image_column_medians))
  # print("Shape of input image: ", inshape)
  # print("Shape of bias image: ", bias_image.shape)
  # print(bias_image)
  
  outimage = inimage  - bias_image   
  
  outfile = outprefix + '_%04d.fits' % (i,) 
  
  # Provide a new date stamp

  file_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

  # Update the header

  outhdr = inhdr
  outhdr['DATE'] = file_time
  outhdr['history'] = 'Original file %s' % (infile)
  outhdr['history'] = 'Column median bias removed ' 

  # Create the fits ojbect for this image using the header of the first image

  outlist = pyfits.PrimaryHDU(outimage,outhdr)


  # Write the fits file

  outlist.writeto(outfile, overwrite = overwriteflag)

  # Close the file reference so that mmap will release the handler

  inlist.close()
    
  del inimage
  del inhdr
  i = i + 1

exit()

