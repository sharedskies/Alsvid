#!/usr/local/bin/julia


#   Read a 2-column file
#   Plot it with an interactive display in a browser

#   John Kielkopf (kielkopf@louisville.edu)
#   MIT License
#   Copyright 2024-2025
#   
#   2024-11-20 Version 1.0
#   2025-01-25 Version 1.1 

using PlotlyJS        # Interactive browser plotting
using CurveFit        # Fitting the continuum
using DelimitedFiles  # For exporting formatted data files

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

  if length(ARGS) == 1
    infile = ARGS[1]     
  else
    println("Use file name on the command line\n")
    exit() 
  end
  
# Use strings for the filename and the fiber number
# If a number is required, use parse(fiberstr)
    
  return infile
end  
    
# ###

# Write a 2-column data file of  x and y vectors
# Requires using DelimitedFiles at top level

function write_data_file(outfile, x_array, y_array) 

  open(outfile, "w") do io
    writedlm(io, [x_array y_array])
  end

end


infile  =  get_commandline_arguments()
wl, spec  = read_data_file(infile)
nwl = size(wl)[1]

# Generate plot with PlotlyJS

trace = scatter(x = wl, y = spec, 
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
    #xaxis_title = "Wavelength (&#8491;)",
    #yaxis_title = "Flux (Counts)"
    xaxis_title = "X",
    yaxis_title = "Y"
  )
  
p = Plot( trace,  layout)           
browser(p)






      
