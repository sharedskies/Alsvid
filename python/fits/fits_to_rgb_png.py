#!/usr/local/bin/python3

"""

   Write a linearly scaled color png image from a FITS Bayer masked image file
   
   Input: 
     infile.fits
     outfile.png
     Optional minval and maxval for the scaling to 8 bits
     
   Output:
     Color outfile.png
     
   This version combines the Bayer r, g, and b pixels into a color superpixel
   with r, g, and b colors assigned from the original filtered pixels 
   
   RGB pixel mask is set for the protocol of an Allied Vision Manta cameras 
     

"""

import os
import sys
import numpy as np
import astropy.io.fits as pyfits
import imageio

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_to_rgb_png.py infile.fits outfile.png")
  print("       fits_to_rgb_png.py infile.fits outfile.png minval maxval")
  print(" ")
  sys.exit("Create a linearly scaled png image\n")
elif len(sys.argv) == 3:
  infile = sys.argv[1]
  outfile = sys.argv[2]
  minmaxflag = False
elif len(sys.argv) ==5:
  # Minimum and maximum
  infile = sys.argv[1]
  outfile = sys.argv[2]
  minval = float(sys.argv[3])
  maxval = float(sys.argv[4])
  if minval >= maxval:
    sys.exit("The specified minimum must be less than the maximum\n")
  minmaxflag = True  
else:
  print(" ")
  print("Usage: fits_to_rgb_png.py infile.fits outfile.png")
  print("       fits_to_rgb_png.py infile.fits outfile.png minval maxval")
  print(" ")
  sys.exit("Create a linearly scaled png image\n")
  
# Open the fits file and create an hdulist

inlist = pyfits.open(infile) 

# Assign image data to a numpy array

inimage =  inlist[0].data.astype('float32')

print('Image size: ', inimage.size)
print('Image shape: ', inimage.shape)

# Scale the image data linearly
if minmaxflag:
  pass
else:  
  minval = float(np.min(inimage))
  maxval = float(np.max(inimage))

delta = maxval - minval
newimage = 255.0*(inimage - minval)/(delta)
newimage[newimage > 255.] = 255.
newimage[newimage < 0.] = 0.


# Convert the RGB values from the masked image pixels to separate images
# Set the size of the output image noting for FITS images here
#   Width of the image is spanned by the second index
#   Height of the image is spanned by the first index

outimage = newimage
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


