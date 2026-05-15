#!/home/jkielkopf/local/bin/julia

# fits_stack_wcs_photometry
#
#   Photometry through the z-axis of a stack of fits images
#
#   Explicit inputs:
#
#     Configuration file 
#
#   Explicit output:
#
#     Data files of flux versus time or slice
#
#
#   John Kielkopf (kielkopf@louisville.edu)
#   MIT License
#   Copyright 2025
#   
 
#   2025-09-05 Version 1.0 
#     Created from fits_stack_photometry version 1.0
#     Tested with SPOC FFIs Sector 91
#
#   2025-09-06 Version 1.01
#     Corrected size operation in apphot carried over from Python
#
#   2025-09-07 Version 1.1
#     Works on files sequentially instead of in blocks
#     This is no longer memory limited
#     Ready to set up for multiprocessing
#
#   2025-09-07 Version 1.2
#     Incorporates masking and median filtering of background
#     Updated apphot from tesscut code



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

#  Create and preallocate array for each target with its signals
#  Adapted from a Gemini AI suggestion
#    vectors_array = Vector{Vector{Float64}}(undef, 3)
#    for i in 1:3
#      vectors_array[i] = zeros(Float64, 50)
#    end

#  When using threads declare this environment variable
#
#    export "JULIA_NUM_THREADS=16"
#
#  for the number of threads equal to the number of CPUs (nproc) available   


using FITSIO               # For FITS management
using WCS                  # For World Coordinate System in FITS
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
  
  # Check if conf_file exists in the current directory

  if isfile(conf_file)
    println("Reading the configuration file " * conf_file)
    println("\n")
  else
    println("The required " * conf_file * " is not in this directory \n")
    exit()
  end

  dictionary = Dict()
  
  # Read the file

  dictionary["in_dir"] = "./"   
  dictionary["out_dir"] = "./"
  dictionary["in_data"] = "targets.dat"
  dictionary["out_data"] = "photometry"
  dictionary["instart"] = 1  
  dictionary["in_step"] = 1   
  dictionary["in_slices"] = 999999 
  dictionary["r_phot"] = 2
  dictionary["r_inner"] = 4
  dictionary["r_outer"] = 6
  
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

    if occursin("out_data", line)
      dictionary["out_data"] = strip(split(line,"=")[2])
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

    if occursin("r_inner", line)
      r_inner_str = strip(split(line,"=")[2])
      dictionary["r_inner"] = parse(Int64, r_inner_str)
    end

    if occursin("r_outer", line)
      r_outer_str = strip(split(line,"=")[2])
      dictionary["r_outer"] = parse(Int64, r_outer_str)
    end  

    if occursin("r_phot", line)
      r_phot_str = strip(split(line,"=")[2])
      dictionary["r_phot"] = parse(Int64, r_phot_str)
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
    

# Read a data file with WCS entries to create and return an array of pixels
# File contains space-delimited ra, dec, and optional id entries on each line 
# ra, dec, and id are treated as strings with no spaces allowed
# id is an optional string identifier for this pixel
# One pixel to a line
# The line may contain additional data which will be ignored


function read_wcs_data(data_file)
  
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
 
    items = split(line)
    if length(items) < 2
      println("Missing components of for a target ")
      exit()
    end
    if length(items) == 3
      id = items[3]
    else
      id = "0"
    end
    rahr, ramin, rasec = split(items[1],":")
    decdeg, decmin, decsec = split(items[2],":")
    ra = 15.0 * sign(parse(Float64, rahr)) * 
      (abs(parse(Float64, rahr)) +  
      parse(Float64, ramin)/60.0 + 
      parse(Float64, rasec)/3600.0 )

    dec = sign(parse(Float64, decdeg)) * 
      (abs(parse(Float64, decdeg)) +  
      parse(Float64, decmin)/60.0 + 
      parse(Float64, decsec)/3600.0 )


    # Build pixel database with ra (degrees), dec (degrees) and id string
    
    npix = npix + 1

    newpixel = [ra,dec,id]
    push!(pixels, newpixel)    
          
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
    


# Build and return image, time,  and header stacks 
# Input an array of FITS file names
# Returns arrays of header strings, images, and times

function build_stacks(fits_files)
  
  d = length(fits_files)
  
  f = FITS(fits_files[1])
  
  # TESS FFIs have 3 or more components with the WCS information  in the third one
  # If WCS is needed, detect and use this HDU
  # This is a simple test for 3 
  # It may fail for non-TESS or for early TESS FFIs with different structure
  
  if length(f) == 3
    hdu = 3
  else
    hdu = 1
  end
      
  (w, h) = size(f[2])
  first_header = read_header(f[hdu], String)
  close(f)
  

  # Initialize the image stack using the size of the first image
  images = zeros(d, w, h)
  times = []
  
  # Initialize the header stack using the first image header
  headers = [first_header]
   
  # Sequentially add images and headers from the files to the stacks
  
  for i in 1:d   

    f = FITS(fits_files[i])
    image = read(f[2])
    (width, height) = size(f[2])
    header_str = read_header(f[hdu], String)
    header_info = read_header(f[hdu])
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
      headers = push!(headers, header_str)
    end
    
    if haskey(header_info, "BJD_TDB")
      push!(times, header_info["BJD_TDB"])
    elseif haskey(header_info, "STARTTJD") 
      push!(times, header_info["STARTTJD"])
    elseif haskey(header_info, "TSTART") 
      push!(times, header_info["TSTART"])      
    else
      push!(times, i)  
    end
    
  
  end  
   
  # Return the new stacks
  
  return headers, images, times

end  


# Build and return time,  and header stacks 
# Input an array of FITS file names
# Returns arrays of header strings, images, and times

function build_info_stacks(fits_files)
  
  d = length(fits_files)
  
  f = FITS(fits_files[1])
  
  # TESS FFIs have 3 or more components with the WCS information  in the third one
  # If WCS is needed, detect and use this HDU
  # This is a simple test for 3 
  # It may fail for non-TESS or for early TESS FFIs with different structure
  
  if length(f) == 3
    hdu = 3
  else
    hdu = 1
  end
      
  (w, h) = size(f[2])
  first_header = read_header(f[hdu], String)
  close(f)
  

  # Initialize the times stack
  times = []
  
  # Initialize the header stack using the first image header
  headers = [first_header]
   
  # Sequentially add time and headers from the files to the stacks
  
  for i in 1:d   

    f = FITS(fits_files[i])
    header_str = read_header(f[hdu], String)
    header_info = read_header(f[hdu])
    close(f)
        
    if i != 1
      headers = push!(headers, header_str)
    end
    
    if haskey(header_info, "BJD_TDB")
      push!(times, header_info["BJD_TDB"])
    elseif haskey(header_info, "STARTTJD") 
      push!(times, header_info["STARTTJD"])
    elseif haskey(header_info, "TSTART") 
      push!(times, header_info["TSTART"])      
    else
      push!(times, i)  
    end
    
  
  end  
   
  # Return the new stacks
  
  return headers, times

end  


# Build and return an image from a FITS file

function build_image(fits_file)
    
  f = FITS(fits_file)
  
  # TESS FFIs have 3 or more components
  # WCS information is in the third calibrated hdu
  # If WCS is needed, detect and use it
  # This is a simple test for 3 
  # It may fail for non-TESS or for early TESS FFIs with different structure
  
  if length(f) == 3
    hdu = 3
  else
    hdu = 1
  end
      
  # Identify the array size need for this image
  (w, h) = size(f[2])
  
  # Initialize the image  using the size from the header
  image = zeros(w, h)

  # Read the image for TESS from HDU = 2
  image = read(f[2])
  
  # Close the file
  close(f)
   
  # Return the image  
  return image 

end  


# Aperture photometry on an image
# Input image coordinates, radii defining aperture and annulus
# Center of pixel n is at x=n-0.5
# Image array is indexed by integers starting with 1
# Photometry aperture radius r1 minimum value is 0.5 
# Photometry annulus radii r2:r3 is null if r2>=r3 or r2<=r1
# Creates masks for aperture and annulus and applies them to the image
# Finds the signal inside an aperture centered at (x,y)  
# Subtracts a background from the annulus median 
# Assumes an image data array [ix,iy] with integer indices indexed from 1
# Returns the total signal in the inner aperture less the background 
# Implemented with masking and median from annulus

function apphot(scidata, x, y, r1, r2, r3)
    
  (nrows, ncols) = size(scidata)
  r1sq = r1*r1
  r2sq = r2*r2
  r3sq = r3*r3
  
  # Create the aperture mask and find total signal
  
  aperture_mask = [(i - x)^2 + (j - y)^2 < r1sq for i in 1:nrows, j in 1:ncols]
  sum_ap = sum(scidata[aperture_mask])
  # mean_ap = mean(scidata[aperture_mask])
  # std_ap = std(scidata[aperture_mask])
  count_ap = count(aperture_mask)

  # Create the annulus mask and find background from annulus median signal
  
  annulus_mask =  [(i - x)^2 + (j - y)^2 > r2sq &&
  (i - x)^2 + (j - y)^2 > r3sq for i in 1:nrows, j in 1:ncols] 
  median_an = median(scidata[annulus_mask])
  bkg_ap = median_an*count_ap  
       
  # Remove background using the median of the signal in the annulus
  
  signal_ap = sum_ap - bkg_ap

  return signal_ap
end



# Aperture photometry on an image
# AIJ or ds9 floating point pixel coordinates (px,py) indexed from 1.0
# Photometry aperture r1
# Photometry inner radius r2
# Photometry outer radius r3
# Finds the signal inside the inner radius centered at  (px,py)
# Subtracts a background from the outer annulus with outlier removal
# The image a data array (x, y)
# Function is derived from AIJ and the Python version fits_wcs_photometry.py 
# Returns the signal in the inner aperture less the background 
# Implemented by indexing and mean from annulus

function apphot_mean(scidata, px, py, r1, r2, r3)

  # Calculate squares once
  
  r12 = r1*r1
  r22 = r2*r2
  r32 = r3*r3
  
  # What are the image limits inside the outer annulus
  
  (nx, ny) = size(scidata)
  
  pxmin = max(1,  floor(px - r3))
  pxmax = min(nx, floor(px + r3))
  pymin = max(1,  floor(py - r3))
  pymax = min(ny, floor(py + r3))
    
    # Initialize sums in the aperture and in the annulus
    
  sum_ap = 0.0
  sum_an = 0.0
  sum_an2 = 0.0
  average_an = 0.0
  
  # Initialize pixel counts in aperture and in annulus
  
  count_ap = 0
  count_an = 0

  # Find totals inside aperture and annulus
  
  for j in pxmin:pxmax
    for k in pymin:pymax
      dpx = (j - px)
      dpy = (k - py)
      dp2 = dpx*dpx + dpy*dpy
      pixval = scidata[j, k]
      if dp2 < r12
        sum_ap = sum_ap + pixval
        count_ap = count_ap + 1
      elseif dp2 >= r22 && dp2 <= r32
        sum_an = sum_an + pixval
        sum_an2 = sum_an2 + pixval*pixval
        count_an = count_an + 1
      end  
    end
  end
    
  # When there are no pixels this prevents a divide by zero error
  
  count_ap = max(1, count_ap)
  count_an = max(1, count_an)

  # Determine average values in the annulus
  
  average_an = sum_an/count_an
  average_an2 = sum_an2/count_an
  
  # Estimate the standard deviation for the annulus
    
  sigma_an = sqrt(abs(average_an2 - average_an*average_an))

  # Make several more passes to exclude outliers in the annulus
  
  npasses = 10
  
  for i in 1:npasses
    sum_an = 0.0
    sum_an2 = 0.0
    count_an = 0
    for j in pxmin:pxmax 
      for k in pymin:pymax
        dpx = (j - px)
        dpy = (k - py)
        dp2 = dpx*dpx + dpy*dpy
        pixval = scidata[j, k] 
        if dp2 >= r12 && dp2 <= r22 && abs(pixval - average_an) <= 2.0*sigma_an
          sum_an = sum_an + pixval
          sum_an2 = sum_an2 + pixval*pixval
          count_an = count_an + 1  
        end
      end
    end   
    count_an = max(1, count_an)
    average_an = sum_an/count_an
    average_an2 = sum_an2/count_an
    sigma_an = sqrt(abs(average_an2 - average_an*average_an))
  end

  # Calculate target signal - background and return
  
  signal  = sum_ap - count_ap*average_an
  return signal
end


# Write a 2-column data file of  x and y vectors
# Requires using DelimitedFiles at top level

function write_xy_data(out_file, x_array, y_array) 

  open(out_file, "w") do io
    writedlm(io, [x_array y_array])
  end

end

# Process the requested images
# Read the configuration file instructions from the current working
# Acquire a list of FITS files to sample from the input directory
# Acquire a list of pixels to sample from in_data coordinates
# Do photometry through the stack for each pixel
# Plot this data
# Save the data as out_data and the plot in out_dir

function process_images()
  
  # Obtain the required configuration parameters

  configuration_file = "zphot.conf"
  zdata_conf = read_configuration(configuration_file)
  in_dir = zdata_conf["in_dir"]
  out_dir = zdata_conf["out_dir"]
  out_data = zdata_conf["out_data"]
  in_data = zdata_conf["in_data"]
  in_start = zdata_conf["in_start"]
  in_step =  zdata_conf["in_step"]
  in_slices =  zdata_conf["in_slices"]
  r_inner = zdata_conf["r_inner"]
  r_outer = zdata_conf["r_outer"]
  r_phot  = zdata_conf["r_phot"]
  
  println("Acquiring a sequence of image file names from " * in_dir)
  fits_files = get_files_by_directory(in_dir,in_start,in_step,in_slices) 
    
  println("Building the ", length(fits_files), " input info stacks")
  headers, times = @time build_info_stacks(fits_files)
  
  (nfiles,)  = size(fits_files)  
 
  println("Found ", nfiles, " fits image files ")
  println("Acquiring the list of pixels to be sampled")

  # Check if indata exists in the current directory

  if isfile(in_data)
    println("Reading the target file " * in_data)
    println("\n")
  else
    println("The required target file " * in_data * " is missing \n")
    exit()
  end

  # Read the list of target celestial coordinates
  # Prepare empty signal array
  targets = read_wcs_data(in_data)  
  (ntargets,) = size(targets)
   
  # Create and preallocate the signals array
  signals = Vector{Vector{Float64}}(undef, ntargets)
  for i in 1:ntargets
    signals[i] = zeros(Float64, nfiles)
  end  

  println("Found ", ntargets, " targets")
   
  # Work on each file and its targets serially
  # This could be done with multiprocessing to speed up measurements
  println("Extracting time-series data for each target in the files")
  println(" ")
     
  for i in 1:nfiles

    # Retrieve the image data from the file
    fits_file = fits_files[i]	        
    image = build_image(fits_file)

    # For this image interate the targets and save the photometry
    for j in 1:ntargets

      (ra, dec, id) = targets[j]

      # For this image and target find x,y for ra,dec using WCS and header[i]
      # The transform is the only element of this vector

      wcs_transform = WCS.from_header(headers[i])[1] 

      # The WCS library is 0-based.  The pixel coordinates are floating point.
      # Julia arrays are 1-based.  Julia arrays are column major
      # The indexing goes across the array in the first row of pixelcoords
  
  
      # world_coords = pix_to_world(wcs_transform, [x, y])
      # println (world_coords)
  
      pixel_coords = world_to_pix(wcs_transform, [ra, dec])
        	  
      x = round(Int64, pixel_coords[1])
      y = round(Int64, pixel_coords[2])
          	    
      # Photometry about about this pixel for this frame
  
      phot = apphot(image, x, y, r_phot, r_inner, r_outer)
      signals[j][i] = phot        
    
    end
  end
    
  # Write the measurements in one file for each target
  # Files have target id in the name
  # File content is time,signal pairs
  
  for j in 1:ntargets
    
    # Retrieve the target id and build the file name
    (ra, dec, id) = targets[j]
    out_file = out_dir * "/" * out_data * "_" * id * ".dat"
   
    # Save the measurements of this target
    write_xy_data(out_file, times, signals[j])
  	
  end
 
end

# Run photometry on the stack using the configuration input

process_images()
exit()

