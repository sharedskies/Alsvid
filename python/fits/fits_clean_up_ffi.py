#!/usr/local/bin/python3

# Identify empty files
# Inspect the first extended header data quality flag
# Move flagged files to separate directories 
#
# Copyright 2019 John Kielkopf and Karen Collins
#
#

import os
import sys
import fnmatch
import astropy.io.fits as pyfits
import numpy as np
import string
import shutil

if len(sys.argv) != 1:
  print(" ")
  sys.exit("Usage: fits_clean_up_ffi.py\n")
  exit()

# Set defaults for data quality selection

entry = "DQUALITY"
badflag = 32
goodflag = 0

# Set directories or create them if they do not exist

toplevel = "./"
baddir = "../bad"
emptydir = "../empty"
cwdpath = os.getcwd()

badpath = os.path.join(cwdpath, baddir)
if not os.path.exists(badpath):
    os.mkdir(baddir)

emptypath = os.path.join(cwdpath, emptydir)
if not os.path.exists(emptypath):
    os.mkdir(emptydir)   

# Search for files with this extension
pattern = '*.fits'

filenames = [f for f in os.listdir(cwdpath) if os.path.isfile(os.path.join(cwdpath, f))]
filenames = fnmatch.filter(filenames, pattern)


# Run through all the filenames in a single loop (allows simple break)
# Move empty files to another directory
# Move detected bad files to another directory

for filename in filenames:
    
  fullfilename = os.path.join(cwdpath, filename)
  try:    
  
    # Open a fits image file
    inlist = pyfits.open(fullfilename)
    
  except IOError: 
    shortfilename = os.path.basename(fullfilename)
    emptypathname = os.path.join(emptypath,shortfilename)
    print("File: %s  %s: %s" % (shortfilename, entry, "Cannot open"))       
    inlist.close()
    os.rename(fullfilename, emptypathname)
    continue   

  # Get the first extended header
  # If there is none, go on to the next file

  try:
    inxhdr = inlist[1].header
  except:
    inlist.close()
    continue  
  
  # Parse first extended header for the entry
  # Decide what to do with the file

  if entry in inxhdr:             
    imentry = inxhdr[entry]
    if imentry != goodflag:
    
      # Sort all files with non-zero DQUALITY to another directory
      shortfilename = os.path.basename(fullfilename)
      badpathname = os.path.join(badpath,shortfilename)
      print("File: %s  %s: %s" % (shortfilename, entry, imentry))
      inlist.close()
      os.rename(fullfilename, badpathname)
      continue

    inlist.close()

print("Finished cleaning FFIs")
print("Empty FFIs are in %s" % (emptydir,) )
print("Low quality FFIs are in %s" % (baddir,) ) 

exit()
    


