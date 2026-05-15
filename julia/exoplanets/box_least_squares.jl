#!/usr/local/bin/julia


#   Read a 2-column file
#   Process it with a box least squares (BLS) search
#   Process it with a Lomb Scargle search
#   Plot it with an interactive display in a browser

#   John Kielkopf (kielkopf@louisville.edu)
#   MIT License
#   Copyright 2025
#   
#   2025-01-25 Version 0.9

using PlotlyJS        # Interactive browser plotting
using CurveFit        # Fitting the continuum
using DelimitedFiles  # For exporting formatted data files
using LombScargle
using BoxLeastSquares

# ###

# Read a 2-column data file and return  x and y vectors

function read_data_file(infile) 
  
  data_text = readlines(infile) 

  # Pre-define empty data arrays of type Float64
  
  x_data = zeros(0) 
  y_data = zeros(0) 

  # Parse the data lines into the values

  for line in data_text 

    # Skip comment line markers by testing for marker characters
    
    if line[1] == '#'
       
      continue
    
    end 
    
    if line[1] == '!' 
       
      continue
    
    end 
   
    # Skip an empty line

    if length(line) <= 2
      
      continue
    
    end      
         
                 
    # Separate entries in a data line using common delimiters
    
    # Function occursin requires two string arguments (needle, haystack)  
           
    if occursin(",", line)
            
      entry = split(line,",")       
        
    # Otherwise try separated or tabbed entries
    
    else
    
      entry = split(line)
        
    end
            
    # Test for successful splitting into two data entries
    # Skip any that do not work

    if length(entry) != 2
      
      continue
    
    end
        
    x = parse(Float64,entry[1])
    y = parse(Float64,entry[2])
                     
    push!(x_data, x) 
    push!(y_data, y)

  end    

  # Return two Float64 vectors
  
  return x_data, y_data 

end 



# ###

# Plot in a browser window using its engine for interaction
# For the PlotlyJS API see https://plotly.com/julia/reference/surface/
# For layout see https://plotly.com/julia/reference/layout/coloraxis/

function browser(p::Plot)
  tmp_filename = "plot.html"
  savefig(p, tmp_filename)
  run(`google-chrome $tmp_filename`)
  #run(`firefox $tmp_filename`)
end

# ###

# Accept data file as command line argument
# Warn if missing and exit
# Return input filename 

function get_commandline_arguments()
  duration = 0.1  
  infile = "bls.dat"
  if length(ARGS) == 1
    infile = ARGS[1]
  elseif length(ARGS) == 2 
    infile = ARGS[1]
    duration = parse(Float64, ARGS[2])
  else
    println("Use file name on the command line\n")
    exit() 
  end
  
# Use strings for the filename and a number
# If a number is required, use parse(number)
  println("Reading file ", infile, " for BLS search of ", duration, " event")    
  return infile, duration
end  
    
# ###

# Write a 2-column data file of  x and y vectors
# Requires using DelimitedFiles at top level

function write_data_file(outfile, x_array, y_array) 

  open(outfile, "w") do io
    writedlm(io, [x_array y_array])
  end

end

infile ="bls.dat"
duration = 1.0/12.0
(infile, duration) = get_commandline_arguments()
println(infile, " ", duration)

t, s  = read_data_file(infile)

# Include for testing

#t1 = t[1]
#t = t .- t1
#s = 1.0 .+ sinpi.(2.0*t/0.29)
#nts = size(t)[1]
#plan = LombScargle.plan(t, s)

# Run BLS on this data


bls_result = BLS(t, s, 0.01*s; duration)
println(BoxLeastSquares.params(bls_result))
period = BoxLeastSquares.periods(bls_result)
power = BoxLeastSquares.power(bls_result)

# Run the Lomb-Scargle search and return the power spectrum

#periodogram = lombscargle(t,s, samples_per_peak=10, maximum_frequency=12.0)
#(frequency, power) = LombScargle.freqpower(periodogram)



# Generate plot of input data with PlotlyJS

trace = scatter(x = t, y = s, 
  name = infile, mode = "markers")

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
        text= string("Data from: ",infile),
        y=1.1,
        x=0.5,
        xanchor = "center",
        yanchor = "top"
      ),
    xaxis_title = "Time",
    yaxis_title = "Signal"
  )
  
indata_plot = Plot( trace,  layout)           
browser(indata_plot)


# Generate plot of BLS period data with PlotlyJS

trace = scatter(x = period, y = power, 
  name = infile, mode = "markers")

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
        text= string("BLS Power from: ",infile),
        y=1.1,
        x=0.5,
        xanchor = "center",
        yanchor = "top"
      ),
    xaxis_title = "Period",
    yaxis_title = "Power"
  )
  
ls_plot = Plot( trace,  layout)           
browser(ls_plot)

# Export BLS data

write_data_file("bls.dat", period, power)





      
