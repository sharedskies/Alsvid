#!/usr/local/bin/python3

# Create autocorrelation stack from a stack of uniformly temporally cadenced images

import os
import sys
import numpy as np
from scipy import signal
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_signal_autocorrelate.py  outprefix infile1.fits infile2.fits ...   ")
  print(" ")
  sys.exit("Create a stack of autocorrelated images from stack of  fits images using scipy signal\n ")
elif len(sys.argv) >=5:
  outprefix = sys.argv[1]
  infiles = sys.argv[2:]
else:
  print(" ")
  print("Usage: fits_signal_autocorrelate.py outprefix infile1.fits infile2.fits ...  ")
  print(" ")
  sys.exit("Create a stack of autocorrelated images from stack of  fits images using scipy signal\n")
  
# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwriteflag = True


# Build an image stack in memory
# Test that all the images are the same shape and exit if not

inlists = []
inhdrs = []
outimages = []
nin = 0
for infile in infiles:
  inlist = pyfits.open(infile)
  inhdr = inlist[0].header  
  inimage = inlist[0].data.astype('float32')

  # Process the image to remove NAN's
  # Replace hot/cold pixels with 0

  xsize, ysize = inimage.shape
  fone = np.ones((xsize,ysize))
  inimage = np.nan_to_num(fone*inimage)
  inimage[inimage > 65535] = 0
  inimage[inimage < 0 ] = 0

  # Extract a template from the first image of the stack
  # Test that other images in the stack are the same size as the template
  
  if nin == 0:
    inshape0 = inimage.shape
    inhdr0 = inlist[0].header
    
  else:
    inshape = inimage.shape
    if inshape != inshape0:
      sys.exit('File %s not the same shape as %s \n' %(infile, infiles[0]) )  

  # Autocorrelate the image

  acimage = signal.fftconvolve(inimage,inimage[::-1],mode='same')
    
  outimage = acimage.real    
  # outimage = np.absolute(outimage)
  
  # Make a list of images
  
  outimages.append(outimage.copy())

  # Close the file reference so that mmap will release the handler

  inlist.close()
  
  # Delete unneeded references to the file content
  
  del inimage
  del inhdr

  # Increment the list counter
  
  nin = nin + 1

if nin < 2:
  sys.exit(' More than 1 image is needed to perform this operation. \n')

# Create a numpy cube from the list of images
# Uncomment this if cube is needed for other analyses

# outstack = np.array(outimages)

# Write the cube one slice at a time

nout = int(nin)
  
for i in range(nout):

  # Uncomment this to use the cube instead of the list of images
  #outimage = outstack[i,:,:]
  
  # Comment this if you use the stack instead of the list
  outimage = outimages[i]
  
  outfile = outprefix + '_%04d.fits' % (i,) 
  
  # Create the fits ojbect for this image using the header of the first image

  outlist = pyfits.PrimaryHDU(outimage,inhdr0)

  # Provide a new date stamp

  file_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

  # Update the header

  outhdr = outlist.header
  outhdr['DATE'] = file_time
  outhdr['history'] = 'Autcorrelation slice %d of %d images by fits_signal_autocorrelate' %(i+1,nout)
  outhdr['history'] = 'First image '+  infiles[0]
  outhdr['history'] = 'Last image  '+  infiles[nin-1]

  # Write the fits file

  outlist.writeto(outfile, overwrite = overwriteflag)

# Exit


exit()

