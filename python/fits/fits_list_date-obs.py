#!/usr/local/bin/python3

# Inspect the fits header and list the date of observation
#
# Copyright 2018 John Kielkopf
#
#

import os
import sys
import fnmatch
import astropy.io.fits as pyfits
import string
import subprocess

nofile      = "  "

if len(sys.argv) != 2:
  print(" ")
  sys.exit("Usage: fits_list_date-obs.py directory\n")
  exit()


toplevel = sys.argv[-1]

# Search for files with this extension
pattern = '*.fits'

for dirname, dirnames, filenames in os.walk(toplevel):
  for filename in fnmatch.filter(filenames, pattern):
    fullfilename = os.path.join(dirname, filename)
    
    try:    
    
      # Open a fits image file
      hdulist = pyfits.open(fullfilename)
      
    except IOError: 
      print('Error opening ', fullfilename)
      break       
    

    # Get the primary image header
    prihdr = hdulist[0]
    
    #Parse  primary header elements and set flags

    ccdfilter = 0 
    filtername = ""             
    if 'DATE-OBS' in prihdr.header:
      imdateobs = prihdr.header['DATE-OBS']
      #shortfilename = os.path.splitext(os.path.basename(fullfilename))
      shortfilename = os.path.basename(fullfilename)
      print("File: %s  Date of observation: %s" % (shortfilename, imdateobs))
        
        



