#!/usr/local/bin/julia

# fits_stack_zdata
#
#   Find pixel data through the z-axis of a stack of fits images
#
#   Explicit inputs:
#
#     Configuration file or use x and y on the command line
#
#   Explicit output:
#
#     Data files of signals versus slice 
#
#
#   John Kielkopf (kielkopf@louisville.edu)
#   MIT License
#   Copyright 2023
#   
 
#   2023-01-12 Version 1.0 
#     working with directory selection

#   2023-01-19 Version 1.1 
#     limits to file selection added
#     accepts floating point coordinates and rounds to integer indices

# Julia acknowledgments

#   Current documentation
#   See https://docs.julialang.org/en/v1/

#   Very helpful guidance from Wikibooks
#   See https://en.wikibooks.org/wiki/Introducing_Julia

#   Julia High Performance guides optimization
#   See https://juliahighperformance.com/

#   See https://juliaastro.github.io/dev/index.html

# Julia programming notes

#   FITSIO is high level interface to CFITSIO 
#   In REPL => Pkg.add("FITSIO")
#   In code => using  FITSIO does not require "FITSIO." before the functions
#   In code => import FITSIO requires "FITSIO."
#   See https://juliaastro.github.io/FITSIO.jl/stable/ for documentation

#   CFITSIO functions are thin wrappers around the CFITSIO C library routines
#   See https://juliaastro.github.io/CFITSIO.jl/dev/

#   Warning:  Julia is column major like Matlab and Fortran.
#   It is always the last dimension that is stored first 
#   with the values for that dimension one after the other in memory.
#   To optimize fast access to consecutively stored data
#   with a 2-dimensional array in for loop,  operate on it 
#   to vary the last dimension most slowly and sequentially
#   get the values in that "column" one after the other. In this
#   example x[i, j] is modified with "i" changing for each fixed "j" in 
#   the innermost loop. Here "i" runs down the column "j" of the 2x2 matrix. 
#
#      for j in 1:size(x, 2) 
#        for i in 1:size(x, 1) 
#          s = s + x[i, j] ^ 2   
#          x[i, j] = s           
#        end                   
#      end                    

#   When using threads declare this environment variable
#
#     export "JULIA_NUM_THREADS=16"
#
#   for the number of threads equal to the number of CPUs (nproc) available   


using FITSIO               # For FITS management
using Dates                # Date and time
using DelimitedFiles       # For exporting data
using Base.Threads         # For multiprocessing



     
# Read a configuration file to create and return a dictionary 
#   in_dir    => directory containing images to be measured
#   out_dir   => directory to save data files for each pixel
#   in_data   => input file name containing pixel coordinates as x,y pairs 
#   base_name => output file name prefix 
#   start     => serial index from 1 of first file to be used
#   step      => step in number of files from the first one
#   slices    => total number of files to be measured 


function read_configuration(conf_file)
  
  dictionary = Dict()
  
  # Read the file

  dictionary["in_dir"] = "./"   
  dictionary["out_dir"] = "./"
  dictionary["base_name"] = "zplot"
  dictionary["start"] = 1  
  dictionary["step"] = 1   
  dictionary["slices"] = 999999  
  
  conf_text = readlines(conf_file) 

  # Parse the text lines

  for line in conf_text 
  
    # Skip empty lines
    
    if length(line) < 1
      continue
    end  
                    
    # Skip comments marked by first character # or !

    if line[1] == '#'
      println(line)
      continue
    end  

    if line[1] == '!'   
      println(line)
      continue
    end  
    
    # Skip but warn of file issues
    
    if !occursin("=", line)
      println("This line ")
      println(line)
      println("was found without an = separator in ", conf_file)
      continue
    end
             
    # Test for valid entries and assign to arrays

    if occursin("in_dir", line)
      dictionary["in_dir"] = strip(split(line,"=")[2])
    end
    
    if occursin("out_dir", line)
      dictionary["out_dir"] = strip(split(line,"=")[2])
    end
    
    if occursin("base_name", line)
      dictionary["base_name"] = strip(split(line,"=")[2])
    end

    if occursin("in_data", line)
      dictionary["in_data"] = strip(split(line,"=")[2])
    end

    if occursin("in_start", line)
      in_start_str = strip(split(line,"=")[2])
      dictionary["in_start"] = parse(Int64, in_start_str)
    end

    if occursin("in_step", line)
      in_step_str = strip(split(line,"=")[2])
      dictionary["in_step"] = parse(Int64, in_step_str)
    end

    if occursin("in_slices", line)
      in_slices_str = strip(split(line,"=")[2])
      dictionary["in_slices"] = parse(Int64, in_slices_str)
    end
        
  end
  
  
  return dictionary

end


 
     
# Read a data file to create and return an array of pixels
# File contains space delimited x, y, and optional id entries on each line 
# x,y are integer coordinates and id is a string with no spaces
# id is an optional string identifier for this pixel
# One pixel to a line
# The line may contain additional data which will be ignored


function read_data(data_file)
  
  data_text = readlines(data_file) 

  # Parse the text lines
  
  npix = 0
  
  # Initialize pixels
  
  pixels = []
  
  for line in data_text 
                        
    # Skip an empty line
    
    if length(line) < 1
      continue
    end
        
    # Skip comments marked by first character # or !

    if line[1] == '#'
      println(line)
      continue
    end  

    if line[1] == '!'   
      println(line)
      continue
    end  
    
    # Build pixel database with x, y, and id string
    # Input x and y may be floating point and are rounded to integer
    
    items = split(line)
    if length(items) == 3    
      npix = npix + 1
      x = round(Int64,parse(Float64,items[1]))
      y = round(Int64,parse(Float64,items[2]))
      id = items[3]
      newpixel = [x,y,id]
      push!(pixels, newpixel)    
    elseif length(items) == 2
      npix = npix + 1
      x = round(Int64,parse(Float64,items[1]))
      y = round(Int64,parse(Float64,items[2]))
      id = lpad(string(npix), 3, '0')
      newpixel = [x,y,id]
      push!(pixels, newpixel)         
    end      
          
  end
  
  if npix == 0
    println("\n")
    println("No pixels were specified in the data file \n")
    exit()
  end  
  
  return pixels

end
    

# Input a directory
# Return an array of selected file names in that directory

function get_files_by_directory(in_dir,in_start,in_step,in_slices)

  in_files = readdir(in_dir)
  file_count = length(in_files)

  if file_count < 2
    println(" ")
    println("Usage:  fits_stack_bin.jl ")
    println(" ")
    println("Samples images from a time- or z-axis stack \n")
    println("Defaults to the current working directory or use zdata.conf \n")
    println("Requires 2 or more files \n")
    exit()
  end
  
  in_end = min(file_count, in_start + (in_slices - 1)*in_step)

  select_files = []
  
  for i in in_start:in_step:in_end
    push!(select_files, in_dir * "/" * in_files[i])
  end
    
  return select_files
end  
    

# Build and return image and header stacks from an array of FITS file names
# Accepts standard and some non-standard keywords such as
#   DATE-OBS (observed CCD frames and FFIs) string in UTC format yyyy-mm-ddTHH:MM:SS.s
#   STARTTJD (TICA files) floating point relative JD in TESS time
#   EXPOSURE (observed CCD frames) seconds
#   EXPOSURE (TESS FFIs) day
#   LIVETIME (TESS FFIs) day
#   EXPTIME (TICA files) seconds

function build_stacks(fits_files)
  
  d = length(fits_files)
  
  f = FITS(fits_files[1])
  (w, h) = size(f[1])
  first_header = read_header(f[1])
  close(f)

  # Initialize the image stack using the size of the first image
  images = zeros(d, w, h)
  
  # Initialize the header stack using the first image header
  headers = [first_header]
   
  # Sequentially add images and headers from the files to the stacks
  
  for i in 1:d   

    f = FITS(fits_files[i])
    image = read(f[1])
    (width, height) = size(f[1])
    header = read_header(f[1])
    close(f)
    
    if (w != width) & (h != height)
      println("Warning: image file " * fits_files[i] * " has a anomalous size")
      exit()
    end

    # Assign the new image into the initialized stack
    # such that each pixel has its sliced data sequentia in memory
    
    # Multiprocess with a for loop 
    # rather than single process  with images[i, :, :] .= image
    
    @threads for k in 1:h
      for j in 1:w
        images[i, j, k] = image[j,k]
      end         
    end
        
    if i != 1
      headers = push!(headers, header)
    end
  
  end  
   
  # Return the stacks
  
  return headers, images

end  


# Write a 2-column data file of  x and y vectors
# Requires using DelimitedFiles at top level

function write_xy_data(out_file, x_array, y_array) 

  open(out_file, "w") do io
    writedlm(io, [x_array y_array])
  end

end


# Process the requested images
#   Read the configuration file instructions from the current working
#   Acquire a list of FITS files to sample from the input directory
#   Acquire a list of pixels to sample
#   Create z-axis data for each pixel
#   Plot this data
#   Save the data and plots in files for each pixel

function process_images()
  
  # Obtain the required configuration parameters

  configuration_file = "zdata.conf"
  println("Reading the zdata configuration file")
  zdata_conf = read_configuration(configuration_file)
  in_dir = zdata_conf["in_dir"]
  out_dir = zdata_conf["out_dir"]
  base_name = zdata_conf["base_name"]
  in_data = zdata_conf["in_data"]
  in_start = zdata_conf["in_start"]
  in_step =  zdata_conf["in_step"]
  in_slices =  zdata_conf["in_slices"]
  
  println("Acquiring a sequence of image file names from " * in_dir)
  select_files = get_files_by_directory(in_dir,in_start,in_step,in_slices) 
    
  println("Building the ", length(select_files), " input image and header stacks")
  headers, frames = @time build_stacks(select_files)
  
  (d, w, h)  = size(frames)  
 
  println("Acquiring the list of pixels to be sampled")
  pixels = read_data(in_data)
  
  println("Extracting time-series data from the stack for each pixel")
  for pixel in pixels

    (x,y,id) = pixel
    signal = []
    time = [] 

    for i in 1:d
          
      # The signal at this pixel for this frame
      
      push!(signal,frames[i,x,y])
      
      # The start time or index number of this frame
      # Use BJD if available
      # For TESS TICA use TJD
      # Otherwise index by frame number
      
      if haskey(headers[i], "BJD_TDB")
        push!(time,headers[i]["BJD_TDB"])
      elseif haskey(headers[i], "STARTTJD") 
        push!(time, headers[i]["STARTTJD"])
      else
        push!(time, i)  
      end
       
    end

    out_file = out_dir * "/" * base_name * "_" * id * ".dat"
     
    # Save these pixel data
    write_xy_data(out_file, time, signal)
    
  
  end

end

process_images()

exit()
