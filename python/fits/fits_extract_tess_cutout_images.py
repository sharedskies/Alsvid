#!/usr/local/bin/python3

"""

  Extract all images from a TESS pixel BINTABLE file
  Removes extended headers
  Selects only the image data
  Detects and does not convert low quality

"""

import os
import sys
import numpy as np
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc

if len(sys.argv) != 3:
  print(" ")
  print("Usage: fits_extract_tess_cutout_images.py cutout_infile.fits outprefix ")
  print(" ")
  sys.exit("Extract cutout images from a  TESS pixel bintable cutout file\n")

infile = sys.argv[1]
outprefix = sys.argv[2]


# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwriteflag = True  
  
# Open the fits file readonly by default and create an input hdulist

inlist = pyfits.open(infile) 

# Assign the input headers 

# Master

inhdr0 = inlist[0].header

# Sector information including range of dates
# For more information inspect the entries in inhdr1
# Is there a DQUALITY flag?

inhdr1 = inlist[1].header

# Coordinates

inhdr2 = inlist[2].header  

# Create a new fits header for the pixel file images

newhdr = inhdr2

# Clear the instrument and telescope keywords 
# AIJ may use them in development software that could break processing

del newhdr['INSTRUME']
del newhdr['TELESCOP']
del newhdr['CHECKSUM']

# Clear the extension name which will not apply to the cutout slices

del newhdr['EXTNAME']

imagedata = inlist[1].data
nimages = np.size(imagedata)

# Diagnostics

# print(np.size(imagedata))
# print(len(imagedata[0]))


for i in range(nimages):
      
  # Get image data
  
  inimage =  imagedata[i][4]
  
  # Get BJD -2457000
  
  bjd0 = 2457000.
  bjd1 = imagedata[i][0]
  quality_flag = imagedata[i][8]
  tess_ffi = imagedata[i][11]
  
  if np.isnan(bjd1):
    print ('Image ', i, 'skipped: lacks valid BJD timestamp.')
   
  elif   quality_flag != 0: 
    print ('Image ', i, 'skipped: poor quality.')

  else:
    bjd = bjd0 + bjd1
    outimage = inimage
    
    # Create the fits object for this image using the header of the bintable image
    # Use float32 for output type
    
    outlist = pyfits.PrimaryHDU(outimage.astype('float32'),newhdr)
    
    # Provide a new date stamp
    
    file_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    
    
    # Update the header
    # Append data to the header from the other header blocks of the bintable file
    
    outhdr = outlist.header
    outhdr['DATE'] = file_time
    outhdr['BJD_TDB'] = bjd
    outhdr['COMMENT'] = tess_ffi
    outhdr['history'] = 'Image from '+  infile
    
    # Write the fits file
    
    outfile = outprefix + '_%05d.fits' % (i,)
    outlist.writeto(outfile, overwrite = overwriteflag)  


# Close the input  and exit

inlist.close()
exit()

