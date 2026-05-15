#!/usr/local/bin/julia

# fits_stack_running_median_differences
#
#   Difference an image stack to the running median of prior images
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
#   Copyright 2022
#   
#   2022-12-29 Version 1.01
#
#   2023-01-16 Version 1.1
#     File selection based on fits_stack_zdata added
#
#   2023-01-16 Version 1.11
#     Increased range of median for each slice
#
#   2023-01-19 Version 1.2
#     Corrects default configuration
#
#   2025-05-17 Version 1.3
#     Allows calibrated images in an FFI with extensions


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

global hdu = 1
     
# Read a configuration file to create and return a dictionary 
#   in_dir    => directory containing images to be measured
#   out_dir   => directory to save difference images
#   base_name => output file name prefix 
#   in_start  => serial index from 1 of first file to be used
#   instep    => step in number of files from the first one
#   in_slices => total number of files to be processed


function read_configuration(conf_file)
  
  dictionary = Dict()
  
  # Read the file

  dictionary["in_dir"] = "./"   
  dictionary["out_dir"] = "./"
  dictionary["base_name"] = "difference"
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
        
  end
   
  return dictionary

end


# Accept list of file names as command line arguments
# Return an array of file names

function get_files_by_name()

  nfiles = length(ARGS)
  nimages = nfiles - 1

  if nimages < 3
    println(" ")
    println("Usage: infile1.fits infile2.fits infile3.fits ... ")
    println(" ")
    println("Create a difference from a running median for files on the command line\n ")
    exit()
  else
    infiles = ARGS[1:nfiles]
  end

  return infiles
end  
    

# Input a directory
# Return an array of selected file names in that directory

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
    


# Build and return an image stack from an array of FITS file names
# The stack is ordered with [slice/nimages, column/width, row/height]

function build_image_stack(infiles)
  global hdu
  d = length(infiles)

  # Test for an FFI with extensions for the first image
  
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

    
# Input a stack of image data with images as the first index
# Return an image estimating  the local standard deviation of the kth image

function local_median(images, k)
  (d, w, h) = size(images)
  median_image = zeros(w,h)
  
  # Set range of median 
  
  r = 400
  
  # When k is r or less use r + 1 steps  into the future
  # Otherwise use r - 1 steps into the past

  if (k < (r+1) )
    for j in 1:h
      for i in 1:w
	median_image[i,j] = median(images[(k+1):(k+r),i,j])
      end   
    end       
  else
    for j in 1:h
      for i in 1:w
	median_image[i,j] = median(images[(k-r):(k-1),i,j])
      end   
    end   
  end
  return median_image
end


# Process the images to find the median 

function process_images()

  println("\n")
  println("To enable threading, use nproc and export \"JULIA_NUM_THREADS=nthreads\" \n") 

  println("Reading the configuration file median.conf \n")

  # Obtain the required configuration parameters

  configuration_file = "median.conf"
  median_conf = read_configuration(configuration_file)
  in_dir = median_conf["in_dir"]
  out_dir = median_conf["out_dir"]
  base_name = median_conf["base_name"]
  in_start = median_conf["in_start"]
  in_step =  median_conf["in_step"]
  in_slices =  median_conf["in_slices"]


  println("Acquiring a sequence of image file names from " * in_dir * "\n")
  
  select_files = get_files_by_directory(in_dir,in_start,in_step,in_slices) 

  nimages = length(select_files)

  println("Building the ", nimages, " image stack in memory \n")
  images = @time build_image_stack(select_files)
  

# Subtract the running median from each image and save the difference
  
  @threads for i in 1:nimages
    this_image = images[i,:,:]
    running_median_image = local_median(images, i) 
    difference_image = this_image .- running_median_image
    f = FITS(select_files[i])
    difference_header = read_header(f[hdu])
    close(f)    
    
    # Update the header date stamp
   
    file_time_str = string(DateTime(now()))
    difference_header["DATE"] = file_time_str

    push!(difference_header.keys, "COMMENT")
    comment_string = "running median difference"
    push!(difference_header.values, "")
    push!(difference_header.comments, comment_string)
    difference_header.map["COMMENT"] = length(difference_header.keys)

    # Save this difference as a FITS file

    difference_file =  out_dir * "/" * base_name * "_" * lpad(i,4,"0") * ".fits"
    difference_fits = FITS(difference_file, "w")
    write(difference_fits, Float32.(difference_image); header=difference_header)
    close(difference_fits)  
  end

  return nimages

end


# Process the stack

println("Differencing the stack to a running median \n")

nimages = @time process_images()

println("\n")
println("Differences from the median of ", nimages, " images have been saved", " \n")

exit()

