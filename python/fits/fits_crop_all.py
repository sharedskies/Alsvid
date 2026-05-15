#!/usr/local/bin/python3

# Crop all fits images in a directory
# Uses numpy processing to crop an image
# Other methods could use astropy helper routines
# Caution urged when WCS is in the header 
# This version uses astropy WCS to modify the crop file header

import os
import sys
import fnmatch
import numpy as np
import astropy.io.fits as pyfits
import astropy.wcs as pywcs

from time import gmtime, strftime  # for utc

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_crop_all.py  x y m n dir")
  print(" ")
  sys.exit("Crops fits files to m x n starting at x y\n")
elif len(sys.argv) == 6:
  xstart = int(float(sys.argv[1]))
  ystart = int(float(sys.argv[2]))
  m = int(float(sys.argv[3]))
  n = int(float(sys.argv[4]))
  indir = sys.argv[5]
else:
  print(" ")
  print("Usage: fits_crop_all.py  x y m n dir")
  print(" ")
  print("Crops fits files to m x n starting at x y\n")
  print("The sizes  m and n must be integers less than the size of the fits file\n")
  sys.exit("The starting location coordinates must be integers  indexed from 1 in the lower left\n")

toplevel = sys.argv[-1]

# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwriteflag = False  


# Search for files with this extension
pattern = '*.fits'

for dirname, dirnames, filenames in os.walk(toplevel):
  for filename in fnmatch.filter(filenames, pattern):
    fullfilename = os.path.join(dirname, filename)
    
    try:    
    
      # Open the fits file readonly by default and create an input hdulist
      inlist = pyfits.open(fullfilename)
      
    except IOError: 
      print('Error opening ', fullfilename)
      break       

  
    # Assign the input header 

    inhdr = inlist[0].header

    # Assign image data to numpy array of the same type and get its size

    inimage =  inlist[0].data.astype('float32')
    xsize, ysize = inimage.shape

    if ( m > xsize or n > ysize ):
      print("The image you are cropping is %d x %d and too small for the request.\n")
      inlist.close()
      exit()


    if ( xstart  > xsize or ystart > ysize ):
      print("The crop requested starts outside the source array.\n")
      inlist.close()
      exit()

     
    # Set bounds for subarray to be extracted
    # Indices are zero-based but input image coordinates start at one
    # Use x and y  for image coordinates and [j,i] for corresponding numpy coordinates
    # Numpy array first index is image y, second index is image j

    i0 = xstart - 1 
    i1 = i0 + m - 1
    j0 = ystart - 1 
    j1 = j0 + n - 1


    # Test bounds, warn user, and adjust to avoid failure

    if (i0 < 0):
      print("The lower x bound is outside the array.  Setting coordinate to 1.\n")
      i0 = 0
    if (i1 > (xsize - 1)):
      print("The upper x bound is outside the array.  Setting coordinate to %d .\n", xsize)
      i1 = xsize - 1
    if (j0 < 0):
      print("The lower y bound is outside the array.  Setting  coordinate to 1.\n")
      j0 = 0
    if (j1 > (ysize - 1)):
      print("The upper y bound is outside the array.  Setting coordinate to %d .\n", ysize)
      j1 = ysize - 1  


    # Copy data from original image noting numpy arrays have y as the first index

    outimage = np.copy(inimage[j0:j1+1,i0:i1+1])

    # Provide a new date stamp

    file_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

    # Create the fits ojbect for this image using the header of the first image

    outlist = pyfits.PrimaryHDU(outimage.astype('float32'),inhdr)

    # Update the header

    inwcs = pywcs.WCS(inhdr)
    outhdr = outlist.header
    outhdr.update(inwcs[j0:j1+1,i0:i1+1].to_header())
    outhdr['DATE'] = file_time
    outhdr['history'] = 'Image cropped by fits_crop'
    outhdr['history'] = 'WCS updated for new size'
    outhdr['history'] = 'Source image file '+  filename

    # Write the fits file
  
    outfile = os.path.splitext(os.path.basename(fullfilename))[0]+'_c.fits'
  
    try:
      outlist.writeto(outfile, overwrite = overwriteflag)
    except:
      print("Your output file may already exist and will not be written.\n")
      

    # Close the input  and exit

    inlist.close()

exit()
