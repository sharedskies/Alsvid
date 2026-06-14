#!/home/john/local/bin/julia

#  transitmodel
#  
#    Lightcurve for a limb-darkened star and transiting planet
#    
#    Explicit inputs:
#    
#      Stellar parameters file with radius, temperature, and limb darkening 
#      Planet parameters file with radius and temperature
#      Orbit parameters file
#      Transit file of sampling times and comparison fluxes
#    
#    Explicit outputs:
#           
#      Transit file of sampling times and model fluxes
#      Transit plot with Makie of comparison of observed and  model fluxes
#      
#    Notes:
#
#      Based AstroImageJ version 2020-03-31 by Karen Collins
#      Based on EXOFAST exofast_occultquad_cel by Jason Eastman et al. (2018)
#      Based on paper by Mandel and Agol (2002)
#      Based on Matlab code of Avi Shporer (2018)
#      
#      John Kielkopf (kielkopf@louisville.edu)
#      MIT License
#      Copyright 2021, 2025, 2026
#      
#      2021-06-29 Version 1.0d
#        Working with eccentricity = 0.0
#      2025-10-24 Version 1.1
#        Phase returned from solution of Kepler equation is now -pi to +pi
#        Working with eccentric orbits
#      2026-06-06 Version 1.2
#        Removed dictionary entries that are not used
#        Added planet bond albedo to dictionary for future use
#        Assigned consistent default dictionary values
#        Added physical constants for future use
#        Makie replaced plotly for desktop graphics
#      2026-06-14 Version 1.3
#        Added comments explaining the terms
#        Tested for consistency against AstroImageJ and Batman
#        Orbital position calculation and sky projection restructured for clarity
#        Models a full period rather than the observed window
#        Provides true anomaly over a full period with correct consistent sign
#        Exports diagnostic data pairs for plots


 
# Julia Language Notes

# Variables should be local, or passed as arguments to
#   functions, whenever possible. 

# Any code that is performance critical should be inside 
#   a function.

# Passing arguments to functions is better style. 
#   It leads to more reusable code and clarifies what the 
#   inputs and outputs are.

# Multidimensional arrays in Julia are stored in 
#   column-major order.

# Broadcast functions denoted by the "." operator.
# Broadcast Boolean operation become bit data type.
 
# Add packages this program depends on
# In julia, use "Pkg.add("package")" to install a missing package
# This program requires DelimitedFiles, GLMakie

using DelimitedFiles  # For exporting formatted data files
using GLMakie         # For plotting results

# Define constants so that if needed they are globally optimized by the compiler

const earth_radius = 6371.0088  # mean radius in km
const earth_mass = 5.9722e24    # kg
const earth_temperature = 288.0 # bolometric mean in kelvin from space
const au = 149597870.700        # km
const earth_period = 365.242189 # sidereal year in jd
const sun_radius = 695700.0     # km 
const sun_mass = 1.988475e30    # kg
const sun_temperature = 5772.0  # bolometric photospheric temperature in kelvin


# Define functions to be used here

# ###

# Read a 2-column data file and return  x and y vectors

function read_data_file(infile) 
  
  data_text = readlines(infile) 

  # Pre-define empty data arrays of type Float64
  
  x_data = zeros(0) 
  y_data = zeros(0) 

  # Parse the data lines into the values

  for line in data_text 

    # Skip comment line markers by testing for marker characters
    
    if line[1] == '#'
       
      continue
    
    end 
    
    if line[1] == '!' 
       
      continue
    
    end 
                 
    # Separate entries in a data line using common delimiters
    
    # Function occursin requires two string arguments (needle, haystack)  
           
    if occursin(",", line)
            
      entry = split(line,",")       
        
    # Otherwise try separated or tabbed entries
    
    else
    
      entry = split(line)
        
    end
            
    # Test for successful splitting into two data entries
    # Skip any that do not work

    if length(entry) != 2
      
      continue
    
    end
        
    x = parse(Float64,entry[1])
    y = parse(Float64,entry[2])
                     
    push!(x_data, x) 
    push!(y_data, y)

  end    

  # Return two Float64 vectors
  
  return x_data, y_data 

end 


# ###

# Write a 2-column data file of  x and y vectors
# Requires using DelimitedFiles at top level

function write_data_file(outfile, x_array, y_array) 

  open(outfile, "w") do io
    writedlm(io, [x_array y_array])
  end

end


# ###

# Parse text for tagged comments
# Return number of lines of comments and tag-free comment text
     

# Read model parameter file and update the parameter dictionary

function read_parameter_file(infile, dictionary)

  # Read the file
  
  parm_text = readlines(infile) 

  # Parse the text lines into parameters

  for line in parm_text 
                    
    # Skip comments marked by first character # or !

    if line[1] == '#'
      println(line)
      continue
    end  

    if line[1] == '!'   
      println(line)
      continue
    end  
    
    # Skip but warn of parameter file issues
    
    if !occursin("=", line)
      println("This line ")
      println(line)
      println("was found without an = separator in ", infile)
      continue
    end

        
    item = split(line,"=")
    
    # Check for "=" in this line
    
    if !occursin("=", line)
      println("Error in the parameter file at this line ", line)
      println("Check for an item without an = separator in ", infile)
      exit
    end
    
    # There should be only 2 items on each line after the split

    if length(item) != 2
      println("Error in the parameter file at line ", line)
      println("Check for an ambiguous item in ", infile)
      exit   
    end
 
    # Test for star entries

    if occursin("star_name", line)
      dictionary["star_name"] = split(line,"=")[2]
    end
    
    if occursin("star_flux", line)
      dictionary["star_flux"] = parse(Float64,split(line,"=")[2])
    end
    
    if occursin("star_radius", line)
      dictionary["star_radius"] = parse(Float64,split(line,"=")[2])
    end
    
    if occursin("star_temperature", line)
      dictionary["star_temperature"] = parse(Float64,split(line,"=")[2])
    end
    
    if occursin("star_ld1", line)
      dictionary["star_ld1"] = parse(Float64,split(line,"=")[2])
    end
    
    if occursin("star_ld2", line)
      dictionary["star_ld2"] = parse(Float64,split(line,"=")[2])
    end
    

    # Test for planet entries

    if occursin("planet_name", line)
      dictionary["planet_name"] = split(line,"=")[2]
    end

    if occursin("planet_radius", line)
      dictionary["planet_radius"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("planet_mass", line)
      dictionary["planet_mass"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("planet_temperature", line)
      dictionary["planet_temperature"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("planet_albedo", line)
      dictionary["planet_albedo"] = parse(Float64,split(line,"=")[2])
    end
    
    

    # Test for orbit entries

    if occursin("orbit_name", line)
      dictionary["orbit_name"] = split(line,"=")[2]
    end

    if occursin("orbit_sax", line)
      dictionary["orbit_sax"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("orbit_per", line)
      dictionary["orbit_per"] = parse(Float64,split(line,"=")[2])
    end
    
    if occursin("orbit_inc", line)
      dictionary["orbit_inc"] = parse(Float64,split(line,"=")[2])
    end
    
    if occursin("orbit_omg", line)
      dictionary["orbit_omg"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("orbit_lan", line)
      dictionary["orbit_lan"] = parse(Float64,split(line,"=")[2])
    end
        
    if occursin("orbit_ecc", line)
      dictionary["orbit_ecc"] = parse(Float64,split(line,"=")[2])
      
      # For circular orbits
      # Force the longitude of the ascending node to pi/2
      
      if isapprox(dictionary["orbit_ecc"], 0.0, atol=1.0e-3)
        dictionary["orbit_lan"] = pi/2.0
      end  
    end

    if occursin("orbit_tpa", line)
      dictionary["orbit_tpa"] = parse(Float64,split(line,"=")[2])
    end
    
  end 
  return dictionary
end
    

# ###

# Model of uniform stellar flux for a transit

# Inputs

  # Star, planet, and orbit parameters as one dictionary
  # Array of apparent separations (km)
  # Array of apparent orbital phases (2 pi)
  
# Output

  # Array of model fractional flux for a uniform stellar disk 
  #   transiting a uniform star at each time

function star_flux_uniform_model(parameters, apparent_separation_array, apparent_phase_array, apparent_z_array)

  # For transit modeling in this routine
  #   separations are in scaled to units of star.radius
  #   phases are reduced to 0.0 to 1.0 where
  #   0.0 to 1.0 covers a full orbit
  #   0.0 and 1.0 are equivalent
  #   0.0 to 0.5 are the centers of the secondary event
  #   0.5 to 1.0 are the centers of the primary event

  # Remove the epoch and put phases on a 0 to 1 interval
  phase_remainder_array = mod.( apparent_phase_array, 1.0 )


  # Mandel and Agol (2002) with corrections for logic
  # Claret (2000) for quadratic limb darkening
  # Collins (2018) for Java scalar version
  # Exofast2 occultquad_cel.pro (2018) for vector version
  
  # Find the parameters needed in this function
  
  star_radius = parameters["star_radius"]
  planet_radius = parameters["planet_radius"]
  star_flux  = parameters["star_flux"]
  
  # Scale the apparent separation array to the stellar radius
  
  s_array = apparent_separation_array ./ star_radius
  
  # Scale the planet radius to the stellar radius
  # Take the absolute value just in case a negative value is called (allowed by Exofast) 

  p  = abs(planet_radius/star_radius)
  p2 = p*p
          
  # Condition elements of s_array at the critical junctures
  
  s_array[ isapprox.(s_array, p, atol=1.0e-8) ] = p
  s_array[ isapprox.(s_array, p - 1.0), atol=1.0e-8 ] = p - 1.0
  s_array[ isapprox.(s_array, 1.0 - p), atol=1.0e-8 ] = 1.0 - p
  s_array[ isapprox.(s_array, 0.0), atol=1.0e-8 ] = 0.0
  
  # Helper arrays
  z2_array = s_array .* s_array
 
  # Mandel and Agol uniform source cases:
  # p = 0           s_array = [0,   inf)
  case_0a = isapprox(p, 0.0, atol=1.0e-8) && (s_array .>= 0.0)
  # p = (0, inf)    s_array = [1 + p, inf)
  case_0b = (p > 0.0) &&  (s_array .> (1.0 + p))
  # p = (0, inf)    s_array = (|1 - p|, 1 + p] 
  case_0c = (p > 0.0) &&  (s_array .> abs(1.0 - p)) &&  (s_array .<= (1.0 + p))
  # p = (0, inf)    s_array = [0, 1 - p]
  case_0d = (p > 0.0) &&  (s_array .>= 0.0) && (s_array .<= (1.0 - p))  
  # p = (0, inf)    s_array = [0, p - 1]
  case_0e = (p > 0.0) &&  (s_array .>= 0.0) && (s_array .<= (p - 1.0))  


  # Evaluate cases for a uniform source
  
  # Case 0a 
  # Star is unocculted
  # No action is needed since the arrays are zero by default

  # Case 0b
  # Planet is ingressing or egressing and partly on the disk
  kappa_0_array = acos( (p2 .- z2_array) ./ ( (2.0*p) .* s_array ) )
  kappa_1_array = acos( ( (1.0 - p2) .+ z2_array) ./ (2.0 .* s_array) )
  lambda_0_array = p2 .* kappa_0_array .+ kappa_1_array .- sqrt.(z2_array .- 0.25 .* (1.0 .+ z2_array .- p2) .* ( 1.0 .+ z2_array .- p2))
  lambda_0_array = lambda_0_array ./ pi
  lambda_e_array[ case_0b ] = lambda_0_array

  # Case 0c
  # Planet is fully on the disk 
  lambda_e_array[ case_0c ] = p2
  
  # Case 0d
  # Planet covers the star completely
  lambda_e_array[ case_0d ] = 1.0
  

  star_flux_uniform_array = (1.0 .- lambda_e_array) .* star_flux  
  return star_flux_uniform_array
end


# ###

# Model of limb-darkened stellar flux for a transit

# Inputs

  # Star, planet, and orbit parameters as one dictionary
  # Array of apparent separations (km)
  # Array of apparent orbital phases (2 pi)
  
# Output

  # Array of fractional fluxes for a planet 
  #   transiting a quadratically limb-darkened star at each time
  # Array of fractional fluxes for a planet 
  #   transiting a uniform star at each time


function star_flux_limb_darkened_model(parameters, apparent_separation_array, apparent_phase_array, apparent_z_array)


  # For transit modeling in this routine
  #   separations are in scaled to units of star.radius
  #   phases are reduced to 0.0 to 1.0 where
  #   0.0 to 1.0 covers a full orbit
  #   0.0 and 1.0 are equivalent
  #   0.0 to 0.5 are the centers of the secondary event
  #   0.5 to 1.0 are the centers of the primary event

  # Sphorer's Matlab version for circular orbits:
  #   z = ar * ( sin(2*pi*phase ).^2 + ( (br/ar)*cos(2*pi*phase) ).^2 ).^(1/2)
  #   where ar is the orbital radius and br is the impact parameter (closest approach to center)

  # Mandel and Agol (2002) with corrections for logic
  # Claret (2000) for quadratic limb darkening
  # Collins (2018) for Java scalar version
  # Exofast2 occultquad_cel.pro (2018) for vector version

  # Create local parameters with readable names
   
  star_radius = parameters["star_radius"]
  planet_radius = parameters["planet_radius"]
  star_flux  = parameters["star_flux"]
  
  # The Claret parameters are star_ld1 and star_ld2 in Exofast
  star_ld1 = parameters["star_ld1"]
  star_ld2 = parameters["star_ld2"]

  # Remove the epoch and put phases on a 0 to 1 interval if they are not
  phase_remainder_array = mod.( apparent_phase_array, 1.0 )
  
  # Scale the unsigned apparent separation array explicitly to the stellar radius 
  s_array = apparent_separation_array ./ star_radius

  # Save how many elements since it is used often
  ns = length(s_array)
  
  # Scale the planet radius to the stellar radius
  # Take the absolute value just in case a negative value is called (allowed by Exofast) 
  p  = abs(planet_radius / star_radius)
  p2 = p*p
  
  # Create arrays of p and p2 for broadcast comparisons with the s_array
  p_array = p .* ones(ns)
  p2_array = p2 .* ones(ns)
        
  # Condition elements of s_array at the critical junctures
  s_array[ isapprox.(s_array, p, atol=1.0e-8) ] .= p
  s_array[ isapprox.(s_array, p - 1.0, atol=1.0e-8) ] .= p - 1.0
  s_array[ isapprox.(s_array, 1.0 - p, atol=1.0e-8) ] .= 1.0 - p
  s_array[ isapprox.(s_array, 0.0, atol=1.0e-8) ] .= 0.0
  
  # These helper arrays require conditioning before broadcast use
  # Mandel and Agol and Exofast use a, b
  # Shporer in the Matlab version uses a, b, q, k0, and k1
  # Collins and Exofast use x1, x2 for similar quantities
         
  a_array = (s_array .- p) .* (s_array .- p)
  b_array = (s_array .+ p) .* (s_array .+ p)
  z2_array = (s_array) .* (s_array)
  q_array = p2 .- z2_array
  q2_array = q_array .* q_array
  n_array = 1.0 .- (1.0 ./ a_array)
  nb_array = 1.0 .- (b_array ./ a_array)
  
  # Compute the Mandel and Agol limb darkening coefficients
  c1 = 0.0
  c2 = star_ld1 + 2.0*star_ld2
  c3 = 0.0
  c4 = -star_ld2
  c0 = 1.0 - c1 - c2 - c3 - c4
  
  # Evaluate the Mandel and Agol normalization factor (their 1.0/(4.0*Omega) )
  omega =  c0/4.0 + c1/5.0 + c2/6.0 + c3/7.0 + c4/8.0
  
  # Find the normalizing factor for the transit terms in the transit model
  flux_norm_ld = 1.0/(4.0*omega)
    
  # Initialize the arrays that determine the flux at each element of the s_array
  lambda_e_array = zeros(ns)
  lambda_d_array = zeros(ns)
  eta_d_array = zeros(ns)
  
  # Define and initialize the Theta (step) function of Mandel and Agol as an array
  theta_array = zeros(ns)
  theta_array[ (p .> s_array) ]  .= 1.0

  # Mandel and Agol (2002) cases
  # The eleven conditions from Mandel and Agol Table 1 
  #  select elements of the array to be redefined
  #  for a transit on a limb-darkened star

  # In Mandel and Agol the [ or ] means the value is allowed at the limit
  #   and the ( or ) means the value is not allowed at the limit
   
  # In Julia the Mandel and Agol uniform source cases are defined as 
  #   Boolean bit-arrays for s_array masking. 
    
  # No planet, no effect, flux defaults to star out of transit
  # p = 0           s_array = [0,   inf)
  # isapprox(p, 0.0, atol=1.0e-8)

  # Before ingress exclusive of contact
  # p = (0, inf)    s_array = (inf, -1 - p)
  # p > 0.0
  case_0a = (s_array .<= (-1.0 - p))  .& (apparent_z_array .> 0.0)

  # After egress exclusive of contact
  # p = (0, inf)    s_array = (1 + p, inf)
  # p > 0.0
  case_0b = (s_array .> (1.0 + p)) .& (apparent_z_array .> 0.0)
    
  # Fully on disk exclusive of contacts
  # p = (0, inf)    s_array = (-1 + p, 1 - p)
  # p > 0.0
  case_0c = (s_array .> (-1.0 + p)) .&  (s_array .<  (1.0 - p)) .& (apparent_z_array .> 0.0) 

  # During  ingress inclusive of contacts
  # p = (0, inf)    s_array = [-1 - p, -1 + p]
  # p > 0.0
  case_0d = (s_array .>= (-1.0 - p)) .&  (s_array .<=  (-1.0 + p)) .& (apparent_z_array .> 0.0)
  
  # During egress inclusive of contacts (Why absolute value here?)
  # p = (0, inf)    s_array = [ 1 - p, 1 + p ]
  # p > 0.0
  case_0e = (s_array .>= abs(1.0 - p)) .&  (s_array .<= (1.0 + p)).& (apparent_z_array .> 0.0)

  # Either ingress or egress
  case_0f = case_0d .| case_0e

  # Large planet covering smaller star 
  # p = (1, inf)    s_array = [1 - p, p - 1]
  # p > 1.0
  case_0g =  (s_array .>= 1.0 - p) .& (s_array .<= (p - 1.0)) .& (apparent_z_array .> 0.0)
    
  # Mandel and Agol case 1: There is no planet or the star is unocculted
  # p = 0           s_array = [0,   inf)
  # p = (0, inf)    s_array = [1 + p, inf)
  # isapprox(p, 0.0, atol=1.0e-8)
  case_1 = s_array .>= (1.0 + p)
    
  # Mandel and Agol case 2: Planet on limb of star
  # p = (0, inf)    s_array = (1/2 + |p - 1/2|, 1 + p) 
  # (p > 0.0)
  case_2 = (s_array .> 0.5 + abs(p - 0.5)) .& (s_array .< (1.0 + p)) .& (apparent_z_array .> 0.0)

  # Mandel and Agol case 3: Inside disk not over center
  # p = (0, 1/2)    s_array = (p, 1 - p)
  # (p > 0.0) && (p < 0.5)
  case_3 = (s_array .> p) .& (s_array .< (1.0 - p)) .& (apparent_z_array .> 0.0)
  
  # Mandel and Agol case 4: Inside disk not over center touching edge 
  # p = (0, 1/2)    s_array = 1 - p  
  # (p > 0.0) && (p < 0.5)
  case_4 = isapprox.(s_array, (1.0 - p), atol=1.0e-8) .& (apparent_z_array .> 0.0)
    
  # Mandel and Agol case 5: Inside disk touching center
  # p = (0, 1/2)    s_array = p
  # (p > 0.0) && (p < 0.5)  
  case_5 = isapprox.(s_array, p, atol=1.0e-8) .& (apparent_z_array .> 0.0)
  
  # Mandel and Agol case 6: Planet diameter is star's radius and edge of planet is on star's center
  # p = 1/2         s_array = 1/2
  # isapprox(p, 0.5, atol=1.0e-8)
  case_6 = isapprox.(s_array, 0.5, atol=1.0e-8) .& (apparent_z_array .> 0.0)
    
  # Mandel and Agol case 7: Edge of planet's disk touches stellar center and planet not entirely inside star
  # p = (1/2, inf)  s_array = p
  # p > 0.5
  case_7 = isapprox.(s_array, p, atol=1.0e-8) .& (apparent_z_array .> 0.0)
  
  # Mandel and Agol case 8: Planet covers center and limb
  # p = (1/2, inf)  s_array = [|1 - p|, p)
  # (p > 0.5)
  case_8 = (s_array .>= abs(1.0 - p)) .& (s_array .< p) .& (apparent_z_array .> 0.0)
  
  # Mandel and Agol case 9: Planet inside stellar disk and covers center
  # p = (0, 1)      s_array = (0, 1/2 - |p - 1/2|)
  # (p > 0.0) && (p < 1.0)
  case_9 = (s_array .> 0.0) .& (s_array .< (0.5 - abs(p - 0.5))) .& (apparent_z_array .> 0.0)
  
  # Mandel and Agol case 10: Planet concentric with star and entirely within stellar disk
  # p = (0, 1)      s_array = 0
  case_10 = (p > 0.0) && (p < 1.0) .& isapprox.(s_array, 0.0, atol=1.0e-8) .& (apparent_z_array .> 0.0)

  # Mandel and Agol case 11: Planet completely eclipses the star
  # p = (1, inf)    s_array = [0, p - 1)
  # p > 1.0
  case_11 =  (s_array .>= 0.0) .& (s_array .< (p - 1.0)) .& (apparent_z_array .> 0.0)

  # Apply these cases to set flux parameter arrays for quadratic limb darkening
  # Corrections to Mandel and Agol from Exofast and AstroImageJ code are incorporated here

  # Evaluate contributions case by case

  # Case 0a 
  # Star is unocculted
  # No action is needed since the arrays are zero by default


  # Cases 0d, 0e, 0f
  # Planet is partly on the disk
  
  select = case_0d .| case_0e .| case_0f

  arg_array = zeros(ns)
  arg_array[select] .= ( -1.0 .+ p2 .+ z2_array[select]) ./ ( (2.0*p) .* s_array[select] )
  kappa_0_array = zeros(ns)
  kappa_0_array[select] .= acos.(arg_array[select])

  arg_array = zeros(ns)
  arg_array[select] .= ( 1.0 .- p2 .+ z2_array[select]) ./ ( 2.0 .* s_array[select] )  
  kappa_1_array = zeros(ns)
  kappa_1_array[select] .= acos.(arg_array[select])  

  arg_array = zeros(ns)
  arg_array[select] .= z2_array[select] .- 0.25 .* (1.0 .+ z2_array[select] .- p2) .* (1.0 .+ z2_array[select] .- p2)

  lambda_e_array  = zeros(ns)
  lambda_e_array[select] .= ( p2 .* kappa_0_array[select] .+ kappa_1_array[select] .- sqrt.(arg_array[select]) ) ./ pi
  

  # Case 0c
  # Planet is fully on the disk 

  select = case_0c
  lambda_e_array[ select ] .= p2

  # Case 0g
  # Planet covers the star completely

  select = case_0g
  lambda_e_array[ select ] .= 1.0   


  # Case 1
  # There is no planet or the star is unocculted

  select = case_1
  eta_5_array = zeros(ns)
  eta_5_array[select] .= 0.
  

  # Case 11
  # Planet completely eclipses the star

  select = case_11
  eta_4_array = zeros(ns)
  eta_4_array[select] .= 0.5 


  # Case 6
  # Planet diameter is star's radius and edge of planet is on star's center

  select = case_6
  eta_3_array = zeros(ns)
  eta_3_array[select] .= (3.0/32.0)


  # Cases 3, 4, 5, 9, 10
  # Planet inside the stellar disk

  select = case_3 .| case_4 .| case_5 .| case_9 .| case_10
  eta_2_array = zeros(ns)
  eta_2_array[select] .= (0.5*p2) .* (p2 .+ (2.0 .* z2_array[select]))
  

  # Cases 2, 7, 8
  # Planet covering the limb 

  select = case_2 .| case_7 .| case_8
  eta_2_array[select] .= (0.5*p2) .* (p2 .+ (2.0 .* z2_array[select]))

  arg_array = zeros(ns)
  arg_array[select] .= ( -1.0 .+ p2 .+ z2_array[select]) ./ ( (2.0*p) .* s_array[select] )
  kappa_0_array = zeros(ns)
  kappa_0_array[select] .= acos.(arg_array[select])

  arg_array = zeros(ns)
  arg_array[select] .= ( 1.0 .- p2 .+ z2_array[select]) ./ ( 2.0 .* s_array[select] )  
  kappa_1_array = zeros(ns)
  kappa_1_array[select] .= acos.(arg_array[select])  
   
  eta_1_array = zeros(ns)
  arg_1_array = zeros(ns)
  arg_2_array = zeros(ns)
  arg_3_array = zeros(ns)

  arg_1_array[select] .= kappa_1_array[select] .+ 2.0 .* eta_2_array[select] .* kappa_0_array[select]
  arg_2_array[select] .=  sqrt.( (1.0 .- a_array[select]) .* (b_array[select] .- 1.0) ) 
  arg_3_array[select] .= 0.25 .* (z2_array[select] .+ (5.0*p2 + 1.0)) .* arg_2_array[select]
  eta_1_array[select] .= (0.5/pi) .* (arg_1_array[select] .- arg_3_array[select])


  # Calculate the elliptic integrals for lambda_1

  k2_array = ones(ns)
  k2_array[select] .= (1.0 .- a_array[select]) ./ ( (4.0*p) .* s_array[select] )

  ellint1_array = zeros(ns)
  ellint2_array = zeros(ns)
  ellint3_array = zeros(ns)
  arg_1_array, arg_2_array = ellint( k2_array[select] )
  arg_3_array = ellint3(n_array[select], k2_array[select])
  ellint1_array[select] .= arg_1_array
  ellint2_array[select] .= arg_2_array  
  ellint3_array[select] .= arg_3_array


  # Case 2
  # Planet on the limb of the star
  
  select = case_2
  
  arg_1_array = zeros(ns)
  arg_1_array[select]  .= ( 1.0 .- b_array[select]) .* ( 2.0 .* b_array[select] .+ a_array[select] .- 3.0 )
  
  arg_1_array[select]  .=  arg_1_array[select] .- 3.0 .* q_array[select] .* (b_array[select] .- 2.0)
  arg_1_array[select]  .=  arg_1_array[select] .* ellint1_array[select]

  arg_2_array = zeros(ns)
  arg_2_array[select]  .= (4.0*p) .* s_array[select] .* (z2_array[select] .+ (7.0*p2 - 4.0) )
  arg_2_array[select]  .= arg_2_array[select] .* ellint2_array[select]  
  
  arg_3_array = zeros(ns)
  arg_3_array[select]  .=  -3.0 .* q_array[select] .* ellint3_array[select] ./ a_array[select] 
  
  arg_4_array = zeros(ns)    
  arg_4_array[select]  .= arg_1_array[select] .+ arg_2_array[select] .+ arg_3_array[select] 

  lambda_1_array = zeros(ns)
  lambda_1_array[select] .=  (1.0/(9.0*pi)) .* arg_4_array[select] ./ sqrt.(p .* s_array[select])
         

  # Cases 3, 9 
  # Inside the disk

  select = case_3 .| case_9

  k2_array = ones(ns)
  k2_array[select] .= (1.0 .- a_array[select]) ./ ( (4.0*p) .* s_array[select] )
  ellint1_array = zeros(ns)
  ellint2_array = zeros(ns)
  ellint3_array = zeros(ns)
  arg_1_array, arg_2_array = ellint(1.0 ./ k2_array[select])
  arg_3_array = ellint3(nb_array[select], (1.0 ./ k2_array[select]))  
  ellint1_array[select] .= arg_1_array
  ellint2_array[select] .= arg_2_array  
  ellint3_array[select] .= arg_3_array
    
  arg_1_array = zeros(ns)
  arg_1_array[select] .= (1.0 .- 5.0 .* z2_array[select] .+ p2) .+ q2_array[select]
  arg_1_array[select] .= arg_1_array[select] .* ellint1_array[select]

  arg_2_array = zeros(ns)
  arg_2_array[select] .= (1.0 .- a_array[select]) .* (z2_array[select] .+ 7.0*p2 .- 4.0) 
  arg_2_array[select] .= arg_2_array[select] .* ellint2_array[select]   

  arg_3_array = zeros(ns)
  arg_3_array[select] .= -3.0 .* q_array[select] ./ a_array[select] 
  arg_3_array[select] .= arg_3_array[select] .* ellint3_array[select]
  
  lambda_2_array = zeros(ns)
  lambda_2_array[select] .= arg_1_array[select] .+ arg_2_array[select]  .+ arg_3_array[select] 
  lambda_2_array[select] .= lambda_2_array[select]  ./ sqrt.(1.0 .- a_array[select]) 
  lambda_2_array[select] = (2.0/(9.0*pi)) .* lambda_2_array[select]  


  # Case 7
  # Edge of the planet's disk touches the stellar center

  select = case_7
   
  # Calculate the elliptic integrals for lambda_3 
  # Corrected typographical error in paper by  1/2k -> 1/2p  
  
  q_array = zeros(ns)
  q_array[select] .= (0.5/p) 
  ellint1_array, ellint2_array = ellint(q_array)
  
  arg_1_array = zeros(ns)
  arg_1_array[select] .= 1.0/3.0 .+ (2.0*p2 - 1.0)*16.0*p/(9.0*pi) .* ellint2_array[select]
  arg_2_array = zeros(ns)
  arg_2_array[select] .= ( (1.0 - 4.0*p2)*(3.0 - 8.0*p2)/(9.0*p*pi) ) .* ellint1_array[select]
  lambda_3_array = zeros(ns)
  lambda_3_array[select] .= arg_1_array[select] .- arg_2_array[select]


  # Case 5
  # Edge of the planet's disk touches the center of the stellar disk  
  
  select = case_5

  q_array_4 = (2.0*p) .* ones(ns)
  ellint1_array_4, ellint2_array_4 = ellint(q_array_4)
  
  lambda_4_array = zeros(ns)
  lambda_4_array_arg_1 =  4.0*(2.0*p2 - 1.0) .* ellint2_array_4
  lambda_4_array_arg_2 = (1.0 - 4.0*p2) .* ellint1_array_4 
  lambda_4_array_arg_3 = lambda_4_array_arg_1 .+ lambda_4_array_arg_2
  lambda_4_array[select] .= 1.0/3.0 .+ (2.0/(9.0*pi)) .* lambda_4_array_arg_3[select]


  # Case 4
  # The planet's disk is entirely inside the stellar disk

  select = case_4
  
  lambda_5_array_arg_1 = (2.0/(3.0*pi)) * acos((1.0 - 2.0*p))  .* ones(ns) 
  lambda_5_array_arg_2 = ((4.0/(9.0*pi))*(3.0 + 2.0*p - 8.0*p2)) .* ones(ns)
  lambda_5_array = zeros(ns)
  lambda_5_array[select] .= lambda_5_array_arg_1[select] .- lambda_5_array_arg_2[select]
    

  # Case 10
  # Planet is concentric with the disk of the star
  #   and at the precise bottom of the transit flux minimum

  select = case_10

  lambda_6_array_arg_1 = -((2.0/3.0)*(1.0 - p2)*sqrt(1.0 - p2)) .* ones(ns)
  lambda_6_array = zeros(ns)
  lambda_6_array[select] .= lambda_6_array_arg_1[select]
  
  
  # Calculate lambda_7
  # Case 6 
  # The planet's diameter equals the star's radius
  #   and the edge of the planet's disk touches both the stellar center and the limb of the star
  
  select = case_6
  
  lambda_7_array_arg_1 = (1.0/3.0 - 4.0/(9.0*pi)) .* ones(ns)
  lambda_7_array = zeros(ns)
  lambda_7_array[select] .= lambda_7_array_arg_1[select]

  
  # Case 11
  # The planet completely eclipses the star

  select = case_11

  lambda_8_array_arg_1 = ones(ns)
  lambda_8_array = zeros(ns)
  lambda_8_array[select] .= lambda_8_array_arg_1[select]
  
  lambda_8_array = zeros(ns)
  lambda_8_array[select] .= ones(ns)[select]


  # Evaluate the flux case by case using these lambda and eta values

  # Case 1
  # Star is unocculted
  # No action is needed since the arrays are zero by default
     
  # Case 2
  # Planet disk on limb of star but not on center of disk
  # Light curve is steepest here 
  lambda_d_array[ case_2 ] = lambda_1_array[ case_2 ]  
  eta_d_array[ case_2 ] = eta_1_array[ case_2 ]  

  # Case 3
  # Planet disk inside stellar disk
  lambda_d_array[ case_3 ] = lambda_2_array[ case_3 ]  
  eta_d_array[ case_3 ] = eta_2_array[ case_3 ]

  # Case 4
  # Planet disk inside stellar disk touching edge of disk
  lambda_d_array[ case_4 ] = lambda_5_array[ case_4 ]  
  eta_d_array[ case_4 ] = eta_2_array[ case_4 ]
 
  # Case 5
  # Planet disk inside stellar disk and touches center
  lambda_d_array[ case_5 ] = lambda_4_array[ case_5 ]  
  eta_d_array[ case_5 ] = eta_2_array[ case_5 ]
 
  # Case 6
  # Planet diameter equals the stellar radius and it touches both the stellar center and limb
  lambda_d_array[ case_6 ] = lambda_7_array[ case_6 ]  
  eta_d_array[ case_6 ] = eta_3_array[ case_6 ]
  
  # Case 7
  # Planet edge touches the stellar center, but the planet extends beyond the stellar disk
  lambda_d_array[ case_7 ] = lambda_3_array[ case_7 ]  
  eta_d_array[ case_7 ] = eta_1_array[ case_7 ]

  # Case 8
  # Planet over the center and the limb of the stellar disk
  lambda_d_array[ case_8 ] = lambda_1_array[ case_8 ]  
  eta_d_array[ case_8 ] = eta_1_array[ case_8 ]
  
  # Case 9
  # Planet entirely inside the stellar disk and over the stellar center
  lambda_d_array[ case_9 ] = lambda_2_array[ case_9 ]  
  eta_d_array[ case_9 ] = eta_2_array[ case_9 ]
  
  # Case 10
  # Planet is concentric with the disk of the star precisely at Tc
  lambda_d_array[ case_10 ] = lambda_6_array[ case_10 ]  
  eta_d_array[ case_10 ] = eta_2_array[ case_10 ]
  
  # Case 11
  # Planet completely eclipses the star
  lambda_d_array[ case_11 ] = lambda_8_array[ case_11 ]  
  eta_d_array[ case_11 ] = eta_4_array[ case_11 ]
     
  # Evaluate the effects of limb darkening
  
  # Mandel and Agol quadratic limb darkening in Section 4
  # F = 1 - (4\Omega}^{-1} \times ( (1 - c_2)\lambda_e + c_2( \lambda_d + (2/3)\Theta(p-z) ) - c_4\eta_d )
  #  where c2 = ld1 + 2 ld_2 and c4 = - ld2
      
  star_flux_limb_darkened_array_arg_1 = (1.0 - c2).* lambda_e_array 
  star_flux_limb_darkened_array_arg_2 = c2 .* (lambda_d_array .+ (2.0/3.0) .* theta_array)
  star_flux_limb_darkened_array_arg_3 = -c4 .* eta_d_array
  star_flux_limb_darkened_array_arg_4 = star_flux_limb_darkened_array_arg_1 .+ star_flux_limb_darkened_array_arg_2
  star_flux_limb_darkened_array_arg_5 = star_flux_limb_darkened_array_arg_4 .+ star_flux_limb_darkened_array_arg_3
  star_flux_limb_darkened_array_arg_6 = flux_norm_ld .* star_flux_limb_darkened_array_arg_5
  
  star_flux_limb_darkened_array = star_flux .* (1.0 .- star_flux_limb_darkened_array_arg_6)  
  star_flux_uniform_array = star_flux .* (1.0 .- lambda_e_array)

  return star_flux_limb_darkened_array, star_flux_uniform_array
  
end
    
    

# ###

# Planet flux model

# Inputs

  # Star, planet, and orbit properties
  # Apparent separationd of planet from star
  # Apparent phases of orbit
  # Apparent line of sight distanced  
  # True separations of planet from star
  
# Output

  # Array of planet fluxes at each position


function planet_flux_model(parameters, apparent_separation_array, apparent_phase_array, apparent_z_array, planet_to_star_array)
  
  # This is a placeholder for the transit flux from the planet
  # As is, it assumes zero Bond albedo and no thermal emission
  
  planet_flux_array = zeros(length(apparent_separation_array))
  
  return planet_flux_array

end


# ###

# Invert Kepler's equation to find the eccentric anomaly for a given mean anomaly
#
#   mean_anomaly = eccentric_anomaly - e \sin(eccentric_anomaly) 
#
#
# Inputs:
#   mean_anom_array:  mean anomaly array 
#   orbit_ecc:  orbital eccentricity scalar 

# Output:
#   ecc_anom_array: eccentric anomaly array of solutions

# Adapted from Helge Eichhorn, Reiner Anderl, Juan Luis Cano, and Frazer McLean
# Comparative study of programming languages for next-generation astrodynamics
#   systems
# https://indico.esa.int/event/111/contributions/266/attachments/348/389/paper.pdf
# Listed in ADS and published in a springer journal
# Eichhorn, H., Cano, J.L., McLean, F. et al. 
# A comparative study of programming languages for next-generation
# astrodynamics systems. 
# CEAS Space J 10, 115-123 (2018). 
# https://doi.org/10.1007/s12567-017-0170-8
# Modified by Gemini Pro to ensure bounded output


function solve_kepler(mean_anom_array, orbit_ecc)
  maximum_iterations = 100
  tolerance = 1.0e-8

  # Force mean anomalies into [-pi, pi]
  mean_anom_array = rem2pi.(mean_anom_array, RoundNearest)
  
  # Added element-wise 
  last_array = mean_anom_array .+ orbit_ecc .* sign.(sin.(mean_anom_array))
  
  # Iterative solution
  for this_step in 1:maximum_iterations    
    solution_array = last_array .- orbit_ecc.*sin.(last_array) .- mean_anom_array
    derivative_array = 1.0 .- orbit_ecc.*cos.(last_array)    
    new_array = last_array .- solution_array./derivative_array
    
    # Test for convergence
    test_array = isapprox.(new_array, last_array, atol=tolerance)    
    if all(test_array) 
      # Ensure the final converged eccentric anomaly is strictly bounded [-pi, pi]
      return rem2pi.(new_array, RoundNearest)
    end
    
    last_array = new_array
  end  
  
  println("The Kepler inversion did not converge.")
  return rem2pi.(last_array, RoundNearest)
end


# Find the true anomaly from the eccentric anomaly for a full orbit
# Preserve the quadrant of the orbit from -pi to +pi
function get_true_anomaly(ecc_anom_array, orbit_ecc)
    # y corresponds to the sine component (scaled by semi-minor axis factor)
    y = sqrt(1.0 - orbit_ecc^2) .* sin.(ecc_anom_array)
    
    # x corresponds to the cosine component
    x = cos.(ecc_anom_array) .- orbit_ecc
    
    # atan(y, x) preserves the quadrant from -pi to +pi
    return atan.(y, x) 
end


# ###

# Center of planet relative to center of star
# Accepts an array of times
# Returns an array of separations in units of the orbit sax
# Based on Karen Collins version derived from ExoFAST 

# Inputs
#   time_array: np array of barycentric julian dates for which to compute the flux (units of day)
#     These times should be in the star's barycentric reference frame
#   orbit parameters:
#     sax: semi-major axis (units of host star radius)
#     per: period (days)
#     inc: inclination (units of radians)
#     ecc: eccentricity defaults to 0
#     omg: omega, the argument of the periapsis of the orbit (units of radians)
#     tpa: time of periapsis (units of BJD)
#     lan: longitude of the ascending node (units of radians)
#       default value is pi

# Output

#   separation_array: np array of apparent center-of-planet to center-of-star separations
#     for each corresponding element in time_array (km)
#   phase_array: np array of apparent phases (2 pi)
#   planet_to_star_separation: np array of actual center-of-planet to center_of_star separations
#     for each corresponding element in time_array (km) 


function planet_center(parameters, time_array)
   
  # In EXOFAST 
  #   ecc is 0 if not specified
  #   omg is the argument of periapsis of the star's orbit in radians
  #   omg_* is typically quoted from RV
  #   is required if e is specified
  #   is assumed to be pi/2 if e not specified
  #   omg_* = omega_planet + pi
  #   lan is set to pi if not specified
  #   Exofast calls this the impact parameter whereas the conventional
  #     impact parameter would be the planet separation at transit event center 

  # In AstroImageJ
  #    The routine is impactParameter
  #    Derived from EXOFAST
  #    Called with  zArray = impactParameter(bjd, inclination, ar, tp, P, e, omega, useLonAscNode, lonAscNode);
  #      where impact parameter is in units of star.radius
  #    Employed in transitModel
      
  # Karen Collins: meananom = (2.0*PI*(1.0 + (bjd[i] - tp)/P)) % (2.0*PI)
  # mean_anom_array = np.mod( 2.0*np.pi*(1.0 + (time_array - orbit_tpa)/orbit_period), 2.0*np.pi)
  # np.mod is an alias for np.remainder

  # Orbit parameters are held in the parameters dictionary
  
  # Reference plane is tangent to the celestial sphere
  #   It is normal to the vector to the Sun
  # Reference direction is in the reference plane 
  #   Right ascension is on x decreasing to (+x), i.e. to west
  #   Declination is on y increasing to (+y), i.e. to north
  # Parameter orbit_inc is the inclination of the orbit plane 
  #   Measure in radians from the reference plane
  #   Equivalent to angle between the normals of the orbit and reference planes
  #   Equal to 0 when the orbit is in the plane of the sky with no possiblity of a transit
  #   Equal to pi/2 when the orbit appears to cross the center of the star
  #   More than pi/2 when the orbit crosses above center (+y)
  #   Less than pi/2 when the orbit crosses below center (-y)
  # Parameter orbit_omg is the argument of periapsis (small omega) 
  #   Measure in radians in the orbit plane from the ascending node
  #   Equal to 0 when periapsis is at the ascending node
  #   Equal to pi when periapsis is at the decending node
  #   For an orbit in the plane of the sky it increases counter-clockwise
  # Parameter orbit_lan is the longitude of the ascending node (big omega)
  #   Measure in radians in the reference plane 
  #   From the reference direction 
  #   Counter-clockwise to the direction of the ascending node
  #   Same sense as small omega when the orbit is in the reference plane 
  #   Equal to 0 or 2 pi  if the ascending node is toward (+x)
  #   Equal to -pi if the ascending node is toward (-x)
  #   With pi/2 inclination and orbit_lan 0
  #     planet moves from (+x) to (-x) across the star with no (y) motion
  #   With pi/2 inclination and orbit_lan pi 
  #     planet moves from (-x) to (+x) across the star with no (y) motion
  #   With 0 inclination and 0 omega
  #     planet moves from bottom to top, i.e. from (-y) to (+y) with no (x) motion
  #   With 0 inclination and pi omega
  #     planet moves from top to bottom, i.e. from (+y) to (-y) with no (x) motion 



  orbit_tpa = parameters["orbit_tpa"] # time of periapsis (d) sets the reference time for the mean anomaly
  orbit_per = parameters["orbit_per"] # period of the orbit (d) from one periapsis to the next
  orbit_ecc = parameters["orbit_ecc"] # eccentricity of the orbit (focus offset / sax)
  orbit_omg = parameters["orbit_omg"] # argument of periapsis (small omega radians ccw in plane of orbit)
  orbit_sax = parameters["orbit_sax"] # semimajor axis of ellipse (sets scale, any unit)
  orbit_inc = parameters["orbit_inc"] # orbit plane normal to reference direction (radians)
  orbit_lan = parameters["orbit_lan"] # longitude of ascending node in the plane of reference

  # Find the mean anomaly in radians for the time series 
  mean_anom_array = (2pi/orbit_per).*(time_array .- orbit_tpa)

  write_data_file("time-mean-anom.dat", time_array, mean_anom_array)

  # Find the true anomalies for these mean anomalies by solving the Kepler equation when needed 
  if isapprox(orbit_ecc, 0.0, atol=1.0e-3)  
    true_anom_array = mean_anom_array    
  else
    # Find the eccentric anomalies
    ecc_anom_array = solve_kepler(mean_anom_array, orbit_ecc) 
    
    # Find corresponding true anomalies 
    true_anom_array = get_true_anomaly(ecc_anom_array, orbit_ecc) 
           
  end
  
  write_data_file("time-true-anom.dat", time_array, true_anom_array)
  
  # Find the position of the planet in units of (orbit_sax)
  # Coordinates in the 2D orbital plane
  orbit_r_array = orbit_sax*(1.0 - orbit_ecc*orbit_ecc) ./ (1.0 .+ orbit_ecc .* cos.(true_anom_array))
  orbit_x_array = orbit_r_array .* cos.(true_anom_array) 
  orbit_y_array = orbit_r_array .* sin.(true_anom_array)  
  
  # First rotation by the argument of periapsis around the z-axis normal to the orbit plane
  
  x1_array = orbit_x_array .* cos(orbit_omg) - orbit_y_array .* sin(orbit_omg)
  y1_array = orbit_x_array .* sin(orbit_omg) + orbit_y_array .* cos(orbit_omg)
  z1_array = 0.0 .* orbit_y_array
  
  # Second rotation by the inclination  around the new x-axis
  
  x2_array = x1_array
  y2_array = y1_array .* cos(orbit_inc)
  z2_array = y1_array .* sin(orbit_inc)
  
  # Third rotation by the longitude of the ascending node around the new z-axis
    
  observed_x_array = x2_array.*cos(orbit_lan) .- y2_array .* sin(orbit_lan)
  observed_y_array = x2_array.*sin(orbit_lan) .+ y2_array .* cos(orbit_lan)
  observed_z_array = z2_array
  observed_r_array = sqrt.(observed_x_array.*observed_x_array .+ observed_y_array.*observed_y_array)
        
  # Observed separations are given in (orbit_sax)
  # Phases of the planetary positions are given in (2 pi), e.g. 0 to 1 for a full period
  # Retain the full phase so that multiple epochs may be treated in one array
  observed_phase_array = (time_array .- orbit_tpa)./orbit_per
  
  
  # Diagnostic files
  
  write_data_file("observed-x-y.dat", observed_x_array, observed_y_array)
  write_data_file("observed-t-x.dat", time_array, observed_x_array)
  write_data_file("observed-t-y.dat", time_array, observed_y_array)
  write_data_file("observed-t-z.dat", time_array, observed_z_array)
  write_data_file("observed-t-phase.dat", time_array, observed_phase_array)
  
  return observed_r_array, observed_phase_array, observed_z_array, orbit_r_array

end  

# ###
#
# Complete elliptic integral of the third kind
# Elliptic integral of the third kind Pi(n,k)
# Pi(n,k) = \int_0^{\pi/2} d\theta /( (1+n\sin^2\theta)(\sqrt(1-k^2\sin^2\theta) }
#
# Wolfram defines with Pi(n,m) with m = k^2 and the opposite sign for n
#
# See https://functions.wolfram.com/EllipticIntegrals/EllipticPi/introductions/
#   CompleteEllipticIntegrals/ShowAll.html
# 
# Inputs:
#   n > -1.0  numpy array of values  greater than -1.0 but no upper limit
#   k [-1,1]  numpy array of values  with absolute value less than 1.0
#  
# Output:
#   Numpy array of values of the integral for each n,k pair
#   
# Derived from Eastman's IDL Exofast routines
# Tested against  https://calcresource.com/eval-elliptic3.html and ellint3_burlirsch.py
# Note opposite sign convention in this routine and in the cited online resources

function ellint3(n_array, k_array)
    
  # Find the complete elliptic integral of the third kind 
  # This is often Pi
  # Use the Burlirsch algorithm adapted from Jason Eastman's Exofast2
  # Bulirsch 1965, Numerische Mathematik, 7, 78
  # Bulirsch 1965, Numerische Mathematik, 7, 353

  # Tests for acceptable inputs would go here
  # [-1 < n < inf) [0 < k < 1]
  
  # This version set to match matlab's 
  
  p_array = sqrt.(1.0 .- n_array)
  d_array = 1.0 ./ p_array

  kc_array = sqrt.(1.0 .- abs.(k_array))

  m0_array = ones(length(n_array))
  c_array = ones(length(n_array))
  e_array = kc_array
  
  tolerance = 1.0e-9
  tolerance_flag = true
  n_iter = 0
  max_iter = 1000
  while tolerance_flag && (n_iter < max_iter)
    f_array = c_array
    c_array = (d_array ./ p_array) .+ f_array
    g_array = e_array ./ p_array
    d_array = 2.0 .* ((f_array .* g_array) .+ d_array)
    p_array = g_array .+ p_array  
    g_array = m0_array 
    m0_array = kc_array .+ m0_array
    tol_array = abs.(1.0 .- (kc_array ./ g_array))
    if ( any( tol_array .> tolerance ) ) 
      kc_array = 2.0 .* sqrt.(e_array)
      e_array = kc_array .* m0_array
      n_iter = n_iter + 1
    else
      tolerance_flag = false
    end
  end
  
  ell_arg_1_array = c_array .* m0_array  .+ d_array
  ell_arg_2_array = m0_array .+ p_array
  ell_arg_3_array = m0_array .* ell_arg_2_array
  ellint3_array = (0.5 * pi) .* ell_arg_1_array ./ ell_arg_3_array
  
  return ellint3_array  

end


# ###

# Complete elliptic integral of the first and second kind
#   Hasting's Pade approximation solution
#   Complete elliptic integral of the first kind is often K
#   Complete elliptic integral of the second kind is often E

#  Inputs:
#    k:  array of floating point parameters

#  Outputs:
#    ellint1: array of corresponding elliptic  integrals of the first kind 
#    ellint2: array of corresponding ellilptic integrals of the second kind

function ellint(m_array)
  
  #  Computes Hasting's polynomial approximation for the complete 
  #  elliptic integral of the first (K(m)) and second (E(m) kind. 
  #
  # From Ali and Harrison (1964) and Hastings (1955)
  # 
  # The scipy.special.ellipk function K(m) documentation has the note
  #   that it uses the parameterization  of Abramowitz and Stegun (1972)
  #
  # Mathematica and Matlab use the integral over 1/sqrt(1 - m sin^2(theta))
  #   For consistency, this routine follows that convention.  
  #   It is the same notational convention used for E and K in Mandel and Agol.
  #
  # The internal Python routines for K and and E are called this way
  #   ellipk_array = ellipk(m_array)
  #   ellipe_array = ellipe(m_array)
  
  # Using the notation of Ali and Harrison for clarity

  eta_array = 1.0 .- m_array

  # Test and modify out of bounds in eta_array
  
  below_mask = eta_array .< 0.0
  above_mask = eta_array .> 1.0
  eta_array[ below_mask ] .= 0.0
  eta_array[ above_mask ] .= 1.0 

  log_eta_array = log.(eta_array)

  # Coefficients for elliptic integral of the first kind

  a0 = 1.38629436112
  a1 = 0.09666344259
  a2 = 0.03590092383
  a3 = 0.03742563713
  a4 = 0.01451196212

  b0 = 0.5
  b1 = 0.12498593597
  b2 = 0.06880248576
  b3 = 0.03328355346
  b4 = 0.00441787012
  
  # Coefficients for elliptic integral of the second kind
  
  c1 = 0.44325141463
  c2 = 0.06260601220
  c3 = 0.04757383546
  c4 = 0.01736506451

  d1 = 0.24998368310
  d2 = 0.09200180037
  d3 = 0.04069697526
  d4 = 0.00526449639
  
  eta_array_p2 = eta_array .* eta_array
  eta_array_p3 = eta_array_p2 .* eta_array
  eta_array_p4 = eta_array_p3 .* eta_array
  
  ellint1_array_asum = a1 .* eta_array .+ a0
  ellint1_array_asum = ellint1_array_asum .+ a2.*eta_array_p2  
  ellint1_array_asum = ellint1_array_asum .+ a3.*eta_array_p3
  ellint1_array_asum = ellint1_array_asum .+ a4.*eta_array_p4
  ellint1_array_bsum = b1 .* eta_array .+ b0
  ellint1_array_bsum = ellint1_array_bsum .+ b2.*eta_array_p2  
  ellint1_array_bsum = ellint1_array_bsum .+ b3.*eta_array_p3
  ellint1_array_bsum = ellint1_array_bsum .+ b4.*eta_array_p4
  ellint1_array_bsum_logeta = ellint1_array_bsum .* log_eta_array
  
  ellint1_array = ellint1_array_asum .- ellint1_array_bsum_logeta 
             
  ellint2_array_csum = c1.*eta_array .+ 1.0
  ellint2_array_csum = ellint2_array_csum .+ c2.*eta_array_p2  
  ellint2_array_csum = ellint2_array_csum .+ c3.*eta_array_p3
  ellint2_array_csum = ellint2_array_csum .+ c4.*eta_array_p4
  ellint2_array_dsum = d1 .* eta_array
  ellint2_array_dsum = ellint2_array_dsum .+ d2.*eta_array_p2  
  ellint2_array_dsum = ellint2_array_dsum .+ d3.*eta_array_p3
  ellint2_array_dsum = ellint2_array_dsum .+ d4.*eta_array_p4
  ellint2_array_dsum_logeta = ellint2_array_dsum .* log_eta_array
  
  ellint2_array = ellint2_array_csum .- ellint2_array_dsum_logeta 
  
  return ellint1_array, ellint2_array

end


# ###

# Model limb-darkened transit versus time for a star and planet system

# Inputs 

#   Note use of physical units with relative scaling applied as needed 
#   time_array: np array of barycentric julian dates for which to compute the flux (units of day)
#     These times should be in the star's barycentric reference frame
#   star:  stellar parameters
#     flux (units of radiant power/area)
#     radius (km)
#     temperature (K)
#     ld1: linear limb darkening coefficient
#     ld2: quadratic limb darkening coefficient 
#   planet:
#     radius (km)
#     temperature (K)
#   orbit:
#     sax: orbit semi-major axis (km)
#     per: orbital period (days)
#     inc: angle between the star-to-Earth vector and the normal to the orbital plane (radians)
#       [0 <= inc <= pi] allowed range
#       [0 <= inc < pi/2]  direct or prograde where the planet proceeds anticlockwise seen from Earth
#       [pi/2 = inc <= pi] retrograde and planet  proceeds clockwise seen from Earth
#       inc == pi/2 motion is transverse on the sky and sense is indeterminant for transit observations alone
#       position angle is measured anticlockwise on the sky and increases with direct motion
#     ecc: orbital eccentricity defaults to 0
#     omg: orbital omega, the argument of the periapsis of the orbit (units of radians)
#       assumed to be PI/2 if e is 0.0
#       omega_* is typically quoted from RV where it is omega_planet + PI
#     tpa: time of periapsis (units of BJD)
#     lan: longitude of the ascending node (units of radians)
#       default value is pi

# Outputs

#   system_flux_array: total flux at each time (units of stellar flux) with planet flux to be added
#   separation_array: separation of planet and star seen by the observer at each time (units of stellar sax)
#   phase_array: phase of the orbit at each time (units of 2 pi)
#   radial_velocity: to be added and is currently available in the observed_z_array by forward differencing

function transit_model(parameters, time_array)
     
  # For times in the array find the apparent separation and transit phase
  observed_r_array, observed_phase_array, observed_z_array, orbit_r_array = planet_center(parameters, time_array)
  
  # Fractional flux with limb darkening and the undarkened flux as a benefit 
  star_flux_array, star_flux_uniform_array  = star_flux_limb_darkened_model(parameters, observed_r_array, observed_phase_array, observed_z_array)
          
  # Contribution to the flux from the planet itself
  planet_flux_array = planet_flux_model(parameters, observed_r_array, observed_phase_array, observed_z_array, orbit_r_array)
  
  # Add star and planet
  system_flux_array = star_flux_array .+ planet_flux_array
              
  return system_flux_array, observed_r_array, observed_phase_array

end


# Execution begins here
# Read the command line

if length(ARGS) != 2
  println("Use parameters.dat and flux.dat on the command line.")
  exit()
end
   
parmfile = ARGS[1] 
fluxfile = ARGS[2]

println("Running ", PROGRAM_FILE, " with arguments ", parmfile, " and ", fluxfile)  


# The parameter file may define these values that modify the defaults
# Solar and Earth units are internal so that data are entered relative to them
# These are placeholder global parameters that may be updated by functions

# The dictionary holds values for the models
# Each dictionary refers to a class of objects

# star:  stellar parameters
#   name: any text name [defaults to "TIC"]
#   flux: (surface power/area solar units) [defaults to 1.0]
#   radius: (solar units) [defaults to 1.0]
#   mass: (solar units) [defaults to 1.0]
#   temperature: (solar units) [defaults to 1.0]
#   ld1: linear limb darkening [defaults to 0.3]
#   ld2: quadratic limb darkening [defaults to 0.3]

# planet: planet parameters
#   name: any text name [defaults to "TOI"]
#   radius: (earth) [defaults to 1.0]
#   mass: (earth) [defaults to 1.0]
#   temperature: (earth) [defaults to 1.0]

# orbit:  system orbit parameters
#   name: should match the planet name for futureproof use [defaults to "TIC"]
#   sax:  semi-major axis (units of host star radius) [defaults to 10.0]
#   per:  period (JD) [defaults to 10.0]
#   inc:  inclination (units of radians) [defaults to 0.0]
#   ecc:  eccentricity defaults to [defaults to 0.0]
#   omg:  omega, the argument of the periapsis of the orbit (units of radians) [defaults to 1.5 pi]
#   tpa:  time of periapsis (BJD) [defaults to 0.0]
#   lan:  longitude of the ascending node


# Create one dictionary as a database for all the parameters
# Do not use it in a function call when the execution time is critical

parameters = Dict()

# Add defaults to the dictionary

star = Dict("star_name" => "TIC", "star_flux" => 1.0 , "star_radius" => 1.0, "star_mass" => 1.0, "star_temperature" => 1.0, "star_ld1" => 0.3, "star_ld2" => 0.3)

planet = Dict("planet_name" => "TOI", "planet_radius" => 1.0, "planet_mass" => 1.0, "planet_temperature" => 1.0)

orbit = Dict("orbit_name"=> "TOI", "orbit_sax" => 10.0,  "orbit_per" =>10.0,  "orbit_inc" =>0.0,  "orbit_ecc" =>0.00,  "orbit_omg" => 1.5*pi,  
  "orbit_tpa" => 0.0,  "orbit_lan" => pi)


parameters = merge(parameters, star, planet, orbit)

# Read the requested model parameters and update the dictionary

println("Reading the parameter file ", parmfile)

parameters = read_parameter_file(parmfile, parameters)

# Read the observed or sampling flux array

println("Reading the observed flux array ", fluxfile)

observed_time_array, observed_flux_array = read_data_file(fluxfile)

# Create a model time array of one period at 200 second TESS cadence
model_period = parameters["orbit_per"]
model_cadence = 200.0/86400.0
model_n_times = trunc(Int64, model_period/model_cadence)
model_start_time = observed_time_array[1] - model_period/4.0
model_time_array = [model_start_time + (i - 1) * model_cadence for i in 1:model_n_times] 

# Run the model 

model_flux_array, model_separation_array, model_phase_array = transit_model(parameters, model_time_array)


# Save the model time and flux 

parmfile_base = split(parmfile, ".")[1]
outfile = parmfile_base*"_model_flux.dat"

time_zero = trunc(observed_time_array[1])
model_reduced_time_array = model_time_array .- time_zero
observed_reduced_time_array = observed_time_array .- time_zero
time_zero_str = string(Int(time_zero))

write_data_file(outfile, model_time_array, model_flux_array)
println("Done for now")
println("Preparing plots")

# Plot the observed flux and model

# Initialize the figure and axis
fig = Figure(size = (1200, 900))
ax = Axis(fig[1, 1], 
    title = "Model Flux for " * parameters["star_name"],
    xlabel = "Time (BJD) - " * time_zero_str,
    ylabel = "Flux"
)

# Plot the model and observed data

# Plot model and observed data
m_plot = lines!(ax, model_reduced_time_array, model_flux_array, label = "Model", color = :blue)
o_plot = scatter!(ax, observed_reduced_time_array, observed_flux_array, label = "Observed",color = :red, markersize = 6)

# Add a legend to the layout
axislegend(ax)

# Configure tooltips
# Define a custom tooltip formatter
#   'plot'     represents the object being hovered
#   'index'    the data point index,
#   'position' (x, y, z) coordinates of that point.
custom_tooltip(plot, index, position) = "Time: $(round(position[1], digits=4))\nFlux: $(round(position[2], digits=4))"

# Apply the custom tooltips only to the observed data points
o_plot.inspector_label = custom_tooltip

# Turn off inspection entirely on the model line to maximize performance
m_plot.inspectable = false

# Activate the inspector for the figure to have tooltips
inspector = DataInspector(fig)


# Display the GUI window and save the file
display(fig) 
save(parmfile_base * "_model_flux.png", fig)

# For code executed from the command line we need to pause
println("Return to continue ...")
readline()

exit()

  



