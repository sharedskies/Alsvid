#!/usr/local/bin/python3

# Inspect the fits primary header and first extended header for an entry for all files in this path
#
# Copyright 2019 John Kielkopf
#
#

import os
import sys
import fnmatch
import astropy.io.fits as pyfits
import numpy as np
import string
import subprocess

nofile      = "  "

if len(sys.argv) != 3:
  print(" ")
  sys.exit("Usage: fits_list_xhead_entry.py entry directory\n")
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
      inlist = pyfits.open(fullfilename)
      
    except IOError: 
      shortfilename = os.path.basename(fullfilename)
      print("File: %s  %s: %s" % (shortfilename, entry, "Cannot open")) 
      break       
    

    # Get the primary image header
    inhdr = inlist[0].header
        
    #Parse  primary header for the entry

    if entry in inhdr:
      imentry = inhdr[entry]
      shortfilename = os.path.basename(fullfilename)
      print("File: %s  %s: %s" % (shortfilename, entry, imentry))

    # Get the first extended header
    # If there is none, go on to the next file

    try:
      inxhdr = inlist[1].header
    except:
      inlist.close()
      break
    
    #Parse first extended header for the entry

    if entry in inxhdr:             
      imentry = inxhdr[entry]
      shortfilename = os.path.basename(fullfilename)
      print("File: %s  %s: %s" % (shortfilename, entry, imentry))

    inlist.close()

exit()
    


