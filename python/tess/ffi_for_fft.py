#!/usr/local/bin/python3

"""

  Prepare a set of TESS FFI images for an FFT of an image stack
  Select images from a directory
  Insert copies of an image for missing frames
  Create a serially numbered image stack in a new directory

"""

import os
import sys
import fnmatch
import shutil
import astropy.io.fits as pyfits
import numpy as np
import string
import time
import datetime

# Allowed accumulated cadence missteps in seconds
terror = 2.

# Turn on for additional run-time messages
diagnostics_flag = False

if len(sys.argv) != 6:
  print(" ")
  print("Usage: ffi_for_fft.py pattern sourcedir basename targetdir number")
  print(" ")
  exit()

pattern = sys.argv[1]
pattern = '*' + pattern + '*.fits'
sourcedir = sys.argv[2]
basename = sys.argv[3]
targetdir = sys.argv[4]
nout = int(sys.argv[5])
cwd = os.getcwd()

sourcepath = os.path.join(cwd, sourcedir)
targetpath = os.path.join(cwd, targetdir)

if (nout != 1024):
  print("It is best to select 1024 images for optimal performance.\n")
  
# Check directories

if not os.path.exists(sourcepath):
  print("Source directory ", sourcedir, " cannot be found.")
  exit()
  
if not os.path.exists(targetpath):
  print("Target directory ", targetdir, " was not found.")
  print("Creating target directory.")
  os.mkdir(targetdir)


filenames = [f for f in os.listdir(sourcedir) if os.path.isfile(os.path.join(sourcedir, f))]
filenames = fnmatch.filter(filenames, pattern)
 
# Run through all filenames in a single loop
# We assume that files are serially ordered by name such that the internal times are also ordered

# Set a file number counter
nfiles = 0

# Define and set an initial cadence
cadence = 1800.

for filename in filenames:

  # Run this until we have written nfiles
  # The number written is increased at the end of the loop
  
  if nfiles >= nout:
    break

  try:    
  
    # Open a fits image file
    hdulist = pyfits.open(filename)
                                                                             
  except IOError: 
    print('Error opening ', filename)
    break       
  
  # Get the primary image header
  prihdr = hdulist[0]
  
  # Parse  primary header for date and time of observation
  # Allow for headers that do not have Z in the timestamp


  if 'DATE-OBS' in prihdr.header:
    utcdate = prihdr.header['DATE-OBS']
    len_date = len(utcdate)
    utcdate[len_date - 1]
    if utcdate[len_date - 1] is "Z":
      timestamp = datetime.datetime.strptime(utcdate, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()
    else:
      timestamp = datetime.datetime.strptime(utcdate, "%Y-%m-%dT%H:%M:%S.%f").timestamp()
    if nfiles == 0:
      timestamp0 = timestamp 
  else:
    print("DATE-OBS must be in the primary header of all images.")
    break

  
  # Find the cadence for this image stack based on the first two frames
  
  if nfiles == 1:
    cadence = timestamp - timestamp0
    print("Found cadence: ", cadence, " seconds")  
  
  # How many files to write?
  
  nwrite = 1
  
  if nfiles > 1:
  
    # Check for missing files in the stack
    # This is only possible after the first two files set the cadence
    # At this step nfiles is the number of files already written
    # This one is nfiles + 1
  
    tdiff = (timestamp - timestamp0) - (nfiles - 1)*cadence 
    nwrite = int( (tdiff + terror) / cadence )    
  
  # Write more indexed files into the target directory
  
  if diagnostics_flag:  
    print("Writing ", nwrite, " copies of ", filename)
  
  for i in range(0, nwrite):
    outname = basename + '_%05d.fits' % (nfiles,)
    outfilename = os.path.join(targetpath, outname)
    shutil.copyfile(filename, outfilename)
    nfiles = nfiles + 1
  
    
exit()
    
     
             
