#!/usr/local/bin/julia

# fits_bayer_to_rgb_fits
#
#   Create a  stack of FITS r, g, and b images  from a Bayer-masked FITS image
#
#   Explicit inputs:
#
#     Directory of FITS files to be processed
#
#   Explicit outputs:
#
#     FITS image files in r, g, and b from the relevant pixels
#
#
#   John Kielkopf (kielkopf@louisville.edu)
#   MIT License
#   Copyright 2021
#   
#   2021-08-05 Version 1.0

#   When using threads declare this environment variable
#
#     export "JULIA_NUM_THREADS=4"
#
#   for the number of threads equal to the number of CPUs available   

# ###

# Julia notes
#
#   FITS image 2064 wide and 1544 high becomes an array of size (2064, 1544)
#   In Python the same image in a numpy array would be (1544, 2064)
#   In Julia the first index goes across the image (column number or x)
#   In Julia the second index goes down the image (row number or y)
#
#   The generator 1:2:n  starts at 1 and with a stepsize of 2 continues to n
#   
#   In Julia the array is (w,h) so the the enumeration  is (column#, row#)
#
#   Floating point images are normalized to 1.0
#   Stacks should be in order CHW, that is [color, height, width], not HWC
#   See juliaimages.org for packages and documentation
#   FileIO requires adding the ImageIO package to save PNG files
#   Use channelview and colorview to alter the representation of an image




# ###

using FITSIO               # For FITS management
using Dates                # Date and time
using Base.Threads         # For multiprocessing


# ###
     
# Read a configuration file to create and return a dictionary
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


# ###

# Input a directory
# Return an array of file names in that directory

function get_files_by_directory(in_dir)

  in_files = readdir(in_dir)
  n_files = length(in_files)

  if n_files < 1
    println(" ")
    println("Usage:  fits_to_rgb.jl ")
    println(" ")
    println("Creates png images from  Bayer RGB masked FITs images \n")
    println("Requires one or more FITS files \n")
    exit()
  end
  j = 1
  in_fits = [""]
  for i in 1:n_files
    if occursin(".fits", in_files[i])
      fits_file = in_files[i]
      if j == 1
        in_fits[1] = fits_file
      else
        in_fits = push![fits_file]
      end   
      j = j+1
    end
  end
  
  if j == 1
    println("Requires one or more FITS files \n")
    exit()
  end  
    
  return in_fits
end  


# ###

# Input a fits file name from a directory
# Return a fits image and header

function read_fits(in_dir, in_file)

  f = FITS(in_dir * "/" * in_file)
  image = read(f[1])
  header = read_header(f[1])
  close(f)
  return header, image

end

# Pick up RGB samples to match Allied Vision Bayer camera mask
# FITS images enumerate pixels starting at [1,1] as does Julia
# Numpy images enumerate arrays starting at [0,0]

# The pattern in all Allied Vision Manta cameras is 
#
#
#           Column 1    Column 2    Column 3
#
#   Row 1      R           G           R
#   Row 2      G           B           G
#   Row 3      R           G           R
#
# When x is the column number (first index) and y is the row number (second index)
#  in a 1-based enumeration (e.g. Julia)
#
#    FITS B  [x, y] is [even, even]
#    FITS R  [x, y] is [odd,   odd]
#    FITS G  [x, y] is both [even, odd] and [odd, even]
#
#  and in a 0-based enumeration even/odd are swapped.
#
# Most Sony CMOS sensors are rectangular and wider than high (w>h)
# In Numpy arrays the row number is the first index
#   and the column number is the second, i.e. [y,x]

# This algorithm assigns the color to its pixel and does not interpolate
# The resulting images are true to color with 1-pixel spatial dithering

# ###

# Input an Bayer-masked FITS image [x, y] array 
# Output the red image as a [y, x]

function red_from_bayer(image)

#  red:  odd rows    odd columns
#  image array: (rows, columns)
#  color array: (rows, columns)

  (width, height) = size(image)
  red_height = Int64(floor(height/2.0))
  red_width = Int64(floor(width/2.0))  
  red_image = zeros(red_width, red_height)
  @threads for y in 1:2:height
    red_y = Int64(ceil(y/2.0))
    for x in 1:2:width       
      red_x = Int64(ceil(x/2.0)) 
      red_image[red_x, red_y] = image[x, y]
    end
  end
  
  return red_image
end


# ###

# Input an Bayer-masked FITS image [x, y] array 
# Output the blue image as a [y, x]

function blue_from_bayer(image)

#  blue:  even rows     even columns
#  image array: (rows, columns)
#  color array: (rows, columns)

  (width, height) = size(image)
  blue_height = Int64(floor(height/2.0))
  blue_width = Int64(floor(width/2.0))  
  blue_image = zeros(blue_width, blue_height)
  @threads for y in 2:2:height
    blue_y = Int64(floor(y/2.0))
    for x in 2:2:width
      blue_x = Int64(floor(x/2.0))
      blue_image[blue_x, blue_y] = image[x, y]
    end
  end
  
  return blue_image
end
    

# ###

# Input an Bayer-masked FITS image [x, y] array 
# Output the mean green image as a [y, x] array

function green_from_bayer(image)

#  green_1:  odd rows   even columns
#  green_2:  even rows  odd columns
#  array: (rows, columns)

  (width, height) = size(image)
  green_height = Int64(floor(height/2.0))
  green_width = Int64(floor(width/2.0))  
  green_image_1 = zeros(green_width, green_height)
  green_image_2 = zeros(green_width, green_height)

  @threads for y in 1:2:height
    green_y = Int64(ceil(y/2.0))
    for x in 2:2:width
      green_x = Int64(floor(x/2.0))
      green_image_1[green_x, green_y] = image[x, y]
    end
  end

  @threads for y in 2:2:height
    green_y = Int64(floor(y/2.0))
    for x in 1:2:width
      green_x = Int64(ceil(x/2.0))
      green_image_2[green_x, green_y] = image[x, y]
    end
  end
    
  green_image = 0.5 .* (green_image_1 .+ green_image_2)

  return green_image
end


# ###

# Input a Bayer-maked image as a data array [x, y] array 
# Return a gray image as a [y, x] array for RGB processing into a CHW array

function gray_from_bayer(image)
   
  red_image = red_from_bayer(image)
  green_image = green_from_bayer(image)
  blue_image = blue_from_bayer(image)
  gray_image = red_image .+ green_image .+ blue_image
   
  return gray_image
end   

# ###

# Write FITS RGB files

function write_rgb_images_as_fits(out_dir, base_name, images)
  
  colors = ['r', 'g', 'b']
  for i in 1:3
    #(width, height) = size(images[i])
    out_file = out_dir * "/" * base_name * "_" * colors[i] * ".fits"
    f = FITS(out_file, "w")
    write(f, images[i])
    close(f)

  end

  println("\n")
  println("The stack of color images has been saved in directory " * out_dir * " \n")

end

# ###

# Process the images 

function process_images()

  configuration_file = "rgb.conf"
  println("Reading the RGB converison configuration file " * configuration_file * " \n")
  rgb_conf = read_configuration(configuration_file)
  
  if haskey(rgb_conf, "in_dir")
    in_dir = rgb_conf["in_dir"]
  else
    in_dir = "."
  end
    
  if haskey(rgb_conf, "out_dir")
    out_dir = rgb_conf["out_dir"]
  else
    out_dir = "."
  end

  println("Acquiring sequential FITS image file names from ", in_dir)
  fits_files = get_files_by_directory(in_dir)
  
  println("Writing the RGB images \n") 
  for in_file in fits_files
    
    # Get the image array from the file
    (header, image) = read_fits(in_dir, in_file)
    
    # Extract the three colors from the image array

    red_image = 1.0*red_from_bayer(image)
    green_image = 1.0*green_from_bayer(image)
    blue_image = 1.0*blue_from_bayer(image)
    base_name = split(in_file, ".")[1]   
    write_rgb_images_as_fits(out_dir, base_name, [red_image, green_image, blue_image])

  end
  
  return

end


# Process the FITS images and write their RGB equivalents

rgb_results = process_images()



exit()
