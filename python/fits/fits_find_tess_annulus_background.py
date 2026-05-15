#!/usr/local/bin/python3

"""

  Generate a background image for a stack of TESS images
    Estimate the background at each pixel using the AstroImageJ annulus algorithm
    Create a new file with the background at that pixel
    Optimized for TESS FFI and cutout images

"""

import os
import sys
import math as ma
import numpy as np
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc

print("This routine will process all the fits files in the current directory.")
print("  It is optimized for TESS full frame and cutout images,")
print("  and since it works pixel-by-pixel, for FFIs it will take several") 
print("  minutes per file to run.")
print("\n")

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_find_tess_annulus_background.py  outprefix infile1.fits infile2.fits ...   ")
  print(" ")
  sys.exit("Find a background in a stack of TESS images\n ")
elif len(sys.argv) >=3:
  outprefix = sys.argv[1]
  infiles = sys.argv[2:]
else:
  print(" ")
  print("Usage: fits_find_tess_annulus_background.py outprefix infile1.fits infile2.fits ...  ")
  print(" ")
  sys.exit("Find a background in a stack of TESS images\n")
  

# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwriteflag = True  


# The full aperture photometry routine here for reference
# See the following for the background subtraction routine

def apphot(imdata, x, y, rinner, router):
	
  # Single star aperture photometry based on AstroImageJ
  # Input image, star center, aperture radii
  # Return total signal, background per pixel, and Gaussian psf hwhm
  
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
  pixcount = 0.
          
  # Find the signal of this star
    
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
        pixsignal = imdata[j, i] - pixbackground
        pixsignalsum = pixsignalsum + pixsignal 
        pixcount = pixcount + 1.     
      else:
        pass
  
  pixcount = max(pixcount, 1.)
  pixmean = pixsignal/pixcount
  sumdelta2 = 0.
  sumr2delta2 = 0.
    
  # Find the standard deviation for this signal
  
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
        sumr2delta2 =  sumr2delta2 + dr2*pixdelta*pixdelta 
        sumdelta2 = sumdelta2 + pixdelta*pixdelta      
      else:
        pass
  pixsigma = ma.sqrt(sumdelta2/pixcount)
  pixr2sigma = ma.sqrt(sumr2delta2/pixcount)
  try:
    a = pixr2sigma/pixsigma
    psfhwhm = a
  except:
    psfhwhm = 1.
    #print (x, y, pixsignalsum, pixbackground, psfhwhm)
      
  return pixsignalsum, pixbackground, psfhwhm


# Background based on the AstroImageJ algorithm

def apbkg(imdata, x, y, rinner, router):
	
  # Single star background  based on AstroImageJ
  # Input image, star center, aperture radii
  # Return total background per pixel
  
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
      
  return pixbackground



i = 0
for infile in infiles:
  inlist = pyfits.open(infile)
  inimage = inlist[0].data
  inhdr = inlist[0].header
  inshape = inimage.shape
  inxmax = inshape[1]
  inymax = inshape[0]
   
  # Select 9x9 region around the pixel

  outimage = 0.*np.copy(inimage)
          
  outfile = outprefix + '_%04d.fits' % (i,) 
  
  # Find the background for this slice
  
  rinner = 4.
  router = 5.
  
  for ix in range(0, inxmax):
    for iy in range(0, inymax):
      x = float(ix + 1)
      y = float(iy + 1)
      background = apbkg(inimage, x, y, rinner, router)
      outimage[iy,ix] = background
    print(x, y, background)

  # Provide a new date stamp

  file_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

  # Update the header

  outhdr = inhdr
  outhdr['DATE'] = file_time
  outhdr['history'] = 'Original file %s' % (infile)
  outhdr['history'] = 'Background from fits_find_background' 

  # Create the fits object for this image using the header of the first image

  outlist = pyfits.PrimaryHDU(outimage,outhdr)


  # Write the fits file

  outlist.writeto(outfile, overwrite = overwriteflag)

  # Close the file reference so that mmap will release the handler

  inlist.close()
    
  del inimage
  del inhdr
  i = i + 1

exit()

