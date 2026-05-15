#!/usr/local/bin/python3

# Sliding median normalization for BLS and TLS fitting

import os
import sys
import numpy as np
from scipy.signal import  medfilt
from bokeh.plotting import figure, output_file, show

if len(sys.argv) == 3:
  infile = sys.argv[1]
  outfile = sys.argv[2]
else:
  print ("Sliding median normalize time-series data")
  sys.exit("Usage: median_normalize.py  infile.dat  outfile.dat ")
  
indata = np.loadtxt(infile)
signal_data = indata[:,1]
time_data = indata[:,0]

reference_data = medfilt(signal_data, 25)
normalized_data = signal_data / reference_data


outdata = np.column_stack((time_data, normalized_data))
np.savetxt(outfile, outdata)

# Plot the result 

# Inform bokeh with the name of the output html file  

output_file("median.html")

# Create the figure and plot the data

x_data = time_data
y_data = normalized_data

p = figure(tools="hover,crosshair,pan,wheel_zoom,box_zoom,box_select,reset",x_axis_label="Time",y_axis_label="Signal")      
p.line(x_data, y_data, line_width=2)

# Show it and also write the file

show(p)



exit()
