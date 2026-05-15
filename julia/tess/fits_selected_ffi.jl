#!/usr/local/bin/julia

# fits_selected_ffi
# 
# Read a SPOC shell script to extract select camera and ccd from a sector
#
# Explicit inputs:
#
#   Shell script
#   Camera and ccd "4-4"
#
# Explicit output:
#
#   Edited shell script "select.sh"
#
#   John Kielkopf (kielkopf@louisville.edu)
#   MIT License
#   Copyright 2025
#   
 
#   2025-05-12 Version 1.0 
#     Command line arguments  

# Accept command line argument
# Warn if missing and exit
# Return input filename 

script_file = "spoc.sh"
select_text = "4-4"
out_file = "select.sh"

function get_commandline_arguments()
  global script_file = "spoc.sh"
  global out_file = "select.sh"
  global select_text = "4-4"
  if length(ARGS) == 3
    global script_file = ARGS[1]
    global out_file = ARGS[2]
    global select_text = ARGS[3]
  elseif length(ARGS) == 2
    global script_file = ARGS[1]
    global out_file = ARGS[2]
    println("Using default 4-4")   
  elseif length(ARGS) == 1
    global select_text = ARGS[1]
    println("Selecting ", select_text)
    println("Using defaults select.sh  4-4")
  else
    println("Using defaults")   
    println("Use script_file out_file select_text  on the command line\n")
  end
  println(script_file, "  ", out_file, "  ", select_text)
end 


# Read the SPOC script

function read_script(script_file, select_text)

  select_lines = []

  # Read the file

  script_text = readlines(script_file) 

  # Parse the text lines

  for line in script_text
    if occursin(select_text, line)
      push!(select_lines, line)
    end

  end
  
  return select_lines
end  
  
# Write a select script line by line

function write_new_script(out_file, select_lines) 
  nlines, = size(select_lines)
  println(nlines," image files are in ", out_file)
  open(out_file, "w") do io
    for i in range(1,nlines)
      #println(select_lines[i])
      write(io,select_lines[i]*"\n")
    end  
  end
end

# Run the process

get_commandline_arguments()
select_lines = read_script(script_file, select_text)  
write_new_script(out_file, select_lines)

exit()




