#!/usr/local/bin/julia

# fits_fft
#
#   Create a frequency FFT stack from s uniformly temporally cadenced image stack
#
#   Explicit inputs:
#
#     Directory of FITS files to be processed
#
#   Explicit outputs:
#
#     Frequency stack of FITS files
#
#
#   John Kielkopf (kielkopf@louisville.edu)
#   MIT License
#   Copyright 2021
#   
#   2021-07-21 Version 1.0

#   When using threads declare this environment variable
#
#     export "JULIA_NUM_THREADS=4"
#
#   for the number of threads equal to the number of CPUs available   


using FITSIO               # For FITS management
using Dates                # Date and time
using Base.Threads         # For multiprocessing
using FFTW                 # For the FFTW library

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
    
    # Skip empty lines
    
    if length(line) == 0
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
        

  end
  
  return dictionary

end

    
# Input a directory
# Return an array of file names in that directory

function get_files_by_directory(in_dir)

  in_files = readdir(in_dir)
  n_files = length(in_files)

  if n_files < 16
    println(" ")
    println("Usage:  fits_fft.jl ")
    println(" ")
    println("Creates fft frequency images from from a time- or z-axis stack \n")
    println("Defaults to the current working directory or use fft.conf \n")
    println("Requires 16 or more files \n")
    exit()
  end

  for i in 1:n_files
    in_files[i] = in_dir * "/" * in_files[i]
  end
    
  return in_files
end  
    


# Build and return an image and header stacks from an array of FITS file names

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


# Input a stack of image data with images as the first index
# Return a stack of FTs on the first dimension

function stack_fft(images)

  # Perform the FFT on real data
  # Return the magnitude of the complex Fourier transform
  
  fts = abs.(rfft(images, 1))

  return fts
end





# Write FITS FFT files

function write_images_as_fits(out_dir, base_name, ft_header, ft_images)

  
  (n_fts, width, height) = size(ft_images)
  frequency = ft_header["FSLICE"]
  
  # Sequentially write the FITS files with the slice frequency for that file

  for i in 1:n_fts

    ft_slice_header = ft_header
    ft_slice_header["FSLICE"] = frequency * (i - 1)/n_fts
    out_file = out_dir * "/" * base_name * "_" * lpad(string(i), 3, '0') * ".fits"
    f = FITS(out_file, "w")
    write(f, ft_images[i,:,:], header=ft_slice_header)
    close(f)

  end

  println("\n")
  println("The stack of Fourier transform slices has been saved in directory " * out_dir * " \n")

end


# Input a stack of headers from the original images and number of Fourier slices
# Return a Fourier transform header based on the content of the image headers
# Accepts standard and some non-standard keywords such as such as 2021-06-22T10:00:36.768
#   DATE-OBS (observed CCD frames and FFIs) string in UTC format yyyy-mm-ddTHH:MM:SS.s
#   STARTTJD (TICA files) floating point relative JD in TESS time
#   EXPOSURE (observed CCD frames) seconds
#   EXPOSURE (TESS FFIs) day
#   LIVETIME (TESS FFIs) day
#   EXPTIME (TICA files) seconds
# Adds a non-standard keywork FSLICE for the frequency spanned by the FT stack
# Frequency has units of per day if timing information is in the image files
# Frequency is 1.0 if there are no identifed timing elements

function fft_header(headers)

  # How many images were taken
  
  n_images = length(headers)
    
  file_time_string = string(now())
  
  # Extract times from the image stack headers
  # Calculate the frequency increment between slices of the Fourier stack
  
  # DATE-OBS format expected to be 2021-06-22T10:00:36.768 yyyy-mm-ddTHH:MM:SS.s
  # JD format expected to be floating point in TICA images
    
  date_format = "yyyy-mm-ddTHH:MM:SS.s"
  if haskey(headers[1], "DATE-OBS") & haskey(headers[n_images], "DATE-OBS")
    first_date_string = headers[1]["DATE-OBS"]
    first_datetime = DateTime(first_date_string, date_format)
    first_jd = datetime2julian(first_datetime)
    last_date_string = headers[n_images]["DATE-OBS"]
    last_datetime = DateTime(last_date_string, date_format)
    last_jd = datetime2julian(last_datetime)
    delta_jd = last_jd - first_jd
    frequency = 0.5*(n_images / delta_jd)
  elseif (haskey(headers[1], "STARTTJD") & haskey(headers[n_images], "STARTTJD"))
    first_jd = float(headers[1]["STARTTJD"])
    last_jd = float(headers[n_images]["STARTTJD"])      
    delta_jd = last_jd - first_jd
    frequency = 0.5*(n_images / delta_jd)
    jd_zero = float(headers[1]["TJD_ZERO"])
    first_date_string = string(julian2datetime(jd_zero + first_jd))
  else    
    first_date_string = file_time_str
    frequency = 0.5*float(n_images) 
  end
  ft_header = deepcopy(headers[1]) 
  ft_header["DATE-OBS"] = first_date_string
  ft_header["DATE"] = file_time_string
  ft_header["FSLICE"] = frequency
  set_comment!(ft_header, "FSLICE", "slice frequency [per d]")
  return ft_header
end


# Create an array of frequency sliced headers for FFTs of FITS images
# Input prototype header with FSLICE entry and the number of transform slices

function stack_fft_headers(ft_header, n_fts)
  global f = ft_header["FSLICE"] 
  global ft_headers = [ft_header,]
  global ft_headers = repeat(ft_headers, n_fts)
  global k = 0
  for i in 1:n_fts
    k = k + 1
    global fs = f * (k - 1) / n_fts
    global ft_headers[k]["FSLICE"] = fs
    println(k, " => ", ft_headers[k]["FSLICE"])
  end
  return ft_headers
end    


# Process the images to find and export the FFT stack and a header

function process_images()

  configuration_file = "fft.conf"
  println("Reading the FFT configuration file " * configuration_file * " \n")
  fft_conf = read_configuration(configuration_file)
  
  if haskey(fft_conf, "in_dir")
    in_dir = fft_conf["in_dir"]
  else
    in_dir = "."
  end
    
  if haskey(fft_conf, "out_dir")
    out_dir = fft_conf["out_dir"]
  else
    out_dir = "."
  end

  if haskey(fft_conf, "base_name")
    base_name = fft_conf["base_name"]
  else
    base_name = "ft_"
  end

  println("Acquiring sequential image file names")
  in_files = get_files_by_directory(in_dir)

  println("Building the input stacks")
  headers, images = @time build_stacks(in_files)

  println("Computing the FFT \n")
  ft_images = @time stack_fft(images)
 
  (n_fts, width, height) = size(ft_images)
   
  println("Creating the Fourier slice header \n")
  ft_header = fft_header(headers)
  
  println("Writing the temporal Fourier transform slices \n") 
  write_images_as_fits(out_dir, base_name, ft_header, ft_images)
  
  return

end


# Process the images and write their temporal Fourier transform

ft_results = process_images()



exit()
