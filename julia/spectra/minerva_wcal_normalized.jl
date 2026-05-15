#!/usr/local/bin/julia

# minerva_wcal_normalized
#
#   Read matlab wcal data from Minerva Australis
#   Extract the spectrum from one telescope
#   Plot the spectrum for interactive display in a browser
#   Export a plain text file of wavelength and normalized flux

#   John Kielkopf (kielkopf@louisville.edu)
#   MIT License
#   Copyright 2023
#   
#   2023-12-06 Version 0.9

using MAT # Enable reading matlab HDF files

# Run these in REPL to see the data

#   filename = "20230507T230704_HD97329_wcal.mat"

#     Fibers 1, 2, 4, 6
#
#     1 => telescope 1
#     2 => telescope 3
#     3 => telescope 4
#     4 => telescope 5 (currently nothing and may be ASA)
#     5 => not used
#     6 => calibration also calspec1 

#   optical order of interference = order index + 96
#   nominal 28 g/mm at 63 degrees 

#   vars = matread(filename)
#   wl = vars["fib3_spec_wave"]
#   spec = vars["fib3_spec"]
#   nord, npix = size(wl)
#   order index 7  => optical order 103 => Na D
#   order index 29 => optical order 125 => H beta

using PlotlyJS        # Interactive browser plotting
using CurveFit        # Fitting the continuum
using DelimitedFiles  # For exporting formatted data files

# ###

# Plot in a browser window using its engine for interaction
# For the PlotlyJS API see https://plotly.com/julia/reference/surface/
# For layout see https://plotly.com/julia/reference/layout/coloraxis/

function browser(p::Plot)
  tmp_filename = "plot.html"
  savefig(p, tmp_filename)
  #run(`google-chrome $tmp_filename`)
  run(`firefox $tmp_filename`)
end

# ###

# Accept data file and fiber number as command line arguments
# Return input filename and fiber id strings

function get_commandline_arguments()

  if length(ARGS) == 2
    infile = ARGS[1]
    fiber_number_str = ARGS[2]
    fiber_id = string("fib",fiber_number_str)
     
  else
    println("Use file name and fiber number on the command line\n")
    exit() 
  end
  
# Use strings for the filename and the fiber number
# If a number is required, use parse(fiberstr)
    
  return infile, fiber_id
end  
    
# ###

# Write a 2-column data file of  x and y vectors
# Requires using DelimitedFiles at top level

function write_data_file(outfile, x_array, y_array) 

  open(outfile, "w") do io
    writedlm(io, [x_array y_array])
  end

end


infile, fiber_id =  get_commandline_arguments()
wl_id = string(fiber_id,"_spec_wave")
spec_id = string(fiber_id,"_spec")
vars = matread(infile)
wl = vars[wl_id]
spec = vars[spec_id]
nord, npix = size(wl)

# The arrays wl and spec are indexed by the order
#    
#   print(wl[19,500],"\n")
#   print(spec[19,500],"\n")
#   print(size(wl),"\n")

# Use the splat ... operator to create a vector from the array

wl_vector = vcat(wl...)
spec_vector = vcat(spec...)

nwl = size(wl_vector)[1]

# Sort both arrays in wavelength order

perm = sortperm(wl_vector)
spec_sort = spec_vector[perm]
wl_sort = wl_vector[perm]

# Process order by order
# Fit each order for the flux level and create a continuum array to match

continuum_sort = ones(nwl)

# Use a running index to these arrays for the start of each new order
# Process npix from an order and update the index for the next order

last = 0

for i in 1:nord
  global last
  first = last + 1
  last = first + npix - 1
  x = wl_sort[first:last]
  y = spec_sort[first:last]
  fit = curve_fit(Polynomial, x, y, 2)
  yfit = fit.(x)
  continuum_sort[first:last] = yfit[1:npix]
end

spec_normalized = spec_sort ./ continuum_sort

# Write the spectrum file

# Save the model flux

file_base = split(infile, ".")[1]
outfile = file_base*"_normalized_flux.dat"

write_data_file(outfile, wl_sort, spec_normalized)


# Generate plot with PlotlyJS

trace_spec = scatter(x = wl_sort, y = spec_sort, 
  name = fiber_id, mode = "markers")
trace_fit = scatter(x = wl_sort, y = continuum_sort, 
  mode = "lines", line_color = "red", name = "fit")
trace_normalized = scatter(x = wl_sort, y = spec_normalized, 
  mode = "lines", line_color = "red", name = "fit")

layout = 
  Layout(
    font = 
      attr(
        family="Open Sans",
        size = 18,
        color = "black"
      ),              
    title = 
      attr(
        text= string("Spectra from: ",infile),
        y=1.1,
        x=0.5,
        xanchor = "center",
        yanchor = "top"
      ),
    xaxis_title = "Wavelength (&#8491;)",
    yaxis_title = "Flux (Counts)"
  )
  
#p = Plot( [trace_spec, trace_fit], layout)
p = Plot( trace_normalized,  layout)           
browser(p)






      
