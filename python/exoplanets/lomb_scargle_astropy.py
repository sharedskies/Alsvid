#!/usr/local/bin/python3

# Compute a spectrum of non-uniformly spaced temporal data
# Uses astropy

import os
import sys
import matplotlib.pyplot as plt
import numpy as np
from astropy.stats import LombScargle


if len(sys.argv) == 3:
  infile = sys.argv[1]
  outfile = sys.argv[2]
else:
  print ("Lomb-Scargle frequency plot for input time-series data")
  sys.exit("Usage: lomb_scargle_astropy.py  infile.dat  outfile.dat ")
  
indata = np.loadtxt(infile)
signal_data = indata[:,1]
time_data = indata[:,0]

# These lines may be useful if slice numbers are input
#   slice_interval = 1.
#   time_data =  time_data*slice_interval

# Use Lomb-Scargle method to calculate the spectrum
frequency, spectrum  = LombScargle(time_data, signal_data).autopower()

outdata = np.column_stack((frequency,spectrum))
np.savetxt(outfile, outdata)

# Plot the result 
fig = plt.figure()
fig.canvas.set_window_title(infile)
fig.subplots_adjust(hspace=0.5)

spectrum_view = fig.add_subplot(2,1,1)
plt.plot(time_data, signal_data, 'ro')
plt.xlabel('Time')
plt.ylabel('Amplitude')
plt.title('Signal')
spectrum_view.plot(time_data, signal_data, 'ro')


power_view = fig.add_subplot(2, 1, 2)

plt.xlabel('Frequency')
plt.ylabel('Amplitude')
plt.title('Lomb Scargle Periodogram')
power_view.plot(frequency, spectrum)

plt.show()

exit()
