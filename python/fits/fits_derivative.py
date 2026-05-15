#!/usr/local/bin/python3

# Differentiate a stack from  of uniformly cadenced images

import os
import sys
import numpy as np
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_derivative.py  outprefix infile1.fits infile2.fits ...   ")
  print(" ")
  sys.exit("Create a derivative stack from a temporal stack of  fits images\n ")
elif len(sys.argv) >=4:
  outprefix = sys.argv[1]
  infiles = sys.argv[2:]
else:
  print(" ")
  print("Usage: fits_derivative.py outprefix infile1.fits infile2.fits ...  ")
  print(" ")
  sys.exit("Differentiate through a cadenced stack of fits images\n")
  

# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwriteflag = True  

# Build an image stack in memory
# Test that all the images are the same shape and exit if not

inhdrs = []
inimages = []
nin = 0
for infile in infiles:
  inlist = pyfits.open(infile)
  inimage = inlist[0].data.astype('float32')
  inhdr= inlist[0].header
  if nin == 0:
    inshape0 = inimage.shape
    xsize, ysize = inshape0
  else:
    inshape = inimage.shape
    inhdr = inlist[0].header
    if inshape != inshape0:
      sys.exit('File %s not the same shape as %s \n' %(infile, infiles[0]) )  
  inhdrs.append(inhdr.copy())
  inimages.append(inimage.copy())  
  inlist.close()
  del inimage
  del inhdr
  nin = nin + 1

if nin < 2:
  sys.exit(' More than 1 image is needed to perform a first order derivative. \n')


# Create a numpy cube from the list of images

instack = np.array(inimages).astype(np.float64)

# Find the differences along the time axis

outstack = np.diff(instack,axis=0)

# Export the differences

nout = nin - 1
  
for i in range(nout):

  outimage = outstack[i,:,:]
  outhdr = inhdrs[i]
  outfile = outprefix + '_%04d.fits' % (i,) 

  # Create the fits ojbect for this image using the header of the first image of a difference pair
  
  outlist = pyfits.PrimaryHDU(outimage,outhdr)

  # Provide a new date stamp

  file_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

  # Update the header

  outhdr = outlist.header
  outhdr['DATE'] = file_time
  outhdr['history'] = 'Slice %d of %d images by fits_derivative' %(i+1,nout)
  outhdr['history'] = 'First image '+  infiles[0]
  outhdr['history'] = 'Last image  '+  infiles[nin-1]

  # Write the fits file

  outlist.writeto(outfile, overwrite = overwriteflag)

# Exit


exit()

