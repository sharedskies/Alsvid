#!/usr/local/bin/python3

"""

  Remove time-varying background 
  
    Input a stack of images in which the background varies with time
    Find the background for each pixel from the minimum in the region around the pixel
    Identify a representative minimum background from the stack
    Return a new stack of images with this varying background removed
    Optionally include a static minimum sky background

"""

import os
import sys
import numpy as np
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc
from scipy import ndimage

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_detrend_sliding_minimum.py  n_minimum outprefix infile1.fits infile2.fits ...   ")
  print(" ")
  sys.exit("Detrend a stack of  fits images with a sliding minimum\n ")
elif len(sys.argv) >=4:
  n_minimum = int(sys.argv[1])
  out_prefix = sys.argv[2]
  in_files = sys.argv[3:]
else:
  print(" ")
  print("Usage: fits_detrend_sliding_minimum.py n_minimum outprefix infile1.fits infile2.fits ...  ")
  print("Sliding minimum requires more than ", n_minimum, " images ")
  sys.exit("Detrend a stack of  fits images with a sliding minimum\n")
  
# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwrite_flag = False  

# Set this true to include a minimum sky background in all exported fits slices

sky_background_flag = False

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

if n_in < n_minimum:
  sys.exit("More than ", n_minimum, " images are needed to perform a sliding minimum \n")


# Create a numpy cube from the list of images

working_stack = np.array(in_images)

# Find the background for each pixel from its footprint in this image 
# First for each image identify a minimum with an 11x11 spatial footprint around that pixel
# Then use that as input to find the median of n-minimum successive slices

minimum_stack = ndimage.minimum_filter(working_stack, footprint=np.ones((1,11,11)))
background_stack = ndimage.median_filter(minimum_stack, footprint=np.ones((n_minimum,11,11))) 

# The background also varies spatially 
# Evaluate the spatial variation as a standard deviation for each time-slice image
# Find the slice in time with the smallest spatial standard deviation
# Use that as a background for all images 

background_sigma = 100000*np.ones((n_in,))
for i in range(n_in):
  background_sigma[i] = ndimage.standard_deviation(background_stack[i,:,:])

background_minimum_index = np.argmin(background_sigma)
background_minimum = background_stack[background_minimum_index]

# Inform about the sky background

print("\n")
print("Lowest scatter background index: ", background_minimum_index)
print("Spatial standard deviation for this index: ", background_sigma[background_minimum_index] )

if sky_background_flag:
  print("Sky background is included in exported fits slices.")
else:
  print("Sky background is removed  in exported fits slices.")
    
print("\n")

# Subtract the background from each image
# This will correct for scattered light but also may remove large scale diffuse or blended components

working_stack = np.subtract(working_stack, background_stack)

# Optionally add back a minimum background that should have the least component of time-variable scattering

if sky_background_flag:
  working_stack = working_stack + background_minimum

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
  out_hdr['history'] = 'Detrended with %d slice minimum' %(n_minimum,)
  if sky_background_flag:
    out_hdr['history'] = 'Sky background included'
  else:
    out_hdr['history'] = 'Sky background removed'  
  out_hdr['history'] = 'Slice %d of %d images' %(i+1,n_in)
  out_hdr['history'] = 'First image '+  in_files[0]
  out_hdr['history'] = 'Last image  '+  in_files[n_in-1]

  # Write the fits file

  out_list.writeto(out_file, overwrite = overwrite_flag)


exit()

