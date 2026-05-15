#!/usr/local/bin/python3

"""

  Convolve images with a Gaussian 
  
    Input a stack of images
    Return a new stack of images convolved with a Gaussian PSF
    The Gaussian kernel sigma is set internally (default = 1 pixel)

"""

import os
import sys
import numpy as np
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc
from scipy import ndimage

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_convolve_gaussian.py  outprefix infile1.fits infile2.fits ...   ")
  print(" ")
  sys.exit("Convolve a gaussian PSF with a stack of fits images\n ")
elif len(sys.argv) >=3:
  out_prefix = sys.argv[1]
  in_files = sys.argv[2:]
else:
  print(" ")
  print("Usage: Convolve a gaussian PSF with fits_convolve_gaussian.py  outprefix infile1.fits infile2.fits ...   ")
  print(" ")
  sys.exit(" a stack of TESS fits images\n ")
  
# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwrite_flag = False


# Set the sigma for the Gaussian kernel

ksigma = 1  

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

# Construct a convolved fits image from each slice of the numpy cube
# The first axis is the image counter (happened when np_array made the cube)

for i in range(n_in):

  out_image = ndimage.gaussian_filter(working_stack[i,:,:], sigma=ksigma)
  out_file = out_prefix + '_%04d.fits' % (i,) 
  
  # Create the fits ojbect for this image using the header of the original image

  out_list = pyfits.PrimaryHDU(out_image,in_hdrs[i])

  # Provide a new date stamp

  file_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

  # Update the header

  out_hdr = out_list.header
  out_hdr['DATE'] = file_time
  out_hdr['history'] = 'Convolved with %d-pixel Gaussian kernel' %(ksigma,) 
  out_hdr['history'] = 'Slice %d of %d images' %(i+1,n_in)
  out_hdr['history'] = 'First image '+  in_files[0]
  out_hdr['history'] = 'Last image  '+  in_files[n_in-1]

  # Write the fits file

  out_list.writeto(out_file, overwrite = overwrite_flag)


exit()

