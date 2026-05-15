#!/usr/local/bin/python3

"""

  Create a random decrement autocorrelation stack from 
  
  Inputs: 
    Threshold absolute value  
    Threshold flag (1 or -1)
    Output filename prefix
    Stack of temporally cadenced images
    
  Output: stack of autocorrelated images for the threshold condition
  
  When the flag is any positive number the condition is above threshold
  When the flag is any negative number the condition is below threshold

"""

import os
import sys
import numpy as np
from scipy.ndimage.interpolation import shift
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_rd.py  threshold sign outprefix infile1.fits infile2.fits ...   ")
  print(" ")
  sys.exit("Create a random decrement autocorrelation  stack from a temporal stack of fits images\n")
elif len(sys.argv) >=7:
  threshold = float(sys.argv[1])
  threshold = abs(threshold)
  threshold_sign_flag_float = float(sys.argv[2])
  if threshold_sign_flag_float > 0:
    threshold_sign_flag = True
  else:
    threshold_sign_flag = False  
  outprefix = sys.argv[3]
  infiles = sys.argv[4:]
else:
  print(" ")
  print("Usage: fits_rd.py  threshold sign outprefix infile1.fits infile2.fits ...   ")
  print(" ")
  sys.exit("Create a random decrement autocorrelation  stack from a temporal stack of fits images\n")
  

# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwriteflag = True  

# Build an image stack in memory
# Test that all the images are the same shape and exit if not
# Note numpy array swaps x and y compared to the FITS image
# Image x is fastest varying which results in 
# First index is image y
# Second index is image x

inlists = []
inhdrs = []
inimages = []
nin = int(0)
for infile in infiles:
  inlist = pyfits.open(infile)
  inimage = inlist[0].data
  inhdr = inlist[0].header
  if nin == 0:
    inshape0 = inimage.shape
    imysize, imxsize = inshape0
  else:
    inshape = inimage.shape
    if inshape != inshape0:
      sys.exit('File %s not the same shape as %s \n' %(infile, infiles[0]) )  
  inlists.append(inlist.copy())
  inimages.append(inimage.copy())  
  inhdrs.append(inhdr.copy())
  inlist.close()
  nin = nin + 1

if nin < 2:
  sys.exit(' More than 1 image is needed to perform a random decrement transform \n')

nout = int(nin/2)


# Create a numpy cube from the list of images
# Note again that this swaps x and y in each image

instack = np.array(inimages)

# Copy the an equivalent null array to the output array
# We will add the RD output to this 

outstack = np.copy(0.*np.abs(instack))

# Run the random decrement analysis on all pixels in the image stack
# Store the analysis in the first half of a copy of the input stack
# Use last outimage + 1 as a normalization plane with a count of pixels contributing
# Planes beyond [nout+1] are not meaningful

# We use the fast shift function from scipy which inserts 0. if a value is missing

# Initialize a floating point counter that will be the number of shift events for that pixel
shift_count = np.zeros(inshape0)

# Work on each pixel in the stack 
for j in range(imysize):
  for i in range(imxsize):
    # At this pixel copy the time series from the input data 
    time_series = np.copy(instack[:,j,i])    
    for k in range(nout):      
      
      # Co-add time_series where the data meets a threshold condition
      # Check whether condition is an increase or decrease in the signal
      
      delta = np.abs(time_series[k+1]) - np.abs(time_series[k])
      if threshold_sign_flag:
        if delta > threshold: 
          # Shift time series to align detection with the first frame
          # Subsequent frames will co-add to build correlation from that instance
          outstack[:,j,i] = outstack[:,j,i] + shift(time_series, -k, cval=0.)
          # Increment counter for each detected event above threshold
          shift_count[j,i] = shift_count[j,i] + 1.
        else:
          continue
      else: 
        if delta < threshold: 
          # Shift time series to align detection with the first frame
          # Subsequent frames will co-add to build correlation from that instance
          outstack[:,j,i] = outstack[:,j,i] + shift(time_series, -k, cval=0.)
          # Increment counter for each detected event above threshold
          shift_count[j,i] = shift_count[j,i] + 1.
        else:
          continue            

for i in range(nout):

  outimage = np.copy(outstack[i,:,:])
  
  outfile = outprefix + '_%04d.fits' % (i,) 
  
  # Create the fits object for this image using the header of the first image

  outlist = pyfits.PrimaryHDU(outimage,inhdrs[i])

  # Provide a new date stamp

  file_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

  # Update the header

  outhdr = outlist.header
  outhdr['DATE'] = file_time
  outhdr['history'] = 'Slice %d of %d images by fits_rd' %(i+1,nout)
  if threshold_sign_flag:
    outhdr['history'] = 'Increase by threshold %f' %(threshold,)
  else:
    outhdr['history'] = 'Decrease by hreshold %f' %(threshold,)  
  outhdr['history'] = 'First image '+  infiles[0]
  outhdr['history'] = 'Last image  '+  infiles[nin-1]

  # Write this slice as a fits file

  outlist.writeto(outfile, overwrite = overwriteflag)

# Prepare and write a normalization image

normimage = np.copy(shift_count)
normfile = outprefix + '_norm.fits'
normlist = pyfits.PrimaryHDU(normimage,inhdrs[0])
normhdr = normlist.header
normhdr['DATE'] = file_time
normhdr['history'] = 'Normalization image by fits_rd'
normhdr['history'] = 'Threshold %f' %(threshold,) 

# Write the fits file

normlist.writeto(normfile, overwrite = overwriteflag)




exit()

