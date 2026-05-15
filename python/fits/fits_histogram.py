#!/usr/local/bin/python3

"""

  Find a distribution of data in  a stack of images
  
  Return a histogram linear text data file

"""

import os
import sys
import numpy as np
import astropy.io.fits as pyfits

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_histogram.py outfile infile1.fits infile2.fits ...   ")
  print(" ")
  sys.exit("Develop a histogram of data in a stack of images\n ")
elif len(sys.argv) >=3:
  out_file = sys.argv[1]
  in_files = sys.argv[2:]
else:
  print(" ")
  print("Usage: fits_histogram outfile infile1.fits infile2.fits ...  ")
  sys.exit("Requires two or more arguments\n")
  
# Set a overwrite flag True so that histogram data can be overwritten
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
  in_image = in_list[0].data.astype('float32')
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

# Flatten the cube to a linear array

stack_data = np.ravel(working_stack)

fmean = np.mean(stack_data)
fmedian = np.median(stack_data)
fsigma = np.std(stack_data)
fminimum = np.amin(stack_data)
fmaximum = np.amax(stack_data)

# Print diagnostics for all data 

print('  ')
print('  Statistics on the image stack:')
print('  Stack megapixels  = %i' %(stack_data.size/1000000))
print('  Minumum value = %f' %(fminimum,))
print('  Maximum value = %f' %(fmaximum,))
print('  Stack mean = %f' %(fmean,))
print('  Stack median = %f' %(fmedian,))
print('  Stack sigma = %f' %(fsigma,))
print(' ')


# Numpy finds the histogram with default options and returns a tuple
# The histogram is (y,x) where x are the boundaries. 
# There is one more element in x than in y

histogram_data = np.histogram(stack_data[:],bins=4097,range=(-2048.0,2048.0))

# Set the output arrays to match the preferred histogram data format

(ydata, xbounds) = histogram_data

# The xdata are the the midpoints of the boundaries

xdelta = 0.5*(xbounds[1] - xbounds[0])
xdata = np.zeros(len(ydata))
for i in range(len(xbounds)-1):
  xdata[i]=xbounds[i] + 0.5*xdelta

# Save the data

dataout = np.column_stack((xdata,ydata))  
np.savetxt(out_file, dataout)

exit()

