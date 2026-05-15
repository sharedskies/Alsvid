#!/usr/local/bin/python3

# Create stack of spatial 2D FFT images from a stack of images

import os
import sys
import numpy as np
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_fft_2d.py  outprefix infile1.fits infile2.fits ...   ")
  print(" ")
  sys.exit("Create a stack of 2D Fourier Transformed images from a stack of  fits images\n ")
elif len(sys.argv) >=5:
  outprefix = sys.argv[1]
  infiles = sys.argv[2:]
else:
  print(" ")
  print("Usage: fits_fft_2d.py outprefix infile1.fits infile2.fits ...  ")
  print(" ")
  sys.exit("Create a stack of 2D Fourier Transformed images from a stack of  fits images\n")
  
# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwriteflag = True  

# Buildimage stack in memory
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
    template = inimage
  else:
    inshape = inimage.shape
    if inshape != inshape0:
      sys.exit('File %s not the same shape as %s \n' %(infile, infiles[0]) )  

  # Transform the image
  
  outimage = np.fft.fft2(inimage)
  outimage = np.fft.fftshift(outimage)
  outimage = np.absolute(outimage)
  
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
  sys.exit(' More images are needed to perform a Fourier Transform \n')

# Create a numpy cube from the list of images
# Uncomment for other uses

# outstack = np.array(outimages)

# Write the cube one slice at a time

nout = int(nin)
  
for i in range(nout):

  # Uncomment the following to use nump cube instead of list of images
  #outimage = outstack[i,:,:]
  
  # Comment the following if using the stack instead of an image list  
  outimage = outimages[i]
  
  outfile = outprefix + '_%04d.fits' % (i,) 
  
  # Create the fits ojbect for this image using the header of the first image

  outlist = pyfits.PrimaryHDU(outimage.astype('float32'),inhdr0)

  # Provide a new date stamp

  file_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

  # Update the header

  outhdr = outlist.header
  outhdr['DATE'] = file_time
  outhdr['history'] = '2D FFT slice %d of %d images by fits_fft_2d' %(i+1,nout)
  outhdr['history'] = 'First image '+  infiles[0]
  outhdr['history'] = 'Last image  '+  infiles[nin-1]

  # Write the fits file

  outlist.writeto(outfile, overwrite = overwriteflag)

# Exit


exit()

