#!/usr/local/bin/python3

# Inspect the fits header and list an entry for all files in this path
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

if len(sys.argv) != 3:
  print(" ")
  sys.exit("Usage: fits_list_head_entry.py entry directory\n")
  exit()

entry = sys.argv[1]
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
    if entry in prihdr.header:
      imentry = prihdr.header[entry]
      #shortfilename = os.path.splitext(os.path.basename(fullfilename))
      shortfilename = os.path.basename(fullfilename)
      print("File: %s  %s: %s" % (shortfilename, entry, imentry))
        
        



