#!/usr/local/bin/julia

# fits_stack_background_subtract
#
#   Difference an image stack to the background at each pixel
#
#   Explicit input:
#
#     Directory of FITS files to be processed
#
#   Explicit output:
#
#     Difference image for each image in the original stack
#
#
#   John Kielkopf (kielkopf@louisville.edu)
#   MIT License
#   Copyright 2023
#   
#   2023-01-17 Version 1.0
#     Working and limited by available memory
#
#   2023-01-21 Version 1.1
#     Runs batches of files 


# Julia language notes

#   Current documentation
#   See https://docs.julialang.org/en/v1/

#   Very helpful guidance from Wikibooks
#   See https://en.wikibooks.org/wiki/Introducing_Julia

#   Julia High Performance guides optimization
#   See https://juliahighperformance.com/

#   See https://juliaastro.github.io/dev/index.html

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
#   to vary the last dimension most slowly and sequentially to
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

#   Optimize for speed by using the first index for each frame


#   When using threads declare this environment before running the code
#
#   export "JULIA_NUM_THREADS=4"
#
#   for the number of threads equal to the number of CPUs (nproc) available   


using FITSIO               # For FITS management
using Dates                # Date and time
using Base.Threads         # For multiprocessing
using Statistics           # For mean, median, sigma

     
# Read a configuration file to create and return a dictionary 
#   in_dir    => directory containing images to be measured
#   out_dir   => directory to save difference images
#   base_name => output file name prefix 
#   start     => serial index from 1 of first file to be used
#   step      => step in number of files from the first one
#   slices    => total number of files to be processed
#   offset    => pixel offset to determine the background

function read_configuration(conf_file)
  
  dictionary = Dict()

  dictionary["in_dir"] = "./"
  dictionary["out_dir"] = "./"
  dictionary["base_name"] = "subtracted"
  dictionary["in_start"] = 1
  dictionary["in_step"] = 1
  dictionary["slices"] = 99999
  dictionary["offset"] = 3

  # Read the file

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
             
    # Test for valid configuration items and assign to a dictionary entry

    if occursin("in_dir", line)
      dictionary["in_dir"] = strip(split(line,"=")[2])
    end
    
    if occursin("out_dir", line)
      dictionary["out_dir"] = strip(split(line,"=")[2])
    end
    
    if occursin("base_name", line)
      dictionary["base_name"] = strip(split(line,"=")[2])
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

    if occursin("offset", line)
      offset_str = strip(split(line,"=")[2])
      dictionary["offset"] = parse(Int64, offset_str)
    end
        


  end
   
  return dictionary

end


# Input from a specified directory
# Return an array of selected file names 
# It is very unlikely this array will stress available memory

function get_files_by_directory(in_dir,in_start,in_step,in_slices)

  in_files = readdir(in_dir)
  file_count = length(in_files)

  if file_count < 3
    println(" ")
    println("Requires 3 or more files \n")
    exit()
  end
  
  in_end = min(file_count, in_start + (in_slices - 1)*in_step)

  select_files = []
  
  for i in in_start:in_step:in_end
    push!(select_files, in_dir * "/" * in_files[i])
  end
    
  return select_files
end  
    


# Background for a pixel 
# Use the median of values in its neighborhood 
# Should have r large enough to extend beyond the PSF of a star   

function local_background(image,r)
  (w, h) = size(image)
  background_image = 0.0 * image

  for j in 1:h
    for i in 1:w
      imin = max(1, (i - r))
      imax = min(w, (i + r))
      jmin = max(1, (j - r))
      jmax = min(h, (j + r))      
      background_image[i,j] = median(image[imin:imax,jmin:jmax])
    end   
  end       

  return background_image
end


# Process the images to find the median 

function process_images()

  println("\n")
  println("To enable threading, use nproc and export \"JULIA_NUM_THREADS=nthreads\" \n") 

  println("Reading the configuration file background.conf \n")

  # Obtain the required configuration parameters

  configuration_file = "background.conf"
  background_conf = read_configuration(configuration_file)
  in_dir = background_conf["in_dir"]
  out_dir = background_conf["out_dir"]
  base_name = background_conf["base_name"]
  in_start = background_conf["in_start"]
  in_step =  background_conf["in_step"]
  in_slices =  background_conf["in_slices"]
  offset = background_conf["offset"]


  println("Acquiring a sequence of image file names from " * in_dir * "\n")
  
  select_files = get_files_by_directory(in_dir,in_start,in_step,in_slices) 

  nselect = length(select_files)

  println("Removing background from each of ", nselect, " images \n")
 

# Remove the background from each image and save the new image
    
  @threads for i in 1:nselect
    f = FITS(select_files[i])
    this_image = read(f[1])
    difference_header = read_header(f[1])
    close(f)
    
    background_image = local_background(this_image, offset) 
    difference_image = this_image .- background_image
  
    
    # Update the header date stamp
   
    file_time_str = string(DateTime(now()))
    difference_header["DATE"] = file_time_str

    push!(difference_header.keys, "COMMENT")
    comment_string = "background difference"
    push!(difference_header.values, "")
    push!(difference_header.comments, comment_string)
    difference_header.map["COMMENT"] = length(difference_header.keys)

    # Save this difference as a FITS file

    difference_file =  out_dir * "/" * base_name * "_" * lpad(i,4,"0") * ".fits"
    difference_fits = FITS(difference_file, "w")
    write(difference_fits, Float32.(difference_image); header=difference_header)
    close(difference_fits)  
  end

  return nselect

end


# Process the stack

println("Differencing the stack to a running median \n")

nselect = @time process_images()

println("\n")
println("Differences from the local background of ", nselect, " images have been saved", " \n")

exit()

