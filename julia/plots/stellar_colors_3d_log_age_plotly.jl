#!/usr/local/bin/julia

using PlotlyJS
#using LaTeXStrings

# Read a 5-column file and return  a, z, y, z and data tag arrays

function read_data_file(infile) 
  
  data_text = readlines(infile) 

  # Pre-define empty data arrays
  
  tags = []
  a_data = zeros(0)
  x_data = zeros(0) 
  y_data = zeros(0)
  z_data = zeros(0)
   

  # Parse the data lines into the values

  for line in data_text 

    # Skip comment line markers by testing for marker characters
    
    if line[1] == '#'
       
      continue
    
    end 
    
    if line[1] == '!' 
       
      continue
    
    end 
   
    # Skip a line without numerical data but include lines without tags

    if length(line) <= 4
      
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

    if length(entry) == 5
      label = entry[1]
      a = parse(Float64,entry[2])
      x = parse(Float64,entry[3])
      y = parse(Float64,entry[4])
      z = parse(Float64,entry[5])
      
    elseif length(entry) == 4
    
      a = parse(Float64,entry[1])
      x = parse(Float64,entry[2])
      y = parse(Float64,entry[3])
      z = parse(Float64,entry[4])
      label = " "     
 
    else
    
      continue
     
    end
    
    push!(a_data, a)                         
    push!(x_data, x) 
    push!(y_data, y)
    push!(z_data, z)
    push!(tags, label)

  end    

  # Return vectors
  
  return a_data, x_data, y_data, z_data, tags 

end 


# Plot in a browser window using its engine for interaction and save html

function browser(p::Plot)
  tmp_filename = "plot.html"
  savefig(p, tmp_filename)
  run(`google-chrome $tmp_filename`)
end

# Accept data file as command line argument
# Warn if missing and exit
# Return input filename 

function get_commandline_arguments()

  if length(ARGS) == 1
    infile = ARGS[1]     
  else
    println("Use a data file name on the command line\n")
    exit() 
  end
      
  return infile
end

# Use the commandline to provide the file

infile  =  get_commandline_arguments()

# Read the 5 columns into arrays

a_data, x_data, y_data, z_data, tags  = read_data_file(infile)

# Use a layout for the formatting

layout = 
  Layout(
    # Instead of title_text, use a title_dictionary
    # title_text = "Data from "*infile,
    title = attr(
        text = "<b> Data from "*infile*" </b>", 
        x = 0.5, 
        xanchor = "center"   
    ),

    scene = attr(
      xaxis = attr(title="<b>g-r</b>"),
      yaxis = attr(title="<b>r-i</b>"),
      zaxis = attr(title="<b>i-z</b>")
    )      
  )

bluescale = [
    [0.0, "rgb(60, 120, 240)"],    # Start of the scale 
    [0.5, "rgb(0, 120, 180)"],    # Middle of the scale 
    [1.0, "rgb(240, 120, 60)"]       # End of the scale 
]

# Scatter 3D  trace

trace = 
  scatter(
    x=x_data,
    y=y_data,
    z=z_data,
    text=tags,
    mode="markers",
    hovertemplate = 
        "<b>%{text}</b><br>" * # Custom label from the 'text' attribute
        "g-r: %{x}<br>" * # Display the x-value
        "r-i: %{y}<br>" * # Display the y-value
        "i-z: %{z}" * # Display the z-value                
        "<extra></extra>", # Removes the secondary box with the trace name
    marker = attr(
      size=12,
      color=log10.(a_data),
      #colorscale="Veridis", # Append _r to reverse the scale, e.g. Blues_r
      colorscale = bluescale,
      showscale=true,
      opacity=0.8
    ),  
    type="scatter3d"
  )


# Create a scatter plot using PlotyJS with a layout

p = Plot(trace,layout)

# Save the plot in a file and display it using the browser's web engine

browser(p)

exit()
