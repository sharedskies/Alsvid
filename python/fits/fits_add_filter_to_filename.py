#!/usr/local/bin/python3

# Inspect the fits header and add the filter to the filename
#
# Copyright 2012-2019 John Kielkopf
#
#

import os
import sys
import fnmatch
import astropy.io.fits as pyfits
import string
import subprocess

nofile      = "  "

if len(sys.argv) != 1:
  print(" ")
  sys.exit("Usage: add_filter_to_fitsname.py \n")
  exit()


toplevel = './'

# Search for files with this extension
pattern = '*.fits'

for dirname, dirnames, filenames in os.walk(toplevel):
  for filename in fnmatch.filter(filenames, pattern):
    fullfilename = os.path.join(dirname, filename)
    
    try:    
    
      # Open a fits image file
      hdulist = pyfits.open(fullfilename)
      
    except IOError: 
      print ('Error opening ', fullfilename)
      break       
    

    # Get the primary image header
    prihdr = hdulist[0]
    
    #Parse  primary header elements and set flags

    filtername = ""             
    if 'FILTER' in prihdr.header:
      imfilter = prihdr.header['FILTER']
      if "g_" in imfilter:
        filtername="g"

      if "r_" in imfilter:
        filtername="r"

      if "i_" in imfilter:
        filtername="i"

      if "z_" in imfilter:
        filtername="z"

      if "bb_" in imfilter:
        filtername="bb"

      if "U_" in imfilter:
        filtername="U"

      if "B_" in imfilter:
        filtername="B"

      if "V_" in imfilter:
        filtername="V"

      if "R_" in imfilter:
        filtername="R"

      if "I_" in imfilter:
        filtername="I"

      if "Halpha_" in imfilter:
        filtername="ha"


      if "og_" in imfilter:
        filtername="og"

      if "open" in imfilter:
        filtername="o"

          
    # Act on values of the flags in the header      
                
    print ('  File:      ', filename)
    print ('  Filter:    ', filtername)
        
    print (' Processing ... ')
    infilename = fullfilename
    if  'dark' in filename:
      pass
    elif 'bias' in filename:
      pass
    elif filtername !="":
      basename = os.path.splitext(os.path.basename(infilename))[0]
      firstname, lastname = basename.split("_")
      newfilename = firstname+'_'+filtername+'_'+lastname+'.fits'
      subprocess.call(["mv", infilename,  newfilename]) 
      print(infilename, "renamed", newfilename)
        
        

exit()


