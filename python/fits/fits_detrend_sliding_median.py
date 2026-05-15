#!/usr/local/bin/python3

"""

  Detrend a stack of images with a sliding median
  
    Return a stack of detrended images scaled to the overall median per pixel

"""

import os
import sys
import numpy as np
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc
from scipy import ndimage

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_detrend_sliding_median.py  n_median outprefix infile1.fits infile2.fits ...   ")
  print(" ")
  sys.exit("Detrend a stack of  fits images with a sliding median\n ")
elif len(sys.argv) >=4:
  n_median = int(sys.argv[1])
  out_prefix = sys.argv[2]
  in_files = sys.argv[3:]
else:
  print(" ")
  print("Usage: fits_detrend_sliding_median.py n_median outprefix infile1.fits infile2.fits ...  ")
  print("Sliding median requires more than ", n_median, " images ")
  sys.exit("Detrend a stack of  fits images with a sliding median\n")
  
# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwrite_flag = False  

# Build an image stack in memory
# Test that all the images are the same shape and exit if not

in_lists = []
in_hdrs = []
in_images = []
n_in = 0
for in_file in in_files:
  in_list = pyfits.open(in_file)
  in_image = in_list[0].data
  in_hdr = in_list[0].header
  if n_in == 0:
    in_shape0 = in_image.shape
  else:
    in_shape = in_image.shape
    if in_shape != in_shape0:
      sys.exit("File %s not the same shape as %s \n" %(in_file, in_files[0]) )  
  in_images.append(in_image.copy())  
  in_hdrs.append(in_hdr.copy())
  
  # Close the file reference so that mmap will release the handler

  in_list.close()
  
  # Delete unneeded references to the file content
  
  del in_image
  del in_hdr
  del in_list

  n_in = n_in + 1

if n_in < n_median:
  sys.exit("More than ", n_median, " images are needed to perform a sliding median \n")


# Create a numpy cube from the list of images

working_stack = np.array(in_images)

# Find the sliding median along the stack axis

reference_stack = ndimage.median_filter(working_stack, footprint=np.ones((n_median,1,1)))

# Find a median for the entire stack  to scale the detrended output

median_image= np.median(working_stack, axis=0)

# Vectorize and do stack math in place here.

working_stack = np.divide(working_stack, reference_stack)
working_stack = median_image*working_stack


# Construct a fits image from each scaled slice of the numpy cube
# The first axis is the image counter (happened when np_array made the cube)

for i in range(n_in):

  out_image = working_stack[i,:,:]
  out_file = out_prefix + '_%04d.fits' % (i,) 
  
  # Create the fits ojbect for this image using the header of the original image

  out_list = pyfits.PrimaryHDU(out_image,in_hdrs[i])

  # Provide a new date stamp

  file_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

  # Update the header

  out_hdr = out_list.header
  out_hdr['DATE'] = file_time
  out_hdr['history'] = 'Detrended with %d slice median' %(n_median,)
  out_hdr['history'] = 'Slice %d of %d images' %(i+1,n_in)
  out_hdr['history'] = 'First image '+  in_files[0]
  out_hdr['history'] = 'Last image  '+  in_files[n_in-1]

  # Write the fits file

  out_list.writeto(out_file, overwrite = overwrite_flag)


exit()

