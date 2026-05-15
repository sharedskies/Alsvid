#!/usr/local/bin/python3

# Compute a box least squares periodogram of  temporal data
# Uses astropy's implementation of BLS woth bokeh grahical output to browser

import os
import sys
import numpy as np
from astropy.stats import BoxLeastSquares
from bokeh.plotting import figure, output_file, show

if len(sys.argv) == 3:
  infile = sys.argv[1]
  outfile = sys.argv[2]
else:
  print ("Box least squares model from  time-series data")
  sys.exit("Usage: bls_astropy.py  infile.dat  outfile.dat ")
  
indata = np.loadtxt(infile)
signal_data = indata[:,1]
time_data = indata[:,0]

# Use  box least squares  method to model the distribution
model = BoxLeastSquares(time_data, signal_data)
periodogram = model.autopower(0.2)

# Diagnostic to see the attributes and some values
# print(periodogram)

periods = periodogram.period
powers = periodogram.power

outdata = np.column_stack((periods,powers))
np.savetxt(outfile, outdata)

# Plot the result 

# Inform bokeh with the name of the output html file  

output_file("bls.html")

# Create the figure and plot the data

x_data = periods 
y_data = powers 

p = figure(tools="hover,crosshair,pan,wheel_zoom,box_zoom,box_select,reset",x_axis_label="Period",y_axis_label="Power")      
p.line(x_data, y_data, line_width=2)

# Show it and also write the file

show(p)

print ("BLS power spectrum is in file ", outfile)
print ("BLS power spectrum for display in browser is in bls.html \n") 



exit()
