#!/usr/local/bin/python3

# Find a Lomb-Scargle periodogram on time series data
# Uses scipy.signal

import os
import sys
import matplotlib.pyplot as plt
import numpy as np
import scipy
import scipy.misc
import scipy.signal 


if len(sys.argv) == 6:
  infile = sys.argv[1]
  outfile = sys.argv[2]
  lowerf = float(sys.argv[3])
  upperf = float(sys.argv[4])
  npts = int(float(sys.argv[5]))
  minmaxflag = True
elif len(sys.argv) == 3:
  infile = sys.argv[1]
  outfile = sys.argv[2]
  minmaxflag = False
else:
  print (" ")
  print ("Usage: lomb_scargle_scipy.py infile.dat outfile.dat [lowerf upperf npts]")
  print (" ")
  sys.exit("Compute Lomb-Scargle periodogram of time series data \n")



time, amplitude = np.loadtxt(infile, unpack=True)

tdel = np.amax(time) - np.amin(time)

if (tdel <= 0):
  sysexit('Check range of times in %s \n' %(infile,))

if not minmaxflag:
  lowerf = 0.5 / tdel 
  upperf = 5000 / tdel
  npts = 10000
  
# Create an array of frequencies for the periodogram
# Scipy Lomb-Scargle works on omega

frequency = np.linspace(lowerf, upperf, npts)
omega = 2.*np.pi*frequency

# Diagnostics

#print time
#print amplitude
#print frequency

normval = time.shape[0]

pgram = scipy.signal.lombscargle(time, amplitude, omega)
pgramnorm = np.sqrt(4*(pgram/normval))

dataout = np.column_stack((frequency,pgramnorm))  
np.savetxt(outfile, dataout)

fig = plt.figure()
fig.canvas.set_window_title(infile)
fig.subplots_adjust(hspace=0.5)

spectrum = fig.add_subplot(2,1,1)
plt.plot(time, amplitude, 'ro')
plt.xlabel('Time')
plt.ylabel('Amplitude')
plt.title('Signal')
spectrum.plot(time, amplitude, 'ro')


power = fig.add_subplot(2, 1, 2)

plt.xlabel('Frequency')
plt.ylabel('Amplitude')
plt.title('Lomb Scargle Periodogram')
power.plot(frequency, pgramnorm)

plt.show()
