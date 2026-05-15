#!/usr/local/bin/python3

"""

  Simplify TESS FFI images in this directory
  Remove extended headers
  Select only the image data

"""

import os
import sys
import fnmatch
import numpy as np
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc

if len(sys.argv) != 1:
  print(" ")
  print("Usage: fits_ffi_to_simple_images.py ")
  print(" ")
  print("Exract the science image from TESS pixel bintable files.\n")
  print("Annotate the file header.\n")
  print("Serially number output files.\n")
  sys.exit("\n")


# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwriteflag = True  
  

toplevel = './'

# Search for files with this extension
pattern = '*.fits'
i = 0

for dirname, dirnames, filenames in os.walk(toplevel):
  for filename in fnmatch.filter(filenames, pattern):
    fullfilename = os.path.join(dirname, filename)
    
    try:    
    
      # Open a fits image file
      inlist = pyfits.open(fullfilename)
      
    except IOError: 
      print('Error opening ', fullfilename)
      break       
    
    # Assign the input headers 

    # Master

    inhdr0 = inlist[0].header

    # Sector information including range of dates
    # For more information inspect the entries in inhdr1

    inhdr1 = inlist[1].header

    # Coordinates

    inhdr2 = inlist[2].header  

    # Create a new fits header for the pixel file images

    newhdr = inhdr1

    # Clear the instrument and telescope keywords so AIJ
    #   will not try to overwrite the BJD from the data slice

    del newhdr['INSTRUME']
    del newhdr['TELESCOP']
    del newhdr['CHECKSUM']
      
    # Final program will loop through all the images
      
    # Get image data
    
    inimage =  inlist[1].data
    
      
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
    outhdr['history'] = 'Image from '+  filename
    
    # Write the fits file
    
    basename = os.path.splitext(os.path.basename(fullfilename))[0]
    outfile = basename + '_simple_%05d.fits' % (i,)
    outlist.writeto(outfile, overwrite = overwriteflag)  
    i = i + 1

    # Close the input  and exit

    inlist.close()
    
exit()    
