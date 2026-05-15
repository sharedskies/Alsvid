#!/usr/local/bin/python3

# Extract all images from a TESS pixel BINTABLE file

import os
import sys
import numpy as np
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc

if len(sys.argv) != 3:
  print(" ")
  print("Usage: fits_extract_tp_image.py tp_infile.fits outprefix ")
  print(" ")
  sys.exit("Extract all images from a  TESS pixel bintable file\n")

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

inhdr1 = inlist[1].header

# Coordinates

inhdr2 = inlist[2].header  

# Cosmic rays

inhdr3 = inlist[3].header

ticobject = inhdr1['OBJECT']
ticid = inhdr1['TICID']
nimages = inhdr1['NAXIS2']

# Create a new fits header for the pixel file images

newhdr = inhdr2

# Clear the instrument and telescope keywords 
# AIJ may use them in development software that could break processing

del newhdr['INSTRUME']
del newhdr['TELESCOP']
del newhdr['CHECKSUM']

for i in range(nimages):
  
  # Final program will loop through all the images
    
  # Get image data
  
  inimage =  inlist[1].data[i][4]
  
  # Get BJD -2457000
  
  bjd0 = 2457000.
  bjd1 = inlist[1].data[i][0]
  
  if np.isnan(bjd1):
    print ('Image ', i, 'skipped: lacks valid BJD timestamp.')

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
    outhdr['OBJECT'] = ticobject
    outhdr['BJD_TDB'] = bjd
    outhdr['history'] = 'Image from '+  infile
    
    # Write the fits file
    
    outfile = outprefix + '_%011d_%05d.fits' % (ticid,i)
    outlist.writeto(outfile, overwrite = overwriteflag)  


# Close the input  and exit

inlist.close()
exit()

