#!/usr/local/bin/python3

"""

   Write a linearly scaled color png image from a FITS Bayer masked image file
   Balance colors
   
   Input: 
     infile.fits
     outfile.png
     
   Output:
     Color outfile.png
     
   This version combines the Bayer r, g, and b pixels into a color superpixel
   with r, g, and b colors assigned from the original filtered pixels 
   
   Optionally it applies a 3x3 median to remove outliers in each color
   
   Balances color scale to the minimum and maximum of the filtered components
   
   RGB pixel mask is set for the protocol of Allied Vision Manta cameras 
     

"""

import os
import sys
import numpy as np
import scipy.signal as sps
import astropy.io.fits as pyfits
import imageio

# Scale an image for output in a color-balanced PNG format
# Median filter this color image with 3x3 kernel to remove outliers
median_flag = True

def color_balance(inimage):

  # Apply median to the image before checking min/max
  
  if median_flag:
    inimage = sps.medfilt(inimage, kernel_size=3) 

  minval = float(np.min(inimage))
  maxval = float(np.max(inimage))
  delta = maxval - minval
  newimage = 255.0*(inimage - minval)/(delta)
  newimage[newimage > 255.] = 255.
  newimage[newimage < 0.] = 0.
  return newimage


if len(sys.argv) != 3:
  print(" ")
  print("Usage: fits_to_rgb_png.py infile.fits outfile.png")
  print(" ")
  sys.exit("Create a linearly-scaled color-balanced png image\n")

infile = sys.argv[1]
outfile = sys.argv[2]
  
# Open the fits file and create an hdulist

inlist = pyfits.open(infile) 

# Assign image data to a numpy array

inimage =  inlist[0].data.astype('float32')

print('Input image size: ', inimage.size)
print('Input image shape: ', inimage.shape)


# Convert the RGB values from the masked image pixels to separate images
# Set the size of the output image noting for FITS images here
#   Width of the image is spanned by the second index
#   Height of the image is spanned by the first index

outimage = inimage
h, w = outimage.shape
oh = h//2
ow = w//2


# Pick up RGB samples to match Allied Vision Bayer camera mask
# FITS images enumerate pixels starting at [1,1] as does Julia
# Numpy images enumerate arrays starting at [0,0]

# The pattern in all Allied Vision Manta cameras is 
#
#
#           Column 1    Column 2    Column 3
#
#   Row 1      R           G           R
#   Row 2      G           B           G
#   Row 3      R           G           R
#
# When x is the column number (first index) and y is the row number (second index)
#  in a 1-based enumeration (e.g. Julia)
#
#    FITS B  [x, y] is [even, even]
#    FITS R  [x, y] is [odd,   odd]
#    FITS G  [x, y] is both [even, odd] and [odd, even]
#
#  and in a 0-based enumeration even/odd are swapped.
#
# Most Sony CMOS sensors are rectangular and wider than high (w>h)
# In Numpy arrays the row number is the first index
#   and the column number is the second, i.e. [y,x]

# This algorithm assigns the color to its pixel and does not interpolate
# The resulting images are true to color with 1-pixel spatial dithering

r_image  = outimage[0::2, 0::2]     # [odd, odd]   -> rows 0,2,4 columns 0,2,4
b_image  = outimage[1::2, 1::2]     # [even, even] -> rows 1,3,5 columns 1,3,5
g0_image = outimage[0::2, 1::2]     # [odd, even]  -> rows 0,2,4 columns 1,3,5
g1_image = outimage[1::2, 0::2]     # [even, odd]  -> rows 1,3,5 columns 0,2,4

# Trim to size and average the g images

r_image = r_image[:oh,:ow]
b_image = b_image[:oh,:ow]
g_image = g0_image[:oh,:ow]//2 + g1_image[:oh,:ow]//2

# Balance the color for this sensor and lighting

r_image = color_balance(r_image)
b_image = color_balance(g_image)
g_image = color_balance(b_image)

# Median filter each color 


# Turn it into unit8

r_image = r_image.astype('uint8')
g_image = g_image.astype('uint8')
b_image = b_image.astype('uint8')

# Stack the color images in RGB order  for output as a color file

rgbimage = np.dstack((r_image, g_image, b_image))

# Save the image as a png file using imageio

imageio.imwrite(outfile, rgbimage, format="PNG-PIL")

# Close the input image file

inlist.close()

exit()


