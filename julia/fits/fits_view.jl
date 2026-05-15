#!/usr/local/bin/julia

# fits_view
#
#   Visualize a FITS image file 
#
#   Explicit input:
#
#     FITS image file
#
#   Explicit output:
#
#     None
#
#
#   John Kielkopf (kielkopf@louisville.edu)
#   MIT License
#   Copyright 2026
#   
#   2026-02-05 Version 1.0
#   2026-02-07 Version 1.1
#     Startup options added to console
#   2026-02-21 Version 1.2
#     Restructured to use functions to map array <--> canvas
#     Added window resizng, zoom and pan
#     Added keyboard input after window is open


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



using FITSIO               # For FITS management
using Dates                # Date and time
using Statistics           # For mean, median, sigma
using Gtk4                 # For GUI 
using Cairo                # For fast 2D graphics without GPU 


# Build and return an image stack from an array of FITS file names
# Uses calibrated image if extended FITS TESS FFIs from SPOC on MAST

function build_image(infile)
  global hdu

  # Test for an FFI with extensions for the first image
  # Set hdu for TESS SPOC FFIs
  
  f = FITS(infile)
  if length(f) == 1  
    global hdu = 1
  elseif length(f) == 3
    global hdu = 2
  else
    println("Unknown type of FITS file reports ", length(f), " HDUs")
    exit()
  end      
  (w, h) = size(f[hdu])
  image = read(f[hdu])
  header = read_header(f[hdu])
  close(f)

  return image, header

end  


# Get the filename from the command line
# Return the name# Accept data file as command line argument
# Warn if missing and exit
# Return input filename 

function get_commandline_arguments()

  if length(ARGS) == 1
    infile = ARGS[1]     
  else
    println()
    println("Use file name on the command line\n")
    exit() 
  end
  
# Use strings for the filename and the fiber number
# If a number is required, use parse(fiberstr)
    
  return infile
end  


# Wait for a byte to continue

function wait_for_key()
  println()
  print("Request \n  header \n  file \n  view \n  exit  \n")
  println()
  print("  with [h, f, v, x and/or return] > : ")
  response = readline()
  cmd = "v"
  if length(response) >= 1
    cmd = string(response[1])
  end
  return cmd
end


# Convert canvas coordinates to array coordinates

#   xa, ya array coordinates
#   xc, yc canvas coordinates
#   wa, ha array dimensions
#   wc, hc canvas dimensions
#   pan is a tuple for array selection center
#   zoom is a multiplier for the display scale
#   return integer xa and ya within the array 
#   return 0 for out of bounds (window larger than the array) 

function c2a(xc, yc, wc, hc, wa, ha, pan, zoom)
  
  x = (xc - wc*0.5)/zoom + pan[1]
  y = (yc - hc*0.5)/zoom + pan[2]

  if x >= 1 && y >= 1 && x <= wa && y <= ha  
    xa = max(1, round(Int64, x))
    xa = min(wa, round(Int64, xa))
    ya = max(1, round(Int64, y))
    ya = min(ha, round(Int64, ya))
  else
    xa = 0
    ya = 0
  end  
  return xa, ya

end  


# Convert array coordinates to canvas coordinates

#   xa, ya array coordinates
#   xc, yc canvas coordinates
#   wa, ha array dimensions
#   wc, hc canvas dimensions
#   pan is a tuple for array selection center
#   zoom is a multiplier for the display scale


function a2c(xa, ya, wc, hc, wa, ha, pan, zoom)
  x = (xa - pan[1])*zoom + wc*0.5 
  y = (ya - pan[2])*zoom + hc*0.5
  
  xc = max(1, round(Int64, x))
  xc = min(wc, round(Int64, xc))
  yc = max(1, round(Int64, y))
  yc = min(hc, round(Int64, yc))
  return xc, yc

end  


infile = get_commandline_arguments()
println()
img_array, img_header = build_image(infile)
println("Loading: ", infile)


println("Image size: ", size(img_array))
println("Image mean: ", mean(img_array))
println("Image sigma: ", std(img_array))
println("Image median: ", median(img_array))
img_max = maximum(img_array)
img_min = minimum(img_array)
img_rng = img_max - img_min
println("Image min: ", img_min)
println("Image max: ", img_max)
println("Image range: ", img_rng)



while true
  println()
  cmd = wait_for_key()
  if cmd == "h"
    println()
    print(img_header)
    println()
  elseif cmd == "f"
    println()
    println("File: ", infile)
    println()  
  elseif cmd == "v"
    break
  elseif cmd == "x"
    exit()
  end
end    


# Setup the user interface

# Limit initial canvas size to less than display dimensions

w_display = 1024
h_display = 1024
w_array, h_array = size(img_array)
w_canvas = minimum((w_display, w_array))
h_canvas = minimum((h_display, h_array))
zoom = 1.0
pan = (0.5*w_array, 0.5*h_array)

# Global mutable variables to pass to the connect callbacks

is_dragging = false
is_selected = false
canvas_drag_start = (1,1)
canvas_drag_select = (1, 1, 1, 1)


# Create the initial canvas
# It may be resized by the user

img_canvas = GtkCanvas()
win = GtkWindow(img_canvas, "FITS Viewer", w_canvas, h_canvas)


# Render the data onto the canvas
# See https://juliagtk.github.io/Gtk4.jl/dev/manual/canvas/
# Call draw(img_canvas) to refresh the image data on the canvas
# User resizing also calls draw()

@guarded draw(img_canvas) do canvas
  ctx = getgc(img_canvas)
  
  # Update a resized canvas 
  
  global w_canvas = width(img_canvas)
  global h_canvas = height(img_canvas)
  
  # Globals known to the draw function
  # img_array, w_array, h_array, pan, zoom
  # canvas_drag_select

  # Use selection box to define the region and zoom
  # Dynamic canvas selection: canvas_drag_select from callback

  # Map every pixel in the canvas to its array equivalent
  
  for xc in 1:w_canvas, yc in 1:h_canvas
    
    xa, ya = c2a(xc, yc, w_canvas, h_canvas, w_array, h_array, pan, zoom)
    if xa >=1 && ya >= 1 && xa <= w_array  && ya <= h_array
      val = (img_array[xa, ya] .- img_min) ./ img_rng
    else
      val = 0.0
    end
    set_source_rgb(ctx, val, val, val)
    rectangle(ctx, xc-1, yc-1, 1, 1)
    fill(ctx)
  end

  # Highlight the selection box while dragging

  if is_dragging
    
    # Highlight canvas selection 
        
    x1, x2, y1, y2 = canvas_drag_select
    
    bx = min(x1, x2)
    by = min(y1, y2)
    bw = abs(x2 - x1)
    bh = abs(y2 - y1)
    
    set_source_rgba(ctx, 0.4, 0.6, 1.0, 0.3)
    rectangle(ctx, bx, by, bw, bh)
    fill_preserve(ctx)
    
    set_source_rgba(ctx, 0.4, 0.6, 1.0, 1.0)
    set_line_width(ctx, 1.0)
    stroke(ctx)
  end

end


# Mouse tracking 
# Create a Motion Controller to listen for mouse moves

motion = GtkEventControllerMotion()

# Connect the "motion" signal

signal_connect(motion, "motion") do controller, x, y

  xc = max(1, round(Int64, x))
  yc = max(1, round(Int64, y))
  
  wc = width(img_canvas)
  hc = height(img_canvas)

  # Convert from canvas to data array coordinates
  # Values of xc and yc should be within the window bounds
  
  xa, ya = c2a(xc, yc, wc, hc, w_array, h_array, pan, zoom)  
  if xa > 0 && ya > 0 
    val = img_array[xa,ya]
    # Use dot notation to update the property
    win.title = "x: $xa | y: $ya | value: $(round(val,sigdigits=3))"
  end 

end


# Attach the controller to the canvas

push!(img_canvas, motion)


# Area selection

drag = GtkGestureDrag()
set_gtk_property!(drag, :button, 1)


# Start the area selection with a left mouse down
# In the do block "widget" is an arbitrary identifier

signal_connect(drag, "drag-begin") do widget, x, y
  global is_dragging = true
  global canvas_drag_start = (x, y)
  global canvas_drag_select = (x, x, y, y)

  draw(img_canvas) 
end

# Hold and drag while displaying the area selected

signal_connect(drag, "drag-update") do widget, offset_x, offset_y
  start_x, start_y = canvas_drag_start
  end_x = start_x + offset_x
  end_y = start_y + offset_y
  
  left = min(start_x, end_x)
  right = max(start_x, end_x)
  top = min(start_y, end_y)
  bottom = max(start_y, end_y)
  global canvas_drag_select = (left, right, top, bottom)
  
  draw(img_canvas) 
end

# Release to act act and  set pan and zoom

signal_connect(drag, "drag-end") do widget, offset_x, offset_y
  global is_dragging = false
  global is_selected = true
  start_x, start_y = canvas_drag_start
  end_x = start_x + offset_x
  end_y = start_y + offset_y
  
  left = min(start_x, end_x)
  right = max(start_x, end_x)
  top = min(start_y, end_y)
  bottom = max(start_y, end_y)
  width = max(1, abs(right - left))
  height = max(1, abs(top - bottom))
  new_zoom = min( w_array/width, h_array/height)
  
  # Use current pan and zoom in c2a(xc, yc, wc, hc, wa, ha, pan, zoom) 
  # Convert canvas to array coordinates to find the new pan
  
  new_pan = c2a( 0.5*(left + right), 0.5*(top + bottom), 
    w_canvas, h_canvas, w_array, h_array, pan, zoom )

  # Export the new pan and zoom for the next canvas draw operation
     
  global zoom = new_zoom
  global pan = new_pan
  draw(img_canvas) 
end

push!(img_canvas, drag)


# Use keys for other functions in this window

key_in = GtkEventControllerKey(win)

signal_connect(key_in, "key-pressed") do controller, keyval, keycode, state

  if Char(keyval) == 'q'
    println("Closing window and quitting")
    destroy(win)
    exit()
    return true # Handle
  end 
  
  if Char(keyval) == 'x'
    println("Closing window and exiting")
    destroy(win)
    exit()
    return true # Handle
  end   
 
  if Char(keyval) == 'v'
    global zoom = 1.0
    global pan = (w_array*0.5, h_array*0.5)
    draw(img_canvas)
    return true # Handle
  end

  if Char(keyval) == 'h'
    println()
    println(img_header)
    println()
    return true # Handle
  end
 
  if Char(keyval) == 'f'
    println()
    println(infile)
    println()
    return true # Handle
  end
 

  # keyval is a UInt32; convert to Char to see the character
  println("Key pressed: ", Char(keyval), "  |  Key value: $keyval)")
  
  # Return true to stop propagation (event handled), 
  # or false to let other handlers see it.
  return true 
end


# Maintain the display using glib polling

if !isinteractive()
  c = Condition()
  signal_connect(win, :close_request) do widget
  notify(c)
  end
  @async Gtk4.GLib.glib_main()
  wait(c)
end


# Notify the user

println("Process finished")

exit()

