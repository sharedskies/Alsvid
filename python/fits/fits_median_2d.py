#!/usr/local/bin/python3

# Median filter within an image over nearest neighbors for a stack of fits images
# Uses ndimage.generic

import os
import sys
import numpy as np
import scipy.signal as sps
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_median_2d.py  outprefix infile1.fits infile2.fits ...   ")
  print(" ")
  sys.exit("Median filter a stack of fits images in the xy plane\n ")
elif len(sys.argv) >=3:
  outprefix = sys.argv[1]
  infiles = sys.argv[2:]
else:
  print(" ")
  print("Usage: fits_median_2d.pyoutprefix infile1.fits infile2.fits ...  ")
  print(" ")
  sys.exit("Nearest neighbor median filter a stack of fits images in the xy plane\n")
  

# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwriteflag = True  


i = 0
for infile in infiles:
  inlist = pyfits.open(infile)
  inimage = inlist[0].data.astype('float32')
  inhdr = inlist[0].header
  inshape = inimage.shape

  # Simple default 3x3 median around the pixel

  outimage = sps.medfilt(inimage)
          
  outfile = outprefix + '_%04d.fits' % (i,) 
  
  # Provide a new date stamp

  file_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

  # Update the header

  outhdr = inhdr
  outhdr['DATE'] = file_time
  outhdr['history'] = 'Original file %s' % (infile)
  outhdr['history'] = 'Nearest neighbor fits_2d_median filtered' 

  # Create the fits ojbect for this image using the header of the first image

  outlist = pyfits.PrimaryHDU(outimage.astype('float32'),outhdr)


  # Write the fits file

  outlist.writeto(outfile, overwrite = overwriteflag)

  # Close the file reference so that mmap will release the handler

  inlist.close()
    
  del inimage
  del inhdr
  i = i + 1

exit()

