#!/usr/local/bin/julia

# fits_stack_bin
#
#   Create binned images from a sequence  of fits images
#
#   Explicit inputs:
#
#     Configuration file or use defaults
#
#   Explicit output:
#
#     Stack of images binned from  the image stack
#
#
#   John Kielkopf (kielkopf@louisville.edu)
#   MIT License
#   Copyright 2021
#   
#   2021-07-22 Version 1.0

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
#     export "JULIA_NUM_THREADS=4"
#
#   for the number of threads equal to the number of CPUs available   


using FITSIO               # For FITS management
using Dates                # Date and time
using Statistics           # For median
using Base.Threads         # For multiprocessing


# ###
     
# Read a configuration file to create and return a dictionary
#   n_bins    => number of input images to one output binned images 
#   in_dir    => directory containing only images to be binned 
#   out_dir   => pre-existing directory for binned images 
#   base_name => output file name prefix  


function read_configuration(conf_file)
  
  dictionary = Dict()
  
  # Read the file
  
  conf_text = readlines(conf_file) 

  # Parse the text lines

  for line in conf_text 
                    
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
        
    item = split(line,"=")
    
    # Check for "=" in this line
    
    if !occursin("=", line)
      println("Error in the configuration file at this line ", line)
      println("Check for an item without an = separator in ", conf_file)
      exit
    end
    
    # There should be only 2 items on each line after the split

    if length(item) != 2
      println("Error in the configuraiton file at line ", line)
      println("Check for an ambiguous item in ", conf_file)
      exit   
    end
 
    # Test for entries removing whitespace from text

    if occursin("in_dir", line)
      dictionary["in_dir"] = strip(split(line,"=")[2])
    end
    
    if occursin("out_dir", line)
      dictionary["out_dir"] = strip(split(line,"=")[2])
    end
    
    if occursin("base_name", line)
      dictionary["base_name"] = strip(split(line,"=")[2])
    end
        
    if occursin("n_bins", line)
      dictionary["n_bins"] = parse(Int64,split(line,"=")[2])
    end

  end
  
  return dictionary

end
    

# Input a stack of image data with images as the first index
# Return a median image through the stack

function stack_median(images)
  (d, w, h) = size(images)
  median_image = zeros(w, h)
  @threads for j in 1:h
    for i in 1:w
      median_image[i,j] = median(images[:,i,j])
    end   
  end    
  return median_image
end


# Input a stack of image data with images as the first index
# Return a mean image through the stack

function stack_mean(images)
  (d, w, h) = size(images)
  mean_image = zeros(w, h)
  @threads for j in 1:h
    for i in 1:w
      mean_image[i,j] = mean(images[:,i,j])
    end   
  end    
  return mean_image
end



# Input a stack of image data and the number of bins n_bins
# Return a stack of images binned n_times as the first index

function bin_images(images, n_bins)
  (n_in, w, h) = size(images)
  n_out = Int64(floor(n_in/n_bins))
  binned_images = zeros(n_out,w,h)
  high_bin = 0
  for i in 1:n_out
    low_bin = high_bin + 1
    high_bin = high_bin + n_bins
    bins = low_bin:high_bin
    @threads for k in 1:h
      for j in 1:w
        binned_images[i,j,k] = sum(images[bins,j,k])
      end   
    end
  end      
  return binned_images
end


# Input a stack of headers and number of bins n_bins
# Return a stack of headers for the images binned n_bins times
# Each binned image header is based on the source images in that bin
# Accepts standard and some non-standard keywords in source headers such as
#   DATE-OBS (observed CCD frames and FFIs) string in UTC format yyyy-mm-ddTHH:MM:SS.s
#   STARTTJD (TICA files) floating point relative JD in TESS time
#   EXPOSURE (observed CCD frames) seconds
#   EXPOSURE (TESS FFIs) day
#   LIVETIME (TESS FFIs) day
#   EXPTIME (TICA files) seconds

function bin_headers(headers, n_bins)
 
  binned_headers = [headers[1],]
  (n_in, ) = size(headers) 
  n_out = Int64(floor(n_in/n_bins))
  high_bin = 0
  for i in 1:n_out
    low_bin = high_bin + 1
    high_bin = high_bin + n_bins
    if i > 1
      binned_headers = push!(binned_headers, headers[low_bin])
    end
       
    # Update the header date stamp
    
    file_time_str = string(now())
    binned_headers[i]["DATE"] = file_time_str

    # Add a new comment about the processing
    
    push!(binned_headers[i].keys, "COMMENT")
    comment_string = "Binned from " * string(n_bins) * " images"
    push!(binned_headers[i].values, "")
    push!(binned_headers[i].comments, comment_string)
    binned_headers[i].map["COMMENT"] = length(binned_headers[i].keys)
    
    # Update exposure duration for the binned images
    
    duration = 0.0
    if  haskey(headers[low_bin], "EXPTIME")
      for j in low_bin:high_bin
        if haskey(headers[j], "EXPTIME")
          duration = duration + headers[j]["EXPTIME"]
        end    
      end
      binned_headers[i]["EXPTIME"] = duration
    elseif  haskey(headers[low_bin], "EXPOSURE")
      for j in low_bin:high_bin
        if haskey(headers[j], "EXPOSURE")
          duration = duration + headers[j]["EXPOSURE"]
        end    
      end
      binned_headers[i]["EXPOSURE"] = duration
    end 

    # Update the header entry DATE-OBS using the first image of the bin
    
    date_format = "yyyy-mm-ddTHH:MM:SS.s"
    date_obs_string = string(DateTime(now()))
    
    if haskey(headers[low_bin], "DATE-OBS")
      
      # Applies to most ground-based imaging and to TESS SPOC FFIs
      
      date_obs_string = headers[low_bin]["DATE-OBS"]
    
    elseif haskey(headers[low_bin], "TJD_ZERO") & haskey(headers[low_bin], "STARTTJD")
      
      # Applies to TESS/MAST TICA images
      
      jd_obs = headers[low_bin]["TJD_ZERO"] + headers[low_bin]["STARTTJD"]
      date_obs = julian2datetime(jd_obs)
      date_obs_string = string(date_obs)   
      
      binned_headers[i]["STARTTJD"] = headers[low_bin]["STARTTJD"]
      binned_headers[i]["ENDTJD"] = headers[high_bin]["ENDTJD"]
    end
    
    binned_headers[i]["DATE-OBS"] = date_obs_string
     
  end
  
  return binned_headers
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
    println("Create a median image from a time- or z-axis stack\n ")
    exit()
  else
    infiles = ARGS[1:nfiles]
  end

  return infiles
end  
    

# Input a directory
# Return an array of file names in that directory

function get_files_by_directory(in_dir)

  in_files = readdir(in_dir)
  n_files = length(in_files)

  if n_files < 2
    println(" ")
    println("Usage:  fits_stack_bin.jl ")
    println(" ")
    println("Creates binned images from from a time- or z-axis stack \n")
    println("Defaults to the current working directory or use binning.conf \n")
    println("Requires 2 or more files \n")
    exit()
  end

  for i in 1:n_files
    in_files[i] = in_dir * "/" * in_files[i]
  end
    
  return in_files
end  
    

# Build and return image and header stacks from an array of FITS file names
# Accepts standard and some non-standard keywords such as
#   DATE-OBS (observed CCD frames and FFIs) string in UTC format yyyy-mm-ddTHH:MM:SS.s
#   STARTTJD (TICA files) floating point relative JD in TESS time
#   EXPOSURE (observed CCD frames) seconds
#   EXPOSURE (TESS FFIs) day
#   LIVETIME (TESS FFIs) day
#   EXPTIME (TICA files) seconds

function build_stacks(in_files)
  
  d = length(in_files)
  
  f = FITS(in_files[1])
  (w, h) = size(f[1])
  first_header = read_header(f[1])
  close(f)

  # Initialize the image stack using the size of the first image
  images = zeros(d, w, h)
  
  # Initialize the header stack using the first image header
  headers = [first_header]
   
  # Sequentially add images and headers from the files to the stacks
  
  for i in 1:d   

    f = FITS(in_files[i])
    image = read(f[1])
    (width, height) = size(f[1])
    header = read_header(f[1])
    close(f)
    
    if (w != width) & (h != height)
      println("Warning: image file " * in_files[i] * " has a anomalous size")
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


# Write FITS files

function write_images_as_fits(out_dir, base_name, headers, images)

  (n_headers, ) = size(headers)
  
  (n_images, width, height) = size(images)

  if n_images != n_headers
    println("The number of headers and images do not match when writing the image stack \n")
    exit()
  end
  
  # Sequentially write the FITS files

  for i in 1:n_images

    out_file = out_dir * "/" * base_name * "_" * lpad(string(i), 3, '0') * ".fits"
    f = FITS(out_file, "w")
    write(f, images[i,:,:], header=headers[i])
    close(f)

  end

  println("\n")
  println("The stack of binned images has been saved in " * out_dir * " \n")

end



# Process the requested images
#   Read the configuration file instructions from the current working
#   Acquire a list of FITS files to bin from the input directory
#   Create binned images and headers
#   Write FITS files for the binned images in the output directory

function process_images()
  
  configuration_file = "binning.conf"
  println("Reading the binning configuration file")
  binning_conf = read_configuration(configuration_file)
  
  if haskey(binning_conf, "n_bins")
    n_bins = binning_conf["n_bins"]
  else
    n_bins = 2
  end
  
  if haskey(binning_conf, "in_dir")
    in_dir = binning_conf["in_dir"]
  else
    in_dir = "."
  end
    
  if haskey(binning_conf, "out_dir")
    out_dir = binning_conf["out_dir"]
  else
    out_dir = "."
  end

  if haskey(binning_conf, "base_name")
    base_name = binning_conf["base_name"]
  else
    base_name = "binned_"
  end
  
  println("Acquiring a sequence of image file names from " * in_dir)
  in_files = get_files_by_directory(in_dir)
  
  println("Building the input stacks")
  headers, images = @time build_stacks(in_files)

  println("Creating the images binned " * string(n_bins) * " times \n")
  binned_images = @time bin_images(images, n_bins)
  
  println("Creating the binned image headers \n")
  binned_headers = @time bin_headers(headers, n_bins)
  
  println("Writing the binned image stack as a sequence of FITS files to " * out_dir * "\n") 
  @time write_images_as_fits(out_dir, base_name, binned_headers, binned_images)
 
  return

end


# Read a directory of FITS image files and write FITS files for the binned images

bin_results = process_images()

exit()
