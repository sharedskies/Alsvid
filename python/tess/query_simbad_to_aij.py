#!/usr/local/bin/python3

"""  

  Obtain the coordinates from an object named on the command line
  Export an AstroImageJ aperture file for an image named on the command line
  
"""  

import os
import sys
import numpy as np
import astropy.io.fits as pyfits
from astropy.wcs import WCS
from time import gmtime, strftime  # for utc
import astropy.units as u
from astropy import coordinates
from astroquery.simbad import Simbad



if len(sys.argv) == 4:
  infile = sys.argv[1]
  objectid = sys.argv[2]
  pixfile = sys.argv[3]
else:
  print(" ")
  print("Usage: query_simbad_to_aij.py infile.fits objectid aij.txt 2>/dev/null ")
  print(" ")
  sys.exit("Convert an object named on the command line to an aij aperture format file\n")

# Take object name from the command line 
# Use the wcs header of an image file for the celestial coordinate conversion parameters
# Calculate and export corresponding pixel coordinates in aij aperture format

# Set this True for verbose output

verboseflag = False

rahr = 0.
ramin = 0.
rasec = 0.
decdeg = 0.
decmin = 0.
decsec = 0.

# Query Simbad
# This will generate an non-trappable error if the object is not found

print("\n")
print("Searching for %s \n" % (objectid,)) 

simbad_table = Simbad.query_object(objectid)

# Try to print the result as an error check

try:
  simbad_table.pprint(show_unit=True)
  print("\n")
except AttributeError:  
  print("No known catalog entry could be found.")
  exit()
  

# Take the first entry 
# This will fail if no object is found in simbad 

idstr = simbad_table['MAIN_ID'][0]
rastr = simbad_table['RA'][0]
decstr = simbad_table['DEC'][0]


# Convert the ra and dec fields into decimal degrees for wcs
# This procedure accepts ra in hours and dec in degrees
# Astroquery table from Simbad is formatted as hh mm: ss.ss and dd mm ss.ss


rahrstr, raminstr, rasecstr = rastr.split(" ")
rahr = abs(float(rahrstr))
ramin = abs(float(raminstr))
rasec = abs(float(rasecstr))
if float(rahrstr) < 0:
  rasign = -1.
else:
  rasign = +1.
ra = rasign*(rahr + ramin/60. + rasec/3600.)*15.
decdegstr, decminstr, decsecstr = decstr.split(" ")
decdeg = abs(float(decdegstr))
decmin = abs(float(decminstr))
decsec = abs(float(decsecstr))
if float(decdegstr) < 0:
  decsign = -1.
else:
  decsign = +1.
dec = decsign*(decdeg + decmin/60. + decsec/3600.)


# Create a sky objects counter and an empty sky objects list

nsky = 0
sky = []


# Add objectid coordinates to the sky list

sky.append((ra, dec))
nsky = nsky + 1


if nsky < 1:
  sys.exit('No objects found at  %s  %s ' % (rastr,decstr,))

# Read the wcs fits reference file and create the reference to the WCS data

inlist = pyfits.open(infile)
inhdr = inlist[0].header
inwcs = WCS(inhdr)

sky_coord = np.array(sky, dtype=np.float32)
pix_coord = inwcs.wcs_world2pix(sky_coord, 1)
      

# Close in the image file
inlist.close()

# Unpack the pix_coord numpy array
npix, nxy = pix_coord.shape

# Test that there are coordinates to write
if npix < 1:
  sysexit("No coordinates found matching targets ")

# Format the aij aperture file

# #AstroImageJ Saved Apertures
# #Sat Jun 22 22:19:34 EDT 2013
# .multiaperture.naperturesmax=500
# .multiaperture.isrefstar=false,false,true,true,true,true
# .multiaperture.xapertures=1473.4099,1580.1968,1539.5604,1593.1986,1511.0461,1547.8082
# .multiaperture.yapertures=1231.65,1272.3362,1156.1813,1132.1183,1280.981,1323.3054

pixfp = open(pixfile, 'w')
  
# Write some useful global parameters that might differ from the defaults
pixfp.write(".multiaperture.naperturesmax=1000\n")

# Write the target or calibration flags for each star in the list
# Here we make them all targets
pixfp.write(".multiaperture.isrefstar=") 
for i in range(npix - 1):
  pixfp.write("false,")
pixfp.write("false\n")

# Write the x apertures in FITS format
pixfp.write(".multiaperture.xapertures=FITS")
for i in range(npix - 1):   
  x = pix_coord[i,0]
  pixline = "%7.2f," % (x,)
  pixfp.write(pixline)
x = pix_coord[npix - 1,0]
pixline = "%7.2f\n" % (x,)
pixfp.write(pixline)

# Write the y apertures in FITS format
pixfp.write(".multiaperture.yapertures=FITS")
for i in range(npix - 1):   
  y = pix_coord[i,1]
  pixline = "%7.2f," % (y,)
  pixfp.write(pixline)
y = pix_coord[npix - 1,1]
pixline = "%7.2f\n" % (y,)
pixfp.write(pixline)

# Close the output file
pixfp.close()

exit()


