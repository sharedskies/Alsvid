#!/usr/local/bin/python3

"""

  Extract time-varying background from TESS image stack
  
    Input a stack of images in which the background varies with time
    Find the background for each pixel 
    Return a new stack of images of the varying background

"""

import os
import sys
import numpy as np
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc
from scipy import ndimage

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_extract_tess_background.py  outprefix infile1.fits infile2.fits ...   ")
  print(" ")
  sys.exit("Extract background from  a stack of TESS fits images\n ")
elif len(sys.argv) >=3:
  out_prefix = sys.argv[1]
  in_files = sys.argv[2:]
else:
  print(" ")
  print("Usage:  fits_extract_tess_background.py  outprefix infile1.fits infile2.fits ...   ")
  print(" ")
  sys.exit("Extract background from  a stack of TESS fits images\n ")
  
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


# Create a numpy cube from the list of images

working_stack = np.array(in_images)

# Create a footprint filter about each pixel

imfilter = np.zeros((1,25,25))

for i in range(25):
  imfilter[0,0,i]=1
  imfilter[0,i,0]=1
  imfilter[0,24,i]=1
  imfilter[0,i,24]=1
   


# Filter samples around the pixel with this mask


# [[[1. 1. 1. ...  1. ... 1. 1. 1.]
#   [1. 0. 0. ...  0. ... 0. 0. 1.]
#   [1. 0. 0. ...  0. ... 0. 0. 1.]
#   [             ...             ]
#   [1. 0. 0. ...  0. ... 0. 0. 1.]
#   [1. 0. 0. ...  0. ... 0. 0. 1.]
#   [1. 1. 1. ...  1. ... 1. 1. 1.]]]
 

# Find the background for each pixel from its footprint in this image 
# For each image find the bacground  with an 9x9 spatial footprint around that pixel

median_stack = ndimage.median_filter(working_stack, footprint=imfilter, mode="nearest")
percentile_stack = ndimage.percentile_filter(median_stack, footprint=imfilter, percentile=90, mode="nearest")
background_stack = ndimage.median_filter(percentile_stack, footprint=imfilter, mode="nearest")



# The background also varies spatially 
# Evaluate the spatial variation as a standard deviation for each time-slice image
# Find the slice in time with the smallest spatial standard deviation
# Use that as a background for all images 

background_sigma = 100000*np.ones((n_in,))
for i in range(n_in):
  background_sigma[i] = ndimage.standard_deviation(background_stack[i,:,:])

background_minimum_index = np.argmin(background_sigma)

# Inform about the sky background

print("\n")
print("Lowest scatter slice name: ", in_files[background_minimum_index])
print("Lowest scatter background index: ", background_minimum_index)
print("Spatial standard deviation for this index: ", background_sigma[background_minimum_index] )    
print("\n")


working_stack = background_stack

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
  out_hdr['history'] = 'Sky background from image stack'  
  out_hdr['history'] = 'Slice %d of %d images' %(i+1,n_in)
  out_hdr['history'] = 'First image '+  in_files[0]
  out_hdr['history'] = 'Last image  '+  in_files[n_in-1]

  # Write the fits file

  out_list.writeto(out_file, overwrite = overwrite_flag)


exit()

