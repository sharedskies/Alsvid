#!/usr/local/bin/python3

"""
  
  Performs a transit least squares search of observational data
  
  Uses TLS with plotting options
  
  Input:
  
    TIC ID
    Filename for data with time and flux
    Filename for output of power versus period

  Output:
  
    File of power versus period
    File of phase-folded detection
    File of model matching phase-folded detection
    Data on the detected transit 
    Optional Matplotlib graphics displayed and saved
    Optional Bokeh graphics displayed and saved
    Optional Plotly graphics displayed and saved

  Credit:
  
    See https://github.com/hippke/tls for the TLS library
    Reference material is also in the journal article
      Michael Hippke and Rene Heller
      Optimized transit detection algorith to search for periodic
      transits of small planes
      A&A 623, A39 (2019)
      
"""

import os
import sys
import numpy as np
from astropy.stats import sigma_clip
from transitleastsquares import (
  transitleastsquares,
  cleaned_array,
  catalog_info,
  transit_mask
  )

# Use these for plotly plotting with html in a browser
import plotly.graph_objects as go
from plotly.offline import plot

# Use these for bokeh plotting with html in a browser 

from bokeh.io import output_file, show
from bokeh.layouts import column
from bokeh.plotting import figure

# Use this for matplotib

import matplotlib.pyplot as plt

# Set true for additional output
verbose_flag = False

# Set true for list of results keys
key_flag = True

# Set true for plotting options
matplotlib_flag = False
bokeh_flag = False
plotly_flag = True

if len(sys.argv) == 4:
  tic_id = int(sys.argv[1])
  infile = sys.argv[2]
  outfile_basename = sys.argv[3]
else:
  print ("Transit least squares model from  time-series data")
  sys.exit("Usage: tls.py  tic_id  infile.dat  outfile_basename ")
  
indata = np.loadtxt(infile)
signal_data = indata[:,1]
time_data = indata[:,0]

print(catalog_info(TIC_ID=tic_id))
ab, mass, mass_min, mass_max, radius, radius_min, radius_max = catalog_info(TIC_ID=tic_id)
print('Searching with limb-darkening estimates using quadratic LD (a,b)=', ab)


# Use transit least squares to explore the data
model = transitleastsquares(time_data, signal_data)


#  Return from transitleastsquares is a dictionary containing:
#
#         transitleastsquaresresults(
#           SDE,
#           SDE_raw,
#           chi2_min,
#           chi2red_min,
#           period,
#           period_uncertainty(test_statistic_periods, power),
#           T0,
#           duration,
#           depth,
#           (depth_mean, depth_mean_std),
#           (depth_mean_even, depth_mean_even_std),
#           (depth_mean_odd, depth_mean_odd_std),
#           transit_depths,
#           transit_depths_uncertainties,
#           rp_rs,
#           snr,
#           snr_per_transit,
#           snr_pink_per_transit,
#           odd_even_mismatch,
#           transit_times,
#           per_transit_count,
#           transit_count,
#           distinct_transit_count,
#           empty_transit_count,
#           FAP(SDE),
#           in_transit_count,
#           after_transit_count,
#           before_transit_count,
#           test_statistic_periods,
#           power,
#           power_raw,
#           SR,
#           chi2,
#           chi2red,
#           model_lightcurve_time,
#           model_lightcurve_model,
#           model_folded_phase,
#           folded_y,
#           folded_dy,
#           folded_phase,
#           model_folded_model,
#         )  

# The search results are returned as a dictionary. The dictionary can be limited:
#   Convert part of the dictionary to a list
#   Limit the list
#   Convert the list ot a new dictionary

results = model.power(u=ab)
depth_ppt = 1000.*(1. - results.depth)

print('Most probable period: ', format(results.period, '.5f'), 'd')
print('Number of transits in these data: ', len(results.transit_times))
print("Transit times in these data: ", results.transit_times)
print("SNR per transit: ", results.snr_per_transit)
print("Odd-even mismatch: ", results.odd_even_mismatch)  
print('Transit depth (PPT): ', format(depth_ppt, '.3f'))
print('Transit duration (days): ', format(results.duration, '.5f'))
print('False alarm probability: ', results.FAP)
print("\n")

statistics_results = dict(list(results.items())[0:28]) 
statistics_file = outfile_basename + "_statistics.txt"
statistics_fp = open(statistics_file, "w")
for key in statistics_results.keys():
  statistics_line = str(key)+": "+str(statistics_results[key])+"\n"
  statistics_fp.write(statistics_line)
statistics_fp.close()

if key_flag:

  # List all the keys in the results dictionary
  print("Complete search results are available for: \n")
  for key in results.keys():
    print("%s\n" % (key,))
  
if verbose_flag:

  # List the essential statistical results from the search
  print("Search outcome: \n")
  for key in statistics_results.keys():
    print("%s %s\n" % (key, statistics_results[key]))

  
# Write the power-period data to a file

outdata = np.column_stack((results.periods,results.power))
power_file = outfile_basename + "_power_periods.dat"
np.savetxt(power_file, outdata)

# Write the data lightcurve-phase to a file

outdata = np.column_stack((results.folded_phase,results.folded_y))
data_phased_file = outfile_basename +"_data_phase.dat"
np.savetxt(data_phased_file, outdata)

# Write the model lightcurve-phase to a file

outdata = np.column_stack((results.model_folded_phase,results.model_folded_model))
model_phased_file = outfile_basename +"_model_phase.dat"
np.savetxt(model_phased_file, outdata)


if matplotlib_flag:

  # Plot the results with matplotlib

  fig = plt.figure(figsize=(8,9))
  fig.canvas.set_window_title(infile)
  fig.subplots_adjust(hspace=0.75)
  figure_title = "TIC ID {0:s} in {1:s}".format(sys.argv[1], sys.argv[2])

  fig.suptitle(figure_title)

  transit_view = fig.add_subplot(3,1,1)

  reference_jd = int(time_data[0])
  time_label = "{0:s}  {1:d}".format("Time since JD ", reference_jd)

  plt.xlabel(time_label)
  plt.ylabel('Amplitude')
  plt.title('Signal')
  transit_view.plot(time_data - reference_jd, signal_data, color='blue')

  spectrum_view = fig.add_subplot(3, 1, 2)
  plt.xlabel('Period')
  plt.ylabel('Power')
  plt.title('Transit Event Periodogram')
  spectrum_view.plot(results.periods, results.power, color='red', markersize=1.5)
  
  phase_view = fig.add_subplot(3, 1, 3)
  plt.xlabel('Phase')
  plt.ylabel('Signal')
  plt.title('Phase-Folded Transit')
  phase_view.plot(results.model_folded_phase, results.model_folded_model, color='red')
  phase_view.scatter(results.folded_phase, results.folded_y, color='blue', s=10, 
    alpha=0.5, zorder=2)  
  phase_view.set_xlim(0.45,0.55)

  matplotlib_png = outfile_basename +"_mpl.png"
  matplotlib_pdf = outfile_basename +"_mpl.pdf"
  plt.savefig(matplotlib_png)
  plt.savefig(matplotlib_pdf)    
  plt.show()


if bokeh_flag:

  #Plot the results using Bokeh and save the html as a file

  bokeh_plot_file = outfile_basename + "_bokeh.html"
  output_file(bokeh_plot_file)
  
  # Create the figure and plot the data

  transit_plot = figure(tools="hover,crosshair,pan,wheel_zoom,box_zoom,box_select,reset",x_axis_label="BJD",y_axis_label="Signal")   
  transit_plot.line(time_data, signal_data, line_color="green", line_alpha=0.6, line_width=2)
  transit_plot.line(results.model_lightcurve_time, results.model_lightcurve_model, line_color="red", line_alpha=0.6, line_width=2)
  
  power_plot = figure(tools="hover,crosshair,pan,wheel_zoom,box_zoom,box_select,reset",x_axis_label="Period",y_axis_label="Power")      
  power_plot.line(results.periods, results.power, line_width=2)
  
  phase_plot = figure(tools="hover,crosshair,pan,wheel_zoom,box_zoom,box_select,reset",x_axis_label="Phase",y_axis_label="Signal")      
  phase_plot.scatter(results.folded_phase, results.folded_y, radius=0.005, fill_color="blue", line_color=None, fill_alpha=0.6)
  phase_plot.line(results.model_folded_phase, results.model_folded_model,line_color="red", line_width=2)

  # Show and save the plots in a vertical panel
 
  show(column(transit_plot, power_plot, phase_plot))


if plotly_flag:

  # Plot the results using Plotly and save the html as a file
  
  plotly_plot_file = outfile_basename + "_plotly.html"
  tls_fig = go.Figure()
  tls_fig.add_trace(go.Scatter(x=results.folded_phase, y=results.folded_y,
    mode='lines',
    name='Observed'))
  tls_fig.add_trace(go.Scatter(x=results.model_folded_phase, y=results.model_folded_model,
    mode='lines',
    name='Model'))

  tic_text =  "TIC "+ format(tic_id, 'd')
  file_text = "TLS data file: "+infile
  epoch_text =  "Epoch: " +  format(results.T0, '.5f')
  period_text = "Period: " + format(results.period, '.5f') + " d \u00B1 " + format(results.period_uncertainty, '.5f')
  tls_fig.update_layout(title=period_text+"  "+epoch_text+"   "+tic_text,
    xaxis_title='Phase',
    yaxis_title='Signal')


  tls_fig.show()
  plot(tls_fig, filename=plotly_plot_file, auto_open=False) 

  


exit()
