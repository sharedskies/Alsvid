#!/usr/local/bin/python3

# Photometry on a fits image file 
# Accepts input list of pixel or ds9 coordinates
# Requires an image with a WCS header
# Returns a file with photometry and RA, Dec coordinates

# Aperture photometry with the AstroIJ algorithm

# Changelog
#
#   2014-12-08  Included in Alsvid 3.5 based on pywcs
#   2017-05-01  Modified for astropy
#   2018-11-18  Coordinate extraction version in Alsvid 5.5

import os
import sys
import math as ma
import numpy as np
import astropy.io.fits as pyfits
from astropy.wcs import WCS
from time import gmtime, strftime  # for utc


def hms(hours):

  # Format floating point hours into a hh:mm:ss.sss string

  hr = int(hours)
  subhours = abs( hours - float(hr) )
  minutes = subhours * 60.
  mn = int(minutes)
  subminutes = abs( minutes - float(mn) )
  seconds = subminutes * 60.
  ss = int(seconds)
  subseconds = abs( seconds - float(ss) )
  subsecstr = ("%.3f" % (subseconds,)).lstrip('0')
  timestr = "%02d:%02d:%02d%s" % (hr, mn, ss, subsecstr) 
  return timestr


def dms(degrees):
  
  # Format floating point degrees into a +/-dd:mm:ss.sss string
  
  dg = int(abs(degrees))
  subdegrees = abs( abs(degrees) - float(dg) )
  minutes = subdegrees * 60.
  mn = int(minutes)
  subminutes = abs( minutes - float(mn))
  seconds = subminutes * 60.
  ss = int(seconds)
  subseconds = abs( seconds - float(ss) )
  subsecstr = ("%.3f" % (subseconds,)).lstrip('0')
  if degrees > 0:
    dsign = '+'
  elif degrees == 0.0:
    dsign = ' '
  else:
    dsign = '-'
  anglestr = "%s%02d:%02d:%02d%s" % (dsign, dg, mn, ss, subsecstr) 
  return anglestr


def apphot(scidata, px, py, r0, r1, r2):

  # AIJ or ds9 floating point pixel coordinates (px,py) indexed from 1.0
  # Photometry aperture r0
  # Photometry inner radius r1
  # Photometry outer radius r2
  # Finds the signal inside the inner radius centered at  (px,py)
  # Subtracts a background from the outer annulus with outlier removal
  # The numpy array scidata is a fits image in the usual flipped numpy format

  # Calculate squares once
  
  r02 = r0*r0
  r12 = r1*r1
  r22 = r2*r2
  
  # What are the image limits inside the outer annulus
  
  ny, nx = scidata.shape
  
  pxmin = max(1,  int(px - r2))
  pxmax = min(nx, int(px + r2))
  pymin = max(1,  int(py - r2))
  pymax = min(ny, int(py + r2))
  
  # Initialize sums in the aperture and in the annulus
    
  sum_ap = 0.0
  sum_an = 0.0
  sum_an2 = 0.0
  
  # Initialize pixel counts in aperture and in annulus
  
  count_ap = 0
  count_an = 0

  # Find totals inside aperture and annulus
  # Note numpy image array scidata has first index y, second x 
  
  for j in range(pxmin, pxmax + 1):
    for k in range(pymin, pymax + 1):
      dpx = (j - px)
      dpy = (k - py)
      dp2 = dpx*dpx + dpy*dpy
      pixval = scidata[k-1, j-1]
      if dp2 < r02:
        sum_ap = sum_ap + pixval
        count_ap = count_ap + 1
      elif dp2 >= r12 and dp2 <= r22:
        sum_an = sum_an + pixval
        sum_an2 = sum_an2 + pixval*pixval
        count_an = count_an + 1

  # When there are no pixels this prevents a divide by zero error
  
  count_ap = max(1, count_ap)
  count_an = max(1, count_an)

  # Determine average values in the annulus
  
  average_an = sum_an/float(count_an)
  average_an2 = sum_an2/float(count_an)
  
  # Estimate the standard deviation for the annulus
    
  sigma_an = ma.sqrt(abs(average_an2 - average_an*average_an))

  # Make several more passes to exclude outliers in the annulus
  
  npasses = 10
  
  for i in range (npasses):
    sum_an = 0.0
    sum_an2 = 0.0
    count_an = 0
    for j in range(pxmin, pxmax + 1):
      for k in range(pymin, pymax + 1):
        dpx = (j - px)
        dpy = (k - py)
        dp2 = dpx*dpx + dpy*dpy
        pixval = scidata[k-1, j-1] 
        if dp2 >= r12 and dp2 <= r22 and abs(pixval - average_an) <= 2.*sigma_an:
          sum_an = sum_an + pixval
          sum_an2 = sum_an2 + pixval*pixval
          count_an = count_an + 1  
    count_an = max(1, count_an)
    average_an = sum_an/float(count_an)
    average_an2 = sum_an2/float(count_an)
    sigma_an = ma.sqrt(abs(average_an2 - average_an*average_an))

  # Calculate target signal - background and return
  
  signal  = sum_ap - float(count_ap)*average_an
  
  return signal


# Main code begins here


if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_wcs_photometry.py r_aperture r_inner r_outer infile_wcs.fits skycoords.txt photdata.txt  ")
  print(" ")
  print("Based on aperture photometry algorithm used by AstroImageJ without automatic centroid")
  print("Input coordinates line by line text, or ds9 circle or box formats")
  print(" ") 
  sys.exit("Aperture photometry on an input fits image with WCS header\n")
elif len(sys.argv) == 7:
  rphot = float(sys.argv[1])
  rinner = float(sys.argv[2])
  router = float(sys.argv[3])
  infile = sys.argv[4]
  skyfile = sys.argv[5]
  photfile = sys.argv[6]
else:
  print(" ")
  print("Usage: fits_wcs_photometry.py r_aperture r_inner r_outer infile_wcs.fits skycoords.txt photdata.txt  ")
  print(" ")
  print("Based on aperture photometry algorithm used by AstroImageJ without automatic centroid")
  print("Input locations in space or comma deliminated line by line text, or ds9 circle or box formats")
  print(" ")   
  sys.exit("Aperture photometry on input fits image with WCS header\n")
  
# Take sky coordinates a plain text file or from a ds9 regions file
# Use the wcs header of an image file for the celestial coordinate conversion parameters
# Calculate photometry and export data with celestial coordinates

# Set this True for decimal instead of hh:mm:ss.sss +/-dd:mm:ss.sss output

decimalflag = False

# Set this True for verbose output

verboseflag = False

# Open the file with coordinates
skyfp = open(skyfile, 'r')

# Read all the lines into a list
skytext = skyfp.readlines()

# Close the pixel file
skyfp.close()

# Create an sky objects counter and an empty sky objects list
i = 0
sky = []

# Split sky text and parse into ra and dec strings  
# We try various formats looking for one with a valid entry and take the first one we find
# This searches ds9 box and circle regions, comma separated, and space separated

# Region in ds9 shows a string in hr:min:sec and deg:min:sec but wcs requires both in decimal degrees

for line in skytext:

  if 'circle' in line:
    # Treat the case of a ds9 circle region
    
    # Remove the leading circle( descriptor
    line = line.replace("circle(", '')

    # Remove the trailing )
    line = line.replace(")", '')

    # Remove the trailing \n and split into text fields
    entry = line.strip().split(",")
    rastr = entry[0]
    decstr = entry[1]
    rahrstr, raminstr, rasecstr = rastr.split(":")
    decdegstr, decminstr, decsecstr = decstr.split(":")
     
    # Convert the text fields into decimal degrees for wcs
    rahr = abs(float(rahrstr))
    ramin = abs(float(raminstr))
    rasec = abs(float(rasecstr))
    if float(rahrstr) < 0:
      rasign = -1.
    else:
      rasign = +1.
          
    decdeg = abs(float(decdegstr))
    decmin = abs(float(decminstr))
    decsec = abs(float(decsecstr))
    if float(decdegstr) < 0:
      decsign = -1.
    else:
      decsign = +1.
   
    ra = rasign*(rahr + ramin/60. + rasec/3600.)*15.
    dec = decsign*(decdeg + decmin/60. + decsec/3600.)

    # Append to the sky list and update the counter
    sky.append((ra, dec))
    i = i + 1

  elif 'box' in line:
    # Treat the case of a ds9 box region
    
    # Remove the leading box( descriptor
    line = line.replace("box(", '')

    # Remove the trailing )
    line = line.replace(")", '')

    # Remove the trailing \n and split into text fields
    entry = line.strip().split(",")
    rastr = entry[0]
    decstr = entry[1]
    rahrstr, raminstr, rasecstr = rastr.split(":")
    decdegstr, decminstr, decsecstr = decstr.split(":")
     
    # Convert the text fields into decimal degrees for wcs
    rahr = abs(float(rahrstr))
    ramin = abs(float(raminstr))
    rasec = abs(float(rasecstr))
    if float(rahrstr) < 0:
      rasign = -1.
    else:
      rasign = +1.
          
    decdeg = abs(float(decdegstr))
    decmin = abs(float(decminstr))
    decsec = abs(float(decsecstr))
    if float(decdegstr) < 0:
      decsign = -1.
    else:
      decsign = +1.
   
    ra = rasign*(rahr + ramin/60. + rasec/3600.)*15.
    dec = decsign*(decdeg + decmin/60. + decsec/3600.)

    # Append to the sky list and update the counter
    sky.append((ra, dec))
    i = i + 1
       
  elif ':' in line:

    # Try to remove the trailing \n and split into text fields depending on separator
    
    try:    
      # Treat the case of a plain text comma separated entry      
      entry = line.strip().split(",")  
      # Get the x,y values for these fields
      rastr = entry[0]
      decstr = entry[1]
      rahrstr, raminstr, rasecstr = rastr.split(":")
      decdegstr, decminstr, decsecstr = decstr.split(":")
     
      # Convert the text fields into decimal degrees for wcs
      rahr = abs(float(rahrstr))
      ramin = abs(float(raminstr))
      rasec = abs(float(rasecstr))
      if float(rahrstr) < 0:
        rasign = -1.
      else:
        rasign = +1.
          
      decdeg = abs(float(decdegstr))
      decmin = abs(float(decminstr))
      decsec = abs(float(decsecstr))
      if float(decdegstr) < 0:
        decsign = -1.
      else:
        decsign = +1.
   
      ra = rasign*(rahr + ramin/60. + rasec/3600.)*15.
      dec = decsign*(decdeg + decmin/60. + decsec/3600.)
      
      sky.append((ra, dec))
      i = i + 1    

    except:      
      
      try: 
        # Treat the case of plane text entries separated by blank space
        entry = line.strip().split()
        rastr = entry[0]
        decstr = entry[1]
        rahrstr, raminstr, rasecstr = rastr.split(":")
        decdegstr, decminstr, decsecstr = decstr.split(":")
         
        # Convert the text fields into decimal degrees for wcs
        rahr = abs(float(rahrstr))
        ramin = abs(float(raminstr))
        rasec = abs(float(rasecstr))
        if float(rahrstr) < 0:
          rasign = -1.
        else:
          rasign = +1.
              
        decdeg = abs(float(decdegstr))
        decmin = abs(float(decminstr))
        decsec = abs(float(decsecstr))
        if float(decdegstr) < 0:
          decsign = -1.
        else:
          decsign = +1.
       
        ra = rasign*(rahr + ramin/60. + rasec/3600.)*15.
        dec = decsign*(decdeg + decmin/60. + decsec/3600.)

        sky.append((ra, dec))
        i = i + 1    
           
      except:
        pass
        

  else:
    # Treat the cases of plain text sky coordinates assuming decimal ra hours and dec degrees
    # Try to remove the trailing \n and split into text fields
    
    try:    
      # Treat the case of a plain text comma separated entry      
      entry = line.strip().split(",")  
      # Get the x,y values for these fields
      ra = 15.*float(entry[0])
      dec = float(entry[1])
      sky.append((ra, dec))
      i = i + 1    
    except:      
      
      try: 
        # Treat the case of a plane text blank space separated entry
        entry = line.strip().split()
        ra = 15.*float(entry[0])
        dec = float(entry[1])
        sky.append((ra, dec))
        i = i + 1    
           
      except:
        pass
        

      
# How many sky objects found?

nsky = i
if nsky < 1:
  sys.exit('No objects found in %s' % (coordsfile,))
  

  

# Read the FITS image file

inlist = pyfits.open(infile)
inhdr = inlist[0].header
indata = inlist[0].data.astype('float32')

# Create a wcs object from this header

inwcs = WCS(inhdr)

# Conversion is based on "1" pixel origin used in ds9 and aij
# Original version used http://stsdas.stsci.edu/astrolib/pywcs/examples.html
# Astropy version uses https://python4astronomers.github.io/astropy/wcs.html
# Convert sky list to numpy floating point array

sky_coord = np.array(sky, dtype=np.float32)
pix_coord = inwcs.wcs_world2pix(sky_coord, 1)

# Close in the image file
inlist.close()

# Unpack the sky_coord numpy array
nsky, nradec  =  sky_coord.shape

# Test that there are coordinates to write
if nsky < 1:
  sysexit("No coordinates found. ")

# Open the output file for appending 
photfp = open(photfile, 'a')

if decimalflag: 
  for i in range(nsky):
    ra = sky_coord[i,0] / 15.
    dec = sky_coord[i,1]
    x = pix_coord[i,0]
    y = pix_coord[i,1]
    phot = apphot(indata, x, y, rphot, rinner, router)
    if verboseflag:
      print(ra, dec)
    photline = "%5.2f  %5.2f  %f  %f  %f \n" % (x, y, ra, dec, phot)   
    photfp.write(photline)
else:
  for i in range(nsky):
    ra = sky_coord[i,0] / 15.
    dec = sky_coord[i,1]
    x = pix_coord[i,0]
    y = pix_coord[i,1]
    phot = apphot(indata, x, y, rphot, rinner, router)    
    if verboseflag:
      print(hms(ra), dms(dec))
    photline = "%5.2f  %5.2f  %s  %s  %f \n" % (x, y, hms(ra), dms(dec), phot)
    photfp.write(photline)

# Close the output file
photfp.close()

exit()

