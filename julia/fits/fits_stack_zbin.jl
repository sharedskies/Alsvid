#!/usr/local/bin/julia

# fits_stack_zbin
#
#   Sliding binning through an image stack 
#
#   Explicit input:
#
#     Configuration file or defaults
#
#   Explicit output:
#
#     New files binned through the stack
#
#
#   John Kielkopf (kielkopf@louisville.edu)
#   MIT License
#   Copyright 2025
#   
#   2025-05-22 Version 1.0
#     Built from fits_stack_running_median_differences.jl


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
#   in_dir    => [./] directory containing images to be measured
#   out_dir   => [./] directory to save difference images
#   base_name => ["zbin_"] output file name prefix 
#   n_start   => [1] serial index from 1 for first file to be used
#   n_bin     => [4] number to bin 
#   n_total   => [99999] total number of files process start to end
#   
#   Reverts to default if there is no entry or no configuration file

function read_configuration(conf_file)
  
  dictionary = Dict()
  
  # Read the file

  dictionary["in_dir"] = "./"   
  dictionary["out_dir"] = "./"
  dictionary["base_name"] = "zbin"
  dictionary["n_start"] = 1  
  dictionary["n_bin"] = 4   
  dictionary["n_total"] = 999999  
  
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
      n_start_str = strip(split(line,"=")[2])
      dictionary["n_start"] = parse(Int64, n_start_str)
    end

    if occursin("n_bin", line)
      n_step_str = strip(split(line,"=")[2])
      dictionary["in_step"] = parse(Int64, n_step_str)
    end

    if occursin("in_slices", line)
      n_total_str = strip(split(line,"=")[2])
      dictionary["in_total"] = parse(Int64, n_total_str)
    end
        
  end
   
  return dictionary

end


# Input a directory limited by file count
# Return an array of selected file names in that directory

function get_files_by_directory(in_dir, n_start, n_total)

  in_files = readdir(in_dir)
  file_count = length(in_files)

  if file_count < 3
    println(" ")
    println("Requires 3 or more files \n")
    exit()
  end
  
  n_stop = min(file_count, n_start + n_total - 1)

  select_files = []
  
  for i in n_start:n_stop
    push!(select_files, in_dir * "/" * in_files[i])
  end
    
  return select_files
end  
    


# Build and return an image stack from an array of FITS file names
# Uses calibrated image if extended FITS TESS FFIs from SPOC on MAST
# The stack is ordered with [slice/nimages, column/width, row/height]

function build_image_stack(infiles)
  global hdu
  d = length(infiles)

  # Test for an FFI with extensions for the first image
  # Set hdu for TESS SPOC FFIs
  
  f = FITS(infiles[1])
  if length(f) == 1  
    global hdu = 1
  elseif length(f) == 3
    global hdu = 2
  else
    println("Unknown type of FITS file reports ", length(f), " HDUs")
    exit()
  end      
  (w, h) = size(f[hdu])
  close(f)

  # Initialize the image stack using the size of the first image
  # Note ordering is explicit in the structure of the images array
  images = zeros(d, w, h)
  
  # Sequentially add images such that the image frame is the slowest index
  
  for i in 1:d   

    f = FITS(infiles[i])
    image = read(f[hdu])
    (width, height) = size(f[hdu])
    close(f)
    
    if (w != width) & (h != height)
      println("Warning: image file " * infiles[i] * " has a anomalous size")
      exit()
    end

    # Assign the new image into the initialized stack
    # such that each pixel has its sliced data sequentially in memory
     
    # Could run a single process  with images[i, :, :] .= image
    # Multiprocessing with threads is faster
    
    @threads for k in 1:h
      for j in 1:w
        images[i, j, k] = image[j,k]
      end   
    end  
    
  end  
   
  # Return the image stack 
  
  return images

end  


# Sum images in a stack starting at s over range r
    
function local_sum(images, s, r)

  # What do we have to work with?
  (d, w, h) = size(images)
  
  # Initialize sum with zeros
  sum_image = zeros(w,h)
  
  # Assure that start is within range
  start = max(s, 1)
  start = min(start, d)
  
  # Assure stop is within range
  stop = min(start + r - 1, d)

  # For every pixel in the stack, sum through the stack over s to s+r-1 images 
  @threads for j in 1:h
    for i in 1:w
      sum_image[i,j] = sum(images[start:stop,i,j])
    end   
  end       
  return sum_image
end



# Process the image stack into binned images associated with leading image of each bin

function process_images()

  
  println("\n")
  println("To enable threading, use nproc and export \"JULIA_NUM_THREADS=nthreads\" \n") 

  println("Reading the configuration file median.conf \n")

  # Obtain the required configuration parameters

  configuration_file = "zbin.conf"
  zbin_conf = read_configuration(configuration_file)
  in_dir =    zbin_conf["in_dir"]
  out_dir =   zbin_conf["out_dir"]
  base_name = zbin_conf["base_name"]
  n_start =   zbin_conf["n_start"]
  n_bin =     zbin_conf["n_bin"]
  n_total =   zbin_conf["n_total"]


  println("Acquiring a sequence of image file names from " * in_dir * "\n")
  
  select_files = get_files_by_directory(in_dir, n_start, n_total) 

  nimages = length(select_files)

  println("Building the ", nimages, " image stack in memory \n")
  images = @time build_image_stack(select_files)
  

  # Sliding bin along the stack
  
  @threads for i in 1:nimages
    this_image = images[i,:,:]
    sum_image = local_sum(images, i, n_bin) 

    # Copy the header for the sum image from the first image of the sum sequence
    f = FITS(select_files[i])
 
    # For TESS FFIs use the calibrated image and header
    if length(f) == 1  
      hdu = 1
    elseif length(f) == 3
      hdu = 2
    else
      println("Unknown type of FITS file reports ", length(f), " HDUs")
      exit()
    end      
 
    sum_header = read_header(f[hdu])
    close(f)    
    
    # Update the header date stamp
   
    file_time_str = string(DateTime(now()))
    sum_header["DATE"] = file_time_str

    push!(sum_header.keys, "COMMENT")
    comment_string = "Running sum of " * string(n_bin)
    push!(sum_header.values, "")
    push!(sum_header.comments, comment_string)
    sum_header.map["COMMENT"] = length(sum_header.keys)

    # Save this sum as a new FITS file

    sum_file =  out_dir * "/" * base_name * lpad(i,4,"0") * ".fits"
    sum_fits = FITS(sum_file, "w")
    write(sum_fits, Float32.(sum_image); header=sum_header)
   
    close(sum_fits)  
  end

  return nimages

end


# Process the stack

println("Binning images through the stack \n")

nimages = @time process_images()

println("\n")
println("These ", nimages, " images have been saved", " \n")

exit()

