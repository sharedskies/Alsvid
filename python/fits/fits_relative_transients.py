#!/usr/local/bin/python3

"""

  Correlate transients in a cadenced (preferrably uniformly) image stack
    Requires a reference image that should be a standard deviation for each pixel of the time series
    Requires a signed threshold multiplier of the standard deviation for that pixels background estimate
    Postive sign selectes events which are incremented from the previous signal
    Negative sign selects events which are decremented from the previous signal
    Requires consistently timed images for effective co-addition of the correlated output stack
    Uses a reference image that should be a standard deviation  in time of the stack
    Returns an image stack summing post threshold crossing events
    Returns transient event image identifying suspect pixels

"""

import os
import sys
import numpy as np
from scipy.ndimage.interpolation import shift
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc if needed

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_relative_transients.py  sigma_reference.fits signed_decrement_threshold outprefix infile1.fits infile2.fits ...   ")
  print(" ")
  sys.exit("Searches for and correlates transients in the same pixel within an  ordered temporal stack of fits images\n")
elif len(sys.argv) >=7:
  reffile = sys.argv[1]
  threshold = float(sys.argv[2])
  outprefix = sys.argv[3]
  infiles = sys.argv[4:]
else:
  print(" ")
  print("Usage: fits_relative_transients.py  sigma_reference.fits signed_decrement_threshold outprefix infile1.fits infile2.fits ...   ")
  print(" ")
  sys.exit("Create an autocorrelation  stack from a temporal stack of fits images\n")
  

# Set an overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwrite_flag = True  
diagnostics_flag = True
verbose_flag = True

# Find the reference image data
# Copy it replacing NANs with numbers
# Estimate a baseline sigma to use later

reflist = pyfits.open(reffile)
reference = np.nan_to_num(reflist[0].data.astype('float32'))
reflist.close()
sigma0 = np.average(reference)

# Are we looking for an increment or decrement in the signal?
# Use this so that subsequent changes do not cancel out the first ones

threshold_sign = np.sign(threshold)

# Build an image stack in memory
# Test that all the images are the same shape and exit if not
# Note numpy array swaps x and y compared to the FITS image
# Image x is fastest varying which results in 
# First index is image y
# Second index is image x

inlists = []
inhdrs = []
inimages = []
nin = int(0)
for infile in infiles:
  inlist = pyfits.open(infile)
  inimage = inlist[0].data.astype('float32')
  inhdr = inlist[0].header
  if nin == 0:
    inshape0 = inimage.shape
    imysize, imxsize = inshape0
  else:
    inshape = inimage.shape
    if inshape != inshape0:
      sys.exit('File %s not the same shape as %s \n' %(infile, infiles[0]) )  
  inlists.append(inlist.copy())
  inimages.append(inimage.copy())  
  inhdrs.append(inhdr.copy())
  inlist.close()
  nin = nin + 1

if nin < 2:
  sys.exit(' More than 1 image is needed to perform a random decrement transform \n')

nout = int(nin/2)

if verbose_flag:

  print("Reference standard deviation is ", sigma0)
  print("Sigma multiplier ", abs(threshold))
  print("Searching ",nin," image files for ", end="")
  
  if threshold_sign > 0.:
    print("for increment")
  else:
    print("for decrement")  


# Create a numpy cube from the list of images
# Note again that this swaps x and y in each image

instack = np.array(inimages)

# Copy a null array to the output array
# We will add the correlated data to it

outstack = np.copy(0.*np.abs(instack))

# Run the analysis on all pixels in the image stack
# Store the analysis in the first half of a copy of the input stack
# Planes beyond [nout+1] are not meaningful

# We use the fast shift function from scipy which inserts 0. if a value is missing

# Initialize  the number of shift events for that pixel as a normalization

normimage = np.zeros(inshape0)

# Work along the time axis for each spatial pixel in the stack
# First data index is image "y", second data index is image "x" 

sigma = sigma0

for i in range(imysize):
  for j in range(imxsize):

    # At this pixel copy the time series from the input data 

    time_series = np.copy(instack[:,i,j])
    
    # At this pixel estimate the temporal sigma from the reference for adjacent pixels
    
    if ( ( (i > 1) and (i < imysize - 1) ) and ( (j > 1) and (j < imxsize - 1) ) ):
      sigma = 0.125*(reference[i+1,j+1] + reference[i-1,j-1] + reference[i+1,j-1] + reference[i-1,j+1] + \
        reference[i,j+1] + reference[i,j-1] + \
        reference[i+1,j] + reference[i-1,j])
    else:
      sigma = sigma0    

    # Search for transient events in this series
    # Use the shift function to coadd correlated events


    for k in range(nout):
    
      if verbose_flag:
        print("Row {:04d}  Column {:04d}  Image {:04d}".format(i, j, k), end="\r", flush=True)

      # Co-add time_series where the data meet the threshold condition compared to the next slice

      delta = time_series[k] - time_series[k+1]
      
      # Test for an upward threshold crossing 
      
      if ( (delta > 0.) and (threshold_sign > 0.) ): 
        
        if ( abs(delta) > abs(threshold*sigma) ): 
          
          if diagnostics_flag:
            print("")
            print(k,i,j," :  ", time_series[k], time_series[k+1], delta)
            print("  ", outstack[0,i,j])
            print("  ", shift(time_series, -k, cval=0.)[0])

          # Add to the output image stack
           
          outstack[:,i,j] = outstack[:,i,j] + shift(time_series, -k, cval=0.)
          
          # Increment counter for each detected event above threshold at this pixel
          
          normimage[i,j] = normimage[i,j] + 1.

          if diagnostics_flag:
            print("  ", normimage[i,j], outstack[0,i,j], outstack[1,i,j], outstack[2,i,j])
        

      # Test for an downward threshold crossing 
      
      if ( (delta < 0.) and (threshold_sign < 0.) ): 
        
        if ( abs(delta) > abs(threshold*sigma) ): 
          
          if diagnostics_flag:
            print("")
            print(k,i,j," :  ", time_series[k], time_series[k+1], delta)
            print("  ", outstack[0,i,j])
            print("  ", shift(time_series, -k, cval=0.)[0])
            
          # Add to the output image stack
           
          outstack[:,i,j] = outstack[:,i,j] + shift(time_series, -k, cval=0.)
                    
          # Increment counter for each detected event above threshold at this pixel
          
          normimage[i,j] = normimage[i,j] + 1.

          if diagnostics_flag:
            print("  ", normimage[i,j], outstack[0,i,j], outstack[1,i,j], outstack[2,i,j])


if verbose_flag:
  print("")
  print("Writing output files") 
  print("")

for k in range(nout):

  outimage = np.copy(outstack[k,:,:])
  
  outfile = outprefix + '_%04d.fits' % (k,) 
  
  # Create the fits object for this image using the header of the first image

  outlist = pyfits.PrimaryHDU(outimage.astype('float32'),inhdrs[0])

  # Provide a new date stamp

  file_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

  # Update the header

  outhdr = outlist.header
  outhdr['DATE'] = file_time
  outhdr['history'] = 'Slice %d of %d images by fits_relative_transients' %(k+1,nout)
  outhdr['history'] = 'Threshold %f' %(threshold,)
  outhdr['history'] = 'First image '+  infiles[0]
  outhdr['history'] = 'Last image  '+  infiles[nin-1]

  # Write this slice as a fits file

  outlist.writeto(outfile, overwrite = overwrite_flag)

# Prepare and write a normalization image

normfile = outprefix + '_norm.fits'
normlist = pyfits.PrimaryHDU(normimage.astype('float32'),inhdrs[0])
normhdr = normlist.header
normhdr['DATE'] = file_time
normhdr['history'] = 'Normalization image by fits_relative_transients'
normhdr['history'] = 'Threshold %f' %(threshold,) 

# Write the fits file

normlist.writeto(normfile, overwrite = overwrite_flag)




exit()

