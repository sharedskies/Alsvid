#!/usr/local/bin/python3

""" 

  Query the MAST database for a TESS Input Catalog star 
  Convert to aij aperture format

"""

import os
import sys
import numpy as np
import astropy.io.fits as pyfits
from astropy.wcs import WCS
from time import gmtime, strftime  # for utc
import astropy.units as u
from astropy import coordinates
from astroquery.mast import Catalogs



if len(sys.argv) == 5:
  infile = sys.argv[1]
  rastr = sys.argv[2]
  decstr = sys.argv[3]
  pixfile = sys.argv[4]
else:
  print(" ")
  print("Usage: query_tic_to_aij.py infile.fits ra dec aij.txt")
  print(" ")
  sys.exit("Search a 2.5 arcminute field for TIC stars and generate an aij aperture file\n")

# Takes coordinates from the command line 
# Use the wcs header of an image file for the celestial coordinate conversion parameters
# Calculate and export corresponding pixel coordinates in aij aperture format


# Set this True for verbose output of the TESS TIC stars
verboseflag = True

# Set this True to centroid the first aperture
centroidflag = True

# Set this True to reference photometry to the first aperture
referenceflag = True

# Set this True for diagnostics
diagnosticsflag = False


rahr = 0.
ramin = 0.
rasec = 0.
decdeg = 0.
decmin = 0.
decsec = 0.

# Convert the ra and dec fields into decimal degrees for wcs
# This procedure accepts ra in hours and dec in degrees
# Input may be formatted as a single decimal entry or as hh:mm::ss.ss dd:mm:ss.ss

if ':' in rastr:
  rahrstr, raminstr, rasecstr = rastr.split(":")
  rahr = abs(float(rahrstr))
  ramin = abs(float(raminstr))
  rasec = abs(float(rasecstr))
  if float(rahrstr) < 0:
    rasign = -1.
  else:
    rasign = +1.
  ra_center = rasign*(rahr + ramin/60. + rasec/3600.)*15.
else:  
  ra_center = 15.*float(rastr) 

if ':' in decstr:
  decdegstr, decminstr, decsecstr = decstr.split(":")
  decdeg = abs(float(decdegstr))
  decmin = abs(float(decminstr))
  decsec = abs(float(decsecstr))
  if float(decdegstr) < 0:
    decsign = -1.
  else:
    decsign = +1.
  dec_center = decsign*(decdeg + decmin/60. + decsec/3600.)
else:  
  dec_center = float(decstr) 


# Create a sky objects counter and an empty sky objects list

nsky = 0
sky = []
radius = 0.041666

# Query MAST
# This may  generate a non-trappable error if the object is not found
# Use 2>/dev/null in Linux to hide verbose reporting

print("\n")
print("Searching MAST database within %4.3f arcminutes of  %s %s \n" % (60.*radius, rastr, decstr) ) 

# MAST TIC input accepts RA and Dec in hh:mm:ss.ss dd:mm:ss.ss
# Returns RA and Dec in degrees and TIC ID

coord = rastr + " " + decstr

mast_table = Catalogs.query_object(coord, radius=radius, catalog="Tic")

print("\n")

if diagnosticsflag:
  # Print a snapshot of the table
  # mast_table.pprint()
  # Print all the column names
  print("Available columns in the MAST data table: \n")  
  for i in range(len(mast_table.colnames)):
    # print(i, mast_table.colnames[i])
    # print("%4d  %s" % (i, mast_table.colnames[i]))
    print('{:4d} {:s}'.format(i, mast_table.colnames[i]) )
  print("\n")


if diagnosticsflag:
  # Test the first entry
  # TESS stars should return ra and dec in decimal degrees

  idstr = mast_table['ID'][0]
  rastr = mast_table['ra'][0]
  decstr = mast_table['dec'][0]
  tmag = mast_table['Tmag'][0]
  print("ID: ", idstr, "  RA: ",  rastr, "  Dec: ", decstr, "  Tmag: ", tmag, "\n")
  

# Find length of table

nstars = len(mast_table)

if nstars < 1:
  sys.exit('No objects found near  %s  %s ' % (rastr,decstr,))

if verboseflag:
  print("Found TIC entries: \n")
  print("   # ID          RA (deg)       Dec (deg)      Tmag     Sep (arcsec) \n")


# Add TESS star coordinates to the sky list

for i in range(nstars):
  rastr = mast_table['ra'][i]
  decstr = mast_table['dec'][i]
  tic = mast_table['ID'][i]
  tmag = mast_table['Tmag'][i]
  distance = mast_table['dstArcSec'][i]

  ra = float(rastr)
  dec = float(decstr)
  if verboseflag:
    print("%4d %s %15.8f %15.8f   %4.3f   %4.2f" % (i, tic, float(rastr), float(decstr), tmag, distance)) 
  sky.append((ra, dec))
  nsky = nsky + 1


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

# Format the aij aperture file like this example

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

# Here we make them all calibrators except optionally the first one
pixfp.write(".multiaperture.isrefstar=") 
for i in range(npix - 1):
  if i==0:
    if referenceflag:
      pixfp.write("false,")
    else:
      pixfp.write("true,")
  else:
    pixfp.write("true,")
pixfp.write("true\n")

# Add an optional centroid condition for the first one
if centroidflag:
  # Centroid the first one will align on any similar image in AIJ
  pixfp.write(".multiaperture.centroidstar=") 
  for i in range(npix - 1):
    if i==0:
      pixfp.write("true,")
    else:
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

# Clean up console
print("\n")

exit()


