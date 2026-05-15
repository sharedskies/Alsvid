#!/usr/local/bin/python3

#  Bin a stack of fits images

import os
import sys
import numpy as np
import astropy.io.fits as pyfits
from time import gmtime, strftime  # for utc

if len(sys.argv) == 1:
  print(" ")
  print("Usage: fits_bin_1d.py binfactor outprefix infile1.fits infile2.fits ...   ")
  print(" ")
  sys.exit("Bin a stack of fits images along the time- or z-axis\n ")
elif len(sys.argv) >=5:
  binfactor = int(float(sys.argv[1]))
  outprefix = sys.argv[2]
  infiles = sys.argv[3:]
else:
  print(" ")
  print("Usage: fits_bin_1d.py binfactor outprefix infile1.fits infile2.fits ...  ")
  print(" ")
  sys.exit("Bin a stack of fits images along the time- or z-axis\n")
  

# Set a overwrite flag True so that images can be overwritten
# Otherwise set it False for safety

overwriteflag = True  

# Build an image stack in memory
# Test that all the images are the same shape and exit if not

inlists = []
inhdrs = []
inimages = []
nin = 0
for infile in infiles:
  inlist = pyfits.open(infile)
  inimage = inlist[0].data.astype('float32')
  inhdr = inlist[0].header
  if nin == 0:
    inshape0 = inimage.shape
    xsize, ysize = inshape0
    inhdr0 = inlist[0].header
  else:
    inshape = inimage.shape
    if inshape != inshape0:
      sys.exit('File %s not the same shape as %s \n' %(infile, infiles[0]) )  
  inimages.append(inimage.copy())  

  # Close the file reference so that mmap will release the handler

  inlist.close()
  
  # Delete unneeded references to the file content
  
  del inimage
  del inhdr
  # print infile
  nin = nin + 1

if nin < 1:
  sys.exit(' No images in the input stack \n')

if binfactor <= 0:
  sys.exit('  Binning factor should be a small non-zero positive integer \n')


newxsize = xsize
newysize = ysize

if newxsize*newysize == 0:
  sys.exit(' Processing requires 2D images \n');
    
print('Creating new %i x %i images binned on the stack axis by %i \n' % (newysize, newxsize, binfactor))


# Create a numpy cube of input images from the list of images

instack = np.array(inimages)


# How many output images will result from this binning?

nout = int(nin/binfactor)


# Create a numpy cube to receive the binned images

outstack = np.zeros((nout, newxsize, newysize))


# Every pixel in each input image contributes to one pixel the binned output image

for i in range(nout):
  imstart = int(i*binfactor)
  imstop = int(imstart + binfactor) 
  outstack[i,:,:] = np.copy(np.sum(instack[imstart:imstop,:,:],axis=0))
          
for i in range(nout):

  outimage = outstack[i,:,:]
          
  outfile = outprefix + '_%04d.fits' % (i,) 
  
  # Create the fits ojbect for this image using the header of the first image

  outlist = pyfits.PrimaryHDU(outimage.astype('float32'),inhdr0)

  # Provide a new date stamp

  file_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

  # Update the header

  outhdr = outlist.header
  outhdr['DATE'] = file_time
  outhdr['history'] = 'Result of fits_bin_1d binned by %d' %(binfactor)
  outhdr['history'] = 'Slice %d of %d images' %(i+1,nout)
  outhdr['history'] = 'First image '+  infiles[0]
  outhdr['history'] = 'Last image  '+  infiles[nin-1]

  # Write the fits file

  outlist.writeto(outfile, overwrite = overwriteflag)

# Exit


exit()

