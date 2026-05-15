#!/usr/local/bin/julia

# fits_stack_mean
#
#   Mean, median, and sigma images from a stack of images
#
#   Explicit input:
#
#     Directory of FITS files to be processed
#
#   Explicit output:
#
#     Mean, median, difference mean-median,  and sigma of the image stack
#
#
#   John Kielkopf (kielkopf@louisville.edu)
#   MIT License
#   Copyright 2023
   
#   2022-12-29 Version 1.01
#     Working to deliver mean, median, and sigma of all files in a directory

#   2023-01-22 Version 1.1
#     Added configuration file that is used if nothing is on the command line
#
#   2025-05-17 Version 1.2
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
  dictionary["base_name"] = "stack_"
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
    println("Create a mean image of files on the command line\n ")
    exit()
  else
    infiles = ARGS[1:nfiles]
  end

  return infiles
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

    

# Input a stack of image data and return the mean, median and sigma through the stack

function stack_mean_median_sigma(images)
  (d, w, h) = size(images)
  mean_image = zeros(w, h)
  median_image = zeros(w,h)
  sigma_image = zeros(w,h)
  @threads for j in 1:h
    for i in 1:w
      mean_image[i,j] = mean(images[:,i,j])
      median_image[i,j] = median(images[:,i,j])
      sigma_image[i,j] = std(images[:,i,j]) 
    end   
  end    
  return mean_image, median_image, sigma_image
end


# Process the images to find the mean, median, and sigma 

function process_images()

  global hdu

  println("\n")
  println("To enable threading, use nproc and export \"JULIA_NUM_THREADS=nthreads\" \n") 

  println("Expecting a command line with in_dir out_dir or a median.conf configuration \n")
  
  # Check for items on the command line
  
  if length(ARGS) == 2
    in_dir = ARGS[1]
    out_dir = ARGS[2]
    in_start = 1
    in_step = 1
    in_slices = 99999
  else
  
    println("Reading the configuration file median.conf \n")

    # Obtain the required configuration parameters

    configuration_file = "median.conf"
    median_conf = read_configuration(configuration_file)
    in_dir = median_conf["in_dir"]
    out_dir = median_conf["out_dir"]
    base_name = median_conf["base_name"]
    in_start = median_conf["in_start"]
    in_step =  median_conf["in_step"]
    in_slices = median_conf["in_slices"]
  
  end



  println("Acquiring image file names \n")

  select_files = get_files_by_directory(in_dir,in_start,in_step,in_slices) 

  nselect = length(select_files)

  println("Building the image stack in memory \n")
  images = @time build_image_stack(select_files)

  println("\n")
  println("Computing the mean, median, and sigma through the stack \n")
  mean_image, median_image, sigma_image = @time stack_mean_median_sigma(images)
  
  # Use the header of the first file for the stack
  
  f = FITS(select_files[1])
  first_header = read_header(f[hdu])
  close(f)
  
  # Update the header date stamp
 
  file_time_str = string(DateTime(now()))
  first_header["DATE"] = file_time_str
    

  # Augment the header of the first image and use it for the mean image

  mean_header = first_header
  push!(mean_header.keys, "COMMENT")
  comment_string = "mean of "*string(nselect)*" images"
  push!(mean_header.values, "")
  push!(mean_header.comments, comment_string)
  mean_header.map["COMMENT"] = length(mean_header.keys)

  # Save this mean as a FITS file

  mean_file = out_dir * "/"  * base_name * "mean.fits"
  mean_fits = FITS(mean_file, "w")
  write(mean_fits, Float32.(mean_image); header=mean_header)
  close(mean_fits) 

  # Augment the header of the first image and use it for the median image

  median_header = first_header
  push!(median_header.keys, "COMMENT")
  comment_string = "median of "*string(nselect)*" images"
  push!(median_header.values, "")
  push!(median_header.comments, comment_string)
  median_header.map["COMMENT"] = length(median_header.keys)

  # Save this median as a FITS file

  median_file = out_dir * "/" * base_name * "median.fits"
  median_fits = FITS(median_file, "w")
  write(median_fits, Float32.(median_image); header=median_header)
  close(median_fits) 
   
  # Augment the header of the first image and use it for the sigma image

  sigma_header = first_header
  push!(sigma_header.keys, "COMMENT")
  comment_string = "sigma of "*string(nselect)*" images"
  push!(sigma_header.values, "")
  push!(sigma_header.comments, comment_string)
  sigma_header.map["COMMENT"] = length(sigma_header.keys)

  # Save this sigma as a FITS file

  sigma_file = out_dir * "/" * base_name * "sigma.fits"
  sigma_fits = FITS(sigma_file, "w")
  write(sigma_fits, Float32.(sigma_image); header=sigma_header)
  close(sigma_fits) 

  # Calculate the mean minus the median and save it as a FITS file

  delta_image = mean_image .- median_image
  delta_header = first_header
  push!(delta_header.keys, "COMMENT")
  comment_string = "mean minus median of "*string(nselect)*" images"
  push!(delta_header.values, "")
  push!(delta_header.comments, comment_string)
  delta_header.map["COMMENT"] = length(delta_header.keys)

  # Save this delta as a FITS file

  delta_file = out_dir * "/"  * base_name * "mean_minus_median.fits"
  delta_fits = FITS(delta_file, "w")
  write(delta_fits, Float32.(delta_image); header=delta_header)
  close(delta_fits) 

  return nselect, out_dir

end

# Process the requested images

nselect, out_dir = @time process_images()


println("\n")
println("Mean, median, difference, and sigma of a stack of ", nselect, 
" images have been saved ", out_dir," \n")


exit()

