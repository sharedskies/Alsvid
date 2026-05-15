#!/usr/local/bin/python3

# Export keywords of all fits files in the current directory to a csv file 

import os
import sys
import fnmatch
import astropy.io.fits as pyfits
import string
import csv

if len(sys.argv) != 2:
  print(" ")
  print("Usage: fits_list_head_to_csv.py dirname ")
  print(" ")
  sys.exit("Export keywords of all fits files in the current directory to a csv file \n")
  
toplevel = sys.argv[-1]


if ( toplevel == './' or toplevel == '.' ):
  outfile = 'index_fits_files.csv'
else:  
  outfile = 'index_fits_files_in_' + toplevel + '.csv'


outfp = open(outfile, 'w')
writer = csv.writer(outfp)
writer.writerow( ('Directory', 'File Name', 'Target', 'Observation Date', 'Exposure Time', 'Filter', 'Telescope', 'Instrument', 'Created Date') )

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
    
    #Parse  primary header elements for the index
    if 'EXPTIME' in prihdr.header:
      imexptime = prihdr.header['EXPTIME']
    else:
      imexptime =  '  ' 
        
    if 'DATE-OBS' in prihdr.header:
      imdateobs = prihdr.header['DATE-OBS']
    else:
      imdateobs = '  '
      
    if 'TARGET'  in prihdr.header:
      imtarget = prihdr.header['TARGET']
    else:
      imtarget = '  '
      
    if 'FILTER' in prihdr.header:
      imfilter = prihdr.header['FILTER']
    else:
      imfilter = '  '
      
    if 'TELESCOP' in prihdr.header:
      imtelescope = prihdr.header['TELESCOP']
    else:
      imtelescope = '  '
      
    if 'INSTRUME' in prihdr.header:
      iminstrument = prihdr.header['INSTRUME']
    else:
      iminstrument = '  '
      
    if 'DATE' in prihdr.header:
      imcreatedate = prihdr.header['DATE']
    else:
      imcreatedate = '  ' 
    
    # Clean up if a full directory name has not been given
                      
    if ( dirname == './' or dirname == '.' ):
      fitsdir = os.getcwd()
    elif  ( dirname[0:2] == './' ):
      fitsdir = dirname[2:]
    elif   ( dirname[0:1] == '.' ): 
      fitsdir = dirname[1:]
    else:
      fitsdir = dirname
        
     
    if  ( filename[0:2] == './' ):
      fitsfile = filename[2:]      
    elif ( filename[0] == '.' ):
      fitsfile = filename[1:]
    else:
      fitsfile = filename
        
       
    # Write a line to the csv file  
       
    writer.writerow( (fitsdir, fitsfile, imtarget, imdateobs, imexptime, imfilter, imtelescope, iminstrument, imcreatedate) )
    
outfp.close()



exit()

