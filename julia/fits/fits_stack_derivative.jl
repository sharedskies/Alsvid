#!/usr/local/bin/julia

# fits_stack_derivative
#
#   Differentiate an image stack 
#
#   Explicit input:
#
#     Directory of FITS files to be processed
#
#   Explicit output:
#
#     Derivate image for each image in the original stack
#
#
#   John Kielkopf (kielkopf@louisville.edu)
#   MIT License
#   Copyright 2023
#   
#   2022-12-30 Version 1.1
#     Working version using command line entry of directory
#
#   2023-02-04 Version 1.2
#     From fits_stack_running_median_differences.jl
#
#   2023-02-23 Version 1.3
#     Added dslice option 

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
#   in_start  => serial index from 1 of first file to be used
#   in_step   => step in number of files from the first one
#   in_slices => total number of files to be processed
#   d_slice   => lookback this many slices for the difference


function read_configuration(conf_file)
  
  dictionary = Dict()
  
  # Read the file

  dictionary["in_dir"] = "./"   
  dictionary["out_dir"] = "./"
  dictionary["base_name"] = "derivative"
  dictionary["in_start"] = 1  
  dictionary["in_step"] = 1   
  dictionary["in_slices"] = 999999
  dictionary["d_slice"] = 1  
  
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

    if occursin("d_slice", line)
      d_slice_str = strip(split(line,"=")[2])
      dictionary["d_slice"] = parse(Int64, d_slice_str)
    end
        
  end
   
  return dictionary

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
    

# Process the images to find the running derivative 

function process_images()

  println("\n")
  println("To enable threading, use nproc and export \"JULIA_NUM_THREADS=nthreads\" \n") 

  println("Reading the configuration file derivative.conf \n")

  # Obtain the required configuration parameters

  configuration_file = "derivative.conf"
  derivative_conf = read_configuration(configuration_file)
  in_dir = derivative_conf["in_dir"]
  out_dir = derivative_conf["out_dir"]
  base_name = derivative_conf["base_name"]
  in_start = derivative_conf["in_start"]
  in_step =  derivative_conf["in_step"]
  in_slices =  derivative_conf["in_slices"]
  d_slice = derivative_conf["d_slice"]


  println("Acquiring a sequence of image file names from " * in_dir * "\n")
  
  select_files = get_files_by_directory(in_dir,in_start,in_step,in_slices) 

  println("Differentiating the stack \n")


  nimages = length(select_files)

  # Sampled stack is on in_step increments
  # Deriviatives are differences between the current image and the prior image
  # Differentiate each image and save the difference
  i_start = 1 + d_slice
  i_stop = nimages
    
  @threads for i in i_start:nimages
    this_f = FITS(select_files[i])
    prior_f = FITS(select_files[i-d_slice])
    this_image = read(this_f[1])
    prior_image = read(prior_f[1])
    difference_header = read_header(this_f[1])
    close(prior_f)
    close(this_f)    

    difference_image = this_image .- prior_image
    
    # Update the header date stamp
   
    file_time_str = string(DateTime(now()))
    difference_header["DATE"] = file_time_str

    push!(difference_header.keys, "COMMENT")
    comment_string = "derivative"
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
println("Derivatives of ", nimages, " images have been saved", " \n")

exit()

