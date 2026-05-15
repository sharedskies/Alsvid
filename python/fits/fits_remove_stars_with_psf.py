#!/usr/local/bin/python3

# Remove stars in a pixel list from afits image  using psf fitting
# Estimates PSF from variance within the aperture

# The pixel list is a set of P(x,y) data identifying centers of regions
# P(x,y) is a floating point coordinate in the image space
# P(x,y) is referenced to the lower left pixel that is 1,1 at its center
# The lower left of the image space is therefore (0.5, 0.5)

# Note that the Numpy array has x and y swapped from the image x and y


import os
import sys
import math as ma
import numpy as np
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc

# Examples of  inner and outer radii for background annulus

rin =  16.   # inner radius floating point in pixels       
rout = 24.   # outer radius floating point in pixels
psfx = 3.0   # scale factor on estimated psf  to determine removal region

# Initialize psf parameters

#psfa = 10.0 # Gaussian 1/e width
#psfh = 10.0 # Gaussian h 

# Define psf function 
  
def psfg(x, y, h, a):
  # Gaussian psf 
  # (x,y)is image coordinate relative to centroid
  # f is the psf signal above background at that pixel
 
  arg = (x**2 + y**2)/a**2
  f =  h*np.exp(-arg) 
  return f


# Define functions for handling photometry at each star

def centroid(imdata, x, y, r):
  
  # Find the signal weighted centroid of a specfied aperture in a numpy array
  # Search within the radius r around the floating point coordinates (x, y)
  # Return the floating point centroid pair 
  
  # Trap for r less than 0.5 and return the same pixel
  
  if r < 0.5:
    return x, y    

  # How big is this image?
  # Numpy images have the y-axis first
  
  ysize, xsize = imdata.shape

  # Define search limits around the target

  xmin = x - r
  xmax = x + r
  ymin = y - r
  ymax = y + r
  
  imin = int(np.floor(xmin - 0.5))
  imax = int(np.floor(xmax - 0.5))
  jmin = int(np.floor(ymin - 0.5))
  jmax = int(np.floor(ymax - 0.5))
  
  imin = max(0, imin)
  jmin = max(0, jmin)
  imax = min(xsize - 1, imax)
  jmax = min(ysize - 1, jmax)
  
  # Initialize sums and constants for the centroid evaluation
  
  tsig = 0.0
  txsig = 0.0
  tysig = 0.0
  r2 = r*r
  
  # Run over this box and perform the weighted sums
  
  for i in range(imin, imax):
    for j in range(jmin, jmax):
      xp = float(i) + 1.0
      yp = float(j) + 1.0
      dx = xp - x
      dy = yp - y
      dx2 = dx * dx
      dy2 = dy * dy
      a2 = dx2 + dy2
      if a2 <= r2:
        txsig = dx * imdata[j, i] + txsig
        tysig = dy * imdata[j, i] + tysig
        tsig = imdata[j, i] + tsig
  
  # Finish by calculating the new centroid coordinates
  
  tsig = max(tsig, 1.)
  xc = txsig/tsig + x
  yc = tysig/tsig + y
  
  return xc, yc


def apphot(imdata, x, y, rinner, router):
	
  # Single star aperture photometry 
  # Input image, star center, aperture radii
  # Return total signal, background per pixel, and Gaussian psf width
  
  # P(x,y) is a floating point coordinate in the image space
  # P(x,y) referenced to the lower left pixel that is 1,1 at its center

  ysize, xsize = imdata.shape
  rinner2 = rinner * rinner
  router2 = router * router

  # Define limits around the target

  xmin = x - rinner
  xmax = x + rinner
  ymin = y - rinner
  ymax = y + rinner
  
  imin = int(np.floor(xmin - 0.5))
  imax = int(np.floor(xmax - 0.5))
  jmin = int(np.floor(ymin - 0.5))
  jmax = int(np.floor(ymax - 0.5))

  imin = max(0, imin)
  jmin = max(0, jmin)
  imax = min(xsize - 1, imax)
  jmax = min(ysize - 1, jmax)
      
  inner = 0.
  innercount = 0.
  outer = 0.0
  outer2 = 0.0
  outercount = 0.0
  
  # Find the first pass background in the annulus
  
  for i in range(imin, imax):
    for j in range(jmin, jmax):      
      xp = float(i) + 1.0
      yp = float(j) + 1.0
      dx = xp - x
      dy = yp - y
      dx2 = dx * dx
      dy2 = dy * dy
      dr2 = dx2 + dy2
      value = imdata[j, i]
      if dr2 < router2 and dr2 >= rinner2:
        outer = outer + value
        outer2 = outer2 + value*value
        outercount = outercount + 1.0
      else:
        pass

  outercount = max(outercount, 1.)
  outeravg = outer/outercount
  outer2avg = outer2/outercount
  outeravg2 = outeravg*outeravg
  outerdelta = max(outer2avg - outeravg2, 0.)
  sigma = ma.sqrt(outerdelta) 

  # Now iterate over the annulus and remove outliers
  # Stop the iteration after maxpasses or when the average converges
  
  maxpasses = 10
  
  for k in range (maxpasses):
    
    # Break if sigma is nearly zero (all pixels equal)
    
    if sigma < 0.1:
      break
    
    lastouteravg = outeravg
    outer = 0.0
    outer2 = 0.0
    outercount = 0.0
    for i in range(imin, imax):
      for j in range(jmin, jmax):      
        xp = float(i) + 1.0
        yp = float(j) + 1.0
        dx = xp - x
        dy = yp - y
        dx2 = dx * dx
        dy2 = dy * dy
        dr2 = dx2 + dy2
        value = imdata[j, i]
        if (dr2 < router2 and dr2 >= rinner2) and (abs(value - outeravg) < 2.*sigma):
          outer = outer + value
          outer2 = outer2 + value*value
          outercount = outercount + 1.0
    
    # Break if only a few pixels remain
    
    if outercount < 2:
      break

    outeravg = outer/outercount

    # Break from the loop once the outer average has stabilized
    # This is ad hoc and would work for 16-bit data where each value is 1 photon
    # It would probably have to be scaled for larger dynamic range
    
    if abs(lastouteravg - outeravg) < 0.1:
      break

    outer2avg = outer2/outercount
    outeravg2 = outeravg*outeravg
    outerdelta = max(abs(outer2avg - outeravg2), 0.)
    sigma = ma.sqrt(outerdelta)

  
  # This establishes the background per pixel with stars and outlier pixels removed
  
  pixbackground = outeravg
  pixsignalsum = 0.
  pixmomentsum = 0.
  pixcount = 0.
          
  # Find the total signal and first moment of this star
    
  for i in range(imin, imax):
    for j in range(jmin, jmax):      
      xp = float(i) + 1.0
      yp = float(j) + 1.0
      dx = xp - x
      dy = yp - y
      dx2 = dx * dx
      dy2 = dy * dy
      dr2 = dx2 + dy2
      #dr1 = ma.sqrt(dr2)
      if dr2 < rinner2:
        pixsignal = imdata[j, i] - pixbackground
        pixsignalsum = pixsignalsum + pixsignal
        pixmomentsum = pixmomentsum + pixsignal*dr2 
        pixcount = pixcount + 1.     
      else:
        pass
  
  pixcount = max(pixcount, 1.)
  pixmean = pixsignalsum/pixcount
  
  try:
    psfa = ma.sqrt(pixmomentsum/pixsignalsum)
  except:
    psfa = 1.
  
        
  # Find the standard deviation for this signal
  
  sumdelta2 = 0.
  for i in range(imin, imax):
    for j in range(jmin, jmax):      
      xp = float(i) + 1.0
      yp = float(j) + 1.0
      dx = xp - x
      dy = yp - y
      dx2 = dx * dx
      dy2 = dy * dy
      dr2 = dx2 + dy2
      if dr2 < rinner2:
        pixdelta = imdata[j, i] - pixbackground - pixmean 
        sumdelta2 = sumdelta2 + pixdelta*pixdelta      
      else:
        pass
  pixsigma = ma.sqrt(sumdelta2/pixcount)
      
  return pixsignalsum, pixbackground, psfa
	
# End of function definitions

if len(sys.argv) != 7:
  print(" ")
  print("Usage: fits_remove_stars_with_psf.py psf_scale r_inner r_outer infile.fits pixels.txt outfile.fits")
  print(" ")
  print("    psf_scale: factor to multiply psf by to set removal region" )
  print("    r_inner: inner radius of annulus for background measurement around a star" )
  print("    r_outer: outer radius of annulus for background measurement around a star" )
  print("    infile.fits: input fits image" )
  print("    pixels.txt: pixel coordinates file in space- or comma-delimited or ds9 format" )
  print("    outfile.fits: output fits image with stars removed")
  print(" ")
  sys.exit("Remove stars from  a fits image\n")

psfx = float(sys.argv[1])
rin = float(sys.argv[2])
rout = float(sys.argv[3])
infile = sys.argv[4]
pixfile = sys.argv[5]
outfile = sys.argv[6]

# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwriteflag = True  
  
# Open the fits file readonly by default and create an input hdulist

inlist = pyfits.open(infile) 

# Assign the input header 

inhdr = inlist[0].header

# Assign image data to numpy array and get its size

inimage =  inlist[0].data.astype('float32')
xsize, ysize = inimage.shape


# Use a unit array to assure we treat the whole image in floating point 

fone = np.ones((xsize,ysize))

# Create the output the image

outimage = fone*inimage

# Take x,y coordinates from a plain text file
# These coordinates are referenced to the lower left pixel at (1,1)

# Open the file with pixel coordinates
pixfp = open(pixfile, 'r')

# Read all the lines into a list
pixtext = pixfp.readlines()

# Close the pixel file
pixfp.close()

# Create a pixels counter and an empty pixels list
i = 0
pixels = []

# Split pixels text and parse into x,y values  
# We try various formats looking for one with a valid entry and take the first one we find
# This searches ds9 box and circle regions, comma separated, and space separated

for line in pixtext:

  if 'circle' in line:
    # Treat the case of a ds9 circle region
    
    # Remove the leading circle( descriptor
    line = line.replace("circle(", '')

    # Remove the trailing )
    line = line.replace(")", '')

    # Remove the trailing \n and split into text fields
    entry = line.strip().split(",")
    
    # Get the x,y values for these fields
    xcenter = float(entry[0])
    ycenter = float(entry[1])
    pixels.append((xcenter, ycenter))
    i = i + 1

  elif 'box' in line:
    # Treat the case of a ds9 box region
    
    # Remove the leading box( descriptor
    line = line.replace("box(", '')

    # Remove the trailing )
    line = line.replace(")", '')

    # Remove the trailing \n and split into text fields
    entry = line.strip().split(",")
     
    # Get the x,y values for these fields
    xcenter = float(entry[0])
    ycenter = float(entry[1])
    pixels.append((xcenter, ycenter))
    i = i + 1
  
  else:
    # Treat the cases of plain text pixel coordinates
    # Try to remove the trailing \n and split into text fields
    
    try:    
      # Treat the case of a plain text comma separated entry
      
      entry = line.strip().split(",")  
      # Get the x,y values for these fields
      xcenter = float(entry[0])
      ycenter = float(entry[1])
      pixels.append((xcenter, ycenter))
      i = i + 1    
    except:      
      
      try: 
        # Treat the case of a plane text blank space separated entry
        entry = line.strip().split()
        xcenter = float(entry[0])
        ycenter = float(entry[1])
        pixels.append((xcenter, ycenter))
        i = i + 1    
           
      except:
        pass
        
      
# How many pixels found?

npixels = i
if npixels < 1:
  sys.exit('No objects found in %s' % (pixelsfile,))


# Clean the image

for k in range(npixels):

  # Look at the next pixel
  x, y = pixels[k]
    
  # Centroid on this location inside an outer radius
  xc, yc = centroid(outimage, x, y, rout)
  
  # Find the background and gaussian width
  signal, bkg, a = apphot(outimage, xc, yc, rin, rout)
    
  h = signal/(a*a*ma.pi)
      
  # Define the region to be replaced in numpy indices 
  
  rc = psfx * a
  rc2 = rc * rc
  xmin = xc - rc
  xmax = xc + rc
  ymin = yc - rc
  ymax = yc + rc
  
  imin = int(np.floor(xmin - 0.5))
  imax = int(np.floor(xmax - 0.5))
  jmin = int(np.floor(ymin - 0.5))
  jmax = int(np.floor(ymax - 0.5))

  imin = max(0, imin)
  jmin = max(0, jmin)
  imax = min(xsize - 1, imax)
  jmax = min(ysize - 1, jmax)
      
  # Remove the psf from this region
    
  for i in range(imin, imax):
    for j in range(jmin, jmax):

      xp = float(i) + 1.0
      yp = float(j) + 1.0
      dx = xp - xc
      dy = yp - yc
      dx2 = dx * dx
      dy2 = dy * dy
      a2 = dx2 + dy2
      if a2 <= rc2:
        outimage[j,i] =  outimage[j,i] - psfg(dx, dy, h, a)




# Create the fits ojbect for this image using the header of the first image
# Use float32 for output type

outlist = pyfits.PrimaryHDU(outimage.astype('float32'),inhdr)

# Provide a new date stamp

file_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

# Update the header

outhdr = outlist.header
outhdr['DATE'] = file_time
outhdr['history'] = 'Processed by fits_remove_stars_with_psf' 
outhdr['history'] = 'Image file '+  infile

# Write the fits file

outlist.writeto(outfile, overwrite = overwriteflag)

# Close the input  and exit

inlist.close()
exit()

