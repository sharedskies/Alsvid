#!/usr/local/bin/julia

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
#      Transit plot (plotly) of comparison and model fluxes at sampling times
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
#      Copyright 2021, 2025
#      
#      2021-06-29 Version 1.0d
#        Working with eccentricity = 0.0
#      2025-10-24 Version 1.1
#        Phase returned from solution of Kepler equation is now -pi to +pi
#        Working with eccentric orbits

 
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
# This program requires DelimitedFiles, Plots, and PlotlyBase

using DelimitedFiles  # For exporting formatted data files
using Plots           # For plotting results


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
      dictionary["planet_temperatue"] = parse(Float64,split(line,"=")[2])
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

    if occursin("orbit_lan_flag", line)
      if occursin("true", split(line,"=")[2])
        dictionary["orbit_lan_flag"] = true
      end
      if occursin("false", split(line,"=")[2])
        dictionary["orbit_lan_flag"] = false
      end
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


    # Test for model entries

    if occursin("transit_model_name", line)
      dictionary["transit_model_name"] = split(line,"=")[2]
    end

    if occursin("transit_model_t1", line)
      dictionary["transit_model_t1"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("transit_model_t2", line)
      dictionary["transit_model_t2"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("transit_model_tcp", line)
      dictionary["transit_model_tcp"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("transit_model_t3", line)
      dictionary["transit_model_t3"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("transit_model_t4", line)
      dictionary["transit_model_t4"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("transit_model_t5", line)
      dictionary["transit_model_t5"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("transit_model_t6", line)
      dictionary["transit_model_t6"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("transit_model_tcs", line)
      dictionary["transit_model_tcs"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("transit_model_t7", line)
      dictionary["transit_model_t7"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("transit_model_t8", line)
      dictionary["transit_model_t8"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("transit_model_dcp", line)
      dictionary["transit_model_dcp"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("transit_model_dcs", line)
      dictionary["transit_model_dcs"] = parse(Float64,split(line,"=")[2])
    end


    # Test for observed entries

    if occursin("transit_observed_name", line)
      dictionary["transit_observed_name"] = split(line,"=")[2]
    end

    if occursin("transit_observed_t1", line)
      dictionary["transit_observed_t1"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("transit_observed_t2", line)
      dictionary["transit_observed_t2"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("transit_observed_tcp", line)
      dictionary["transit_observed_tcp"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("transit_observed_t3", line)
      dictionary["transit_observed_t3"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("transit_observed_t4", line)
      dictionary["transit_observed_t4"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("transit_observed_t5", line)
      dictionary["transit_observed_t5"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("transit_observed_t6", line)
      dictionary["transit_observed_t6"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("transit_observed_tcs", line)
      dictionary["transit_observed_tcs"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("transit_observed_t7", line)
      dictionary["transit_observed_t7"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("transit_observed_t8", line)
      dictionary["transit_observed_t8"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("transit_observed_dcp", line)
      dictionary["transit_observed_dcp"] = parse(Float64,split(line,"=")[2])
    end

    if occursin("transit_observed_dcs", line)
      dictionary["transit_observed_dcs"] = parse(Float64,split(line,"=")[2])
    end
  end 
  return dictionary
end
    

# ###

# Model of uniform stellar flux for a transit

# Inputs

  # Star parameters
  # Planet parameters
  # Orbit parameters
  # Array of apparent separations (km)
  # Array of apparent orbital phases (2 pi)
  
# Output

  # Array of model fractional flux for a uniform stellar disk 
  #   transiting a uniform star at each time

function star_flux_uniform_model(parameters, apparent_separation_array, apparent_phase_array)

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
  
  # Scale the apparent separation array in km to the stellar radius
  
  z_array = apparent_separation_array ./ star_radius
  
  # Scale the planet radius to the stellar radius
  # Take the absolute value just in case a negative value is called (allowed by Exofast) 

  p  = abs(planet_radius/star_radius)
  p2 = p*p
          
  # Condition elements of z_array at the critical junctures
  
  z_array[ isapprox.(z_array, p, atol=1.0e-8) ] = p
  z_array[ isapprox.(z_array, p - 1.0), atol=1.0e-8 ] = p - 1.0
  z_array[ isapprox.(z_array, 1.0 - p), atol=1.0e-8 ] = 1.0 - p
  z_array[ isapprox.(z_array, 0.0), atol=1.0e-8 ] = 0.0
  
  # Helper arrays
  z2_array = z_array .* z_array
 
  # Mandel and Agol uniform source cases:
  # p = 0           z_array = [0,   inf)
  case_0a = isapprox(p, 0.0, atol=1.0e-8) && (z_array .>= 0.0)
  # p = (0, inf)    z_array = [1 + p, inf)
  case_0b = (p > 0.0) &&  (z_array .> (1.0 + p))
  # p = (0, inf)    z_array = (|1 - p|, 1 + p] 
  case_0c = (p > 0.0) &&  (z_array .> abs(1.0 - p)) &&  (z_array .<= (1.0 + p))
  # p = (0, inf)    z_array = [0, 1 - p]
  case_0d = (p > 0.0) &&  (z_array .>= 0.0) && (z_array .<= (1.0 - p))  
  # p = (0, inf)    z_array = [0, p - 1]
  case_0e = (p > 0.0) &&  (z_array .>= 0.0) && (z_array .<= (p - 1.0))  


  # Evaluate cases for a uniform source
  
  # Case 0a 
  # Star is unocculted
  # No action is needed since the arrays are zero by default

  # Case 0b
  # Planet is ingressing or egressing and partly on the disk
  kappa_0_array = acos( (p2 .- z2_array) ./ ( (2.0*p) .* z_array ) )
  kappa_1_array = acos( ( (1.0 - p2) .+ z2_array) ./ (2.0 .* z_array) )
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

# Model of limb darkened stellar flux for a transit

# Inputs

  # Star parameters
  # Planet parameters
  # Orbit parameters
  # Array of apparent separations (km)
  # Array of apparent orbital phases (2 pi)
  
# Output

  # Array of fractional fluxes for a planet 
  #   transiting a quadratically limb-darkened star at each time
  # Array of fractional fluxes for a planet 
  #   transiting a uniform star at each time


function star_flux_limb_darkened_model(parameters, apparent_separation_array, apparent_phase_array)


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

  # Remove the epoch and put phases on a 0 to 1 interval
  phase_remainder_array = mod.( apparent_phase_array, 1.0 )
  
  # Scale the unsigned apparent separation array in km to the stellar radius in km
  z_array = apparent_separation_array ./ star_radius

  # Save how many elements since it is used often
  nz = length(z_array)
  
  # Scale the planet radius to the stellar radius
  # Take the absolute value just in case a negative value is called (allowed by Exofast) 
  p  = abs(planet_radius / star_radius)
  p2 = p*p
  
  # Create arrays of p and p2 for broadcast comparisons with the z_array
  p_array = p .* ones(nz)
  p2_array = p2 .* ones(nz)
        
  # Condition elements of z_array at the critical junctures
  z_array[ isapprox.(z_array, p, atol=1.0e-8) ] .= p
  z_array[ isapprox.(z_array, p - 1.0, atol=1.0e-8) ] .= p - 1.0
  z_array[ isapprox.(z_array, 1.0 - p, atol=1.0e-8) ] .= 1.0 - p
  z_array[ isapprox.(z_array, 0.0, atol=1.0e-8) ] .= 0.0
  
  # These helper arrays require conditioning before broadcast use
  # Mandel and Agol and Exofast use a, b
  # Shporer in the Matlab version uses a, b, q, k0, and k1
  # Collins and Exofast use x1, x2 for similar quantities
         
  a_array = (z_array .- p) .* (z_array .- p)
  b_array = (z_array .+ p) .* (z_array .+ p)
  z2_array = (z_array) .* (z_array)
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
    
  # Initialize the arrays that determine the flux at each element of the z_array
  lambda_e_array = zeros(nz)
  lambda_d_array = zeros(nz)
  eta_d_array = zeros(nz)
  
  # Define and initialize the Theta (step) function of Mandel and Agol as an array
  theta_array = zeros(nz)
  theta_array[ (p .> z_array) ]  .= 1.0

  # Mandel and Agol (2002) cases
  # The eleven conditions from Mandel and Agol Table 1 
  #  select elements of the array to be redefined
  #  for a transit on a limb-darkened star

  # In Mandel and Agol the [ or ] means the value is allowed at the limit
  #   and the ( or ) means the value is not allowed at the limit
   
  # In Julia the Mandel and Agol uniform source cases are defined as 
  #   Boolean bit-arrays for z_array masking. 
    
  # No planet, no effect, flux defaults to star out of transit
  # p = 0           z_array = [0,   inf)
  # isapprox(p, 0.0, atol=1.0e-8)

  # Before ingress exclusive of contact
  # p = (0, inf)    z_array = (inf, -1 - p)
  # p > 0.0
  case_0a = (z_array .<= (-1.0 - p))  

  # After egress exclusive of contact
  # p = (0, inf)    z_array = (1 + p, inf)
  # p > 0.0
  case_0b = (z_array .> (1.0 + p))
    
  # Fully on disk exclusive of contacts
  # p = (0, inf)    z_array = (-1 + p, 1 - p)
  # p > 0.0
  case_0c = (z_array .> (-1.0 + p)) .&  (z_array .<  (1.0 - p))  

  # During  ingress inclusive of contacts
  # p = (0, inf)    z_array = [-1 - p, -1 + p]
  # p > 0.0
  case_0d = (z_array .>= (-1.0 - p)) .&  (z_array .<=  (-1.0 + p)) 
  
  # During egress inclusive of contacts (Why absolute value here?)
  # p = (0, inf)    z_array = [ 1 - p, 1 + p ]
  # p > 0.0
  case_0e = (z_array .>= abs(1.0 - p)) .&  (z_array .<= (1.0 + p))

  # Either ingress or egress
  case_0f = case_0d .| case_0e

  # Large planet covering smaller star 
  # p = (1, inf)    z_array = [1 - p, p - 1]
  # p > 1.0
  case_0g =  (z_array .>= 1.0 - p) .& (z_array .<= (p - 1.0)) 
    
  # Mandel and Agol case 1: There is no planet or the star is unocculted
  # p = 0           z_array = [0,   inf)
  # p = (0, inf)    z_array = [1 + p, inf)
  # isapprox(p, 0.0, atol=1.0e-8)
  case_1 = z_array .>= (1.0 + p)
    
  # Mandel and Agol case 2: Planet on limb of star
  # p = (0, inf)    z_array = (1/2 + |p - 1/2|, 1 + p) 
  # (p > 0.0)
  case_2 = (z_array .> 0.5 + abs(p - 0.5)) .& (z_array .< (1.0 + p))

  # Mandel and Agol case 3: Inside disk not over center
  # p = (0, 1/2)    z_array = (p, 1 - p)
  # (p > 0.0) && (p < 0.5)
  case_3 = (z_array .> p) .& (z_array .< (1.0 - p))
  
  # Mandel and Agol case 4: Inside disk not over center touching edge 
  # p = (0, 1/2)    z_array = 1 - p  
  # (p > 0.0) && (p < 0.5)
  case_4 = isapprox.(z_array, (1.0 - p), atol=1.0e-8)
    
  # Mandel and Agol case 5: Inside disk touching center
  # p = (0, 1/2)    z_array = p
  # (p > 0.0) && (p < 0.5)  
  case_5 = isapprox.(z_array, p, atol=1.0e-8)
  
  # Mandel and Agol case 6: Planet diameter is star's radius and edge of planet is on star's center
  # p = 1/2         z_array = 1/2
  # isapprox(p, 0.5, atol=1.0e-8)
  case_6 = isapprox.(z_array, 0.5, atol=1.0e-8)
    
  # Mandel and Agol case 7: Edge of planet's disk touches stellar center and planet not entirely inside star
  # p = (1/2, inf)  z_array = p
  # p > 0.5
  case_7 = isapprox.(z_array, p, atol=1.0e-8)
  
  # Mandel and Agol case 8: Planet covers center and limb
  # p = (1/2, inf)  z_array = [|1 - p|, p)
  # (p > 0.5)
  case_8 = (z_array .>= abs(1.0 - p)) .& (z_array .< p)
  
  # Mandel and Agol case 9: Planet inside stellar disk and covers center
  # p = (0, 1)      z_array = (0, 1/2 - |p - 1/2|)
  # (p > 0.0) && (p < 1.0)
  case_9 = (z_array .> 0.0) .& (z_array .< (0.5 - abs(p - 0.5)))
  
  # Mandel and Agol case 10: Planet concentric with star and entirely within stellar disk
  # p = (0, 1)      z_array = 0
  case_10 = (p > 0.0) && (p < 1.0) .& isapprox.(z_array, 0.0, atol=1.0e-8)

  # Mandel and Agol case 11: Planet completely eclipses the star
  # p = (1, inf)    z_array = [0, p - 1)
  # p > 1.0
  case_11 =  (z_array .>= 0.0) .& (z_array .< (p - 1.0))

  # Apply these cases to set flux parameter arrays for quadratic limb darkening
  # Corrections to Mandel and Agol from Exofast and AstroImageJ code are incorporated here

  # Evaluate contributions case by case

  # Case 0a 
  # Star is unocculted
  # No action is needed since the arrays are zero by default


  # Cases 0d, 0e, 0f
  # Planet is partly on the disk
  
  select = case_0d .| case_0e .| case_0f

  arg_array = zeros(nz)
  arg_array[select] .= ( -1.0 .+ p2 .+ z2_array[select]) ./ ( (2.0*p) .* z_array[select] )
  kappa_0_array = zeros(nz)
  kappa_0_array[select] .= acos.(arg_array[select])

  arg_array = zeros(nz)
  arg_array[select] .= ( 1.0 .- p2 .+ z2_array[select]) ./ ( 2.0 .* z_array[select] )  
  kappa_1_array = zeros(nz)
  kappa_1_array[select] .= acos.(arg_array[select])  

  arg_array = zeros(nz)
  arg_array[select] .= z2_array[select] .- 0.25 .* (1.0 .+ z2_array[select] .- p2) .* (1.0 .+ z2_array[select] .- p2)

  lambda_e_array  = zeros(nz)
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
  eta_5_array = zeros(nz)
  eta_5_array[select] .= 0.
  

  # Case 11
  # Planet completely eclipses the star

  select = case_11
  eta_4_array = zeros(nz)
  eta_4_array[select] .= 0.5 


  # Case 6
  # Planet diameter is star's radius and edge of planet is on star's center

  select = case_6
  eta_3_array = zeros(nz)
  eta_3_array[select] .= (3.0/32.0)


  # Cases 3, 4, 5, 9, 10
  # Planet inside the stellar disk

  select = case_3 .| case_4 .| case_5 .| case_9 .| case_10
  eta_2_array = zeros(nz)
  eta_2_array[select] .= (0.5*p2) .* (p2 .+ (2.0 .* z2_array[select]))
  

  # Cases 2, 7, 8
  # Planet covering the limb 

  select = case_2 .| case_7 .| case_8
  eta_2_array[select] .= (0.5*p2) .* (p2 .+ (2.0 .* z2_array[select]))

  arg_array = zeros(nz)
  arg_array[select] .= ( -1.0 .+ p2 .+ z2_array[select]) ./ ( (2.0*p) .* z_array[select] )
  kappa_0_array = zeros(nz)
  kappa_0_array[select] .= acos.(arg_array[select])

  arg_array = zeros(nz)
  arg_array[select] .= ( 1.0 .- p2 .+ z2_array[select]) ./ ( 2.0 .* z_array[select] )  
  kappa_1_array = zeros(nz)
  kappa_1_array[select] .= acos.(arg_array[select])  
   
  eta_1_array = zeros(nz)
  arg_1_array = zeros(nz)
  arg_2_array = zeros(nz)
  arg_3_array = zeros(nz)

  arg_1_array[select] .= kappa_1_array[select] .+ 2.0 .* eta_2_array[select] .* kappa_0_array[select]
  arg_2_array[select] .=  sqrt.( (1.0 .- a_array[select]) .* (b_array[select] .- 1.0) ) 
  arg_3_array[select] .= 0.25 .* (z2_array[select] .+ (5.0*p2 + 1.0)) .* arg_2_array[select]
  eta_1_array[select] .= (0.5/pi) .* (arg_1_array[select] .- arg_3_array[select])


  # Calculate the elliptic integrals for lambda_1

  k2_array = ones(nz)
  k2_array[select] .= (1.0 .- a_array[select]) ./ ( (4.0*p) .* z_array[select] )

  ellint1_array = zeros(nz)
  ellint2_array = zeros(nz)
  ellint3_array = zeros(nz)
  arg_1_array, arg_2_array = ellint( k2_array[select] )
  arg_3_array = ellint3(n_array[select], k2_array[select])
  ellint1_array[select] .= arg_1_array
  ellint2_array[select] .= arg_2_array  
  ellint3_array[select] .= arg_3_array


  # Case 2
  # Planet on the limb of the star
  
  select = case_2
  
  arg_1_array = zeros(nz)
  arg_1_array[select]  .= ( 1.0 .- b_array[select]) .* ( 2.0 .* b_array[select] .+ a_array[select] .- 3.0 )
  
  arg_1_array[select]  .=  arg_1_array[select] .- 3.0 .* q_array[select] .* (b_array[select] .- 2.0)
  arg_1_array[select]  .=  arg_1_array[select] .* ellint1_array[select]

  arg_2_array = zeros(nz)
  arg_2_array[select]  .= (4.0*p) .* z_array[select] .* (z2_array[select] .+ (7.0*p2 - 4.0) )
  arg_2_array[select]  .= arg_2_array[select] .* ellint2_array[select]  
  
  arg_3_array = zeros(nz)
  arg_3_array[select]  .=  -3.0 .* q_array[select] .* ellint3_array[select] ./ a_array[select] 
  
  arg_4_array = zeros(nz)    
  arg_4_array[select]  .= arg_1_array[select] .+ arg_2_array[select] .+ arg_3_array[select] 

  lambda_1_array = zeros(nz)
  lambda_1_array[select] .=  (1.0/(9.0*pi)) .* arg_4_array[select] ./ sqrt.(p .* z_array[select])
         

  # Cases 3, 9 
  # Inside the disk

  select = case_3 .| case_9

  k2_array = ones(nz)
  k2_array[select] .= (1.0 .- a_array[select]) ./ ( (4.0*p) .* z_array[select] )
  ellint1_array = zeros(nz)
  ellint2_array = zeros(nz)
  ellint3_array = zeros(nz)
  arg_1_array, arg_2_array = ellint(1.0 ./ k2_array[select])
  arg_3_array = ellint3(nb_array[select], (1.0 ./ k2_array[select]))  
  ellint1_array[select] .= arg_1_array
  ellint2_array[select] .= arg_2_array  
  ellint3_array[select] .= arg_3_array
    
  arg_1_array = zeros(nz)
  arg_1_array[select] .= (1.0 .- 5.0 .* z2_array[select] .+ p2) .+ q2_array[select]
  arg_1_array[select] .= arg_1_array[select] .* ellint1_array[select]

  arg_2_array = zeros(nz)
  arg_2_array[select] .= (1.0 .- a_array[select]) .* (z2_array[select] .+ 7.0*p2 .- 4.0) 
  arg_2_array[select] .= arg_2_array[select] .* ellint2_array[select]   

  arg_3_array = zeros(nz)
  arg_3_array[select] .= -3.0 .* q_array[select] ./ a_array[select] 
  arg_3_array[select] .= arg_3_array[select] .* ellint3_array[select]
  
  lambda_2_array = zeros(nz)
  lambda_2_array[select] .= arg_1_array[select] .+ arg_2_array[select]  .+ arg_3_array[select] 
  lambda_2_array[select] .= lambda_2_array[select]  ./ sqrt.(1.0 .- a_array[select]) 
  lambda_2_array[select] = (2.0/(9.0*pi)) .* lambda_2_array[select]  


  # Case 7
  # Edge of the planet's disk touches the stellar center

  select = case_7
   
  # Calculate the elliptic integrals for lambda_3 
  # Corrected typographical error in paper by  1/2k -> 1/2p  
  
  q_array = zeros(nz)
  q_array[select] .= (0.5/p) 
  ellint1_array, ellint2_array = ellint(q_array)
  
  arg_1_array = zeros(nz)
  arg_1_array[select] .= 1.0/3.0 .+ (2.0*p2 - 1.0)*16.0*p/(9.0*pi) .* ellint2_array[select]
  arg_2_array = zeros(nz)
  arg_2_array[select] .= ( (1.0 - 4.0*p2)*(3.0 - 8.0*p2)/(9.0*p*pi) ) .* ellint1_array[select]
  lambda_3_array = zeros(nz)
  lambda_3_array[select] .= arg_1_array[select] .- arg_2_array[select]


  # Case 5
  # Edge of the planet's disk touches the center of the stellar disk  
  
  select = case_5

  q_array_4 = (2.0*p) .* ones(nz)
  ellint1_array_4, ellint2_array_4 = ellint(q_array_4)
  
  lambda_4_array = zeros(nz)
  lambda_4_array_arg_1 =  4.0*(2.0*p2 - 1.0) .* ellint2_array_4
  lambda_4_array_arg_2 = (1.0 - 4.0*p2) .* ellint1_array_4 
  lambda_4_array_arg_3 = lambda_4_array_arg_1 .+ lambda_4_array_arg_2
  lambda_4_array[select] .= 1.0/3.0 .+ (2.0/(9.0*pi)) .* lambda_4_array_arg_3[select]


  # Case 4
  # The planet's disk is entirely inside the stellar disk

  select = case_4
  
  lambda_5_array_arg_1 = (2.0/(3.0*pi)) * acos((1.0 - 2.0*p))  .* ones(nz) 
  lambda_5_array_arg_2 = ((4.0/(9.0*pi))*(3.0 + 2.0*p - 8.0*p2)) .* ones(nz)
  lambda_5_array = zeros(nz)
  lambda_5_array[select] .= lambda_5_array_arg_1[select] .- lambda_5_array_arg_2[select]
    

  # Case 10
  # Planet is concentric with the disk of the star
  #   and at the precise bottom of the transit flux minimum

  select = case_10

  lambda_6_array_arg_1 = -((2.0/3.0)*(1.0 - p2)*sqrt(1.0 - p2)) .* ones(nz)
  lambda_6_array = zeros(nz)
  lambda_6_array[select] .= lambda_6_array_arg_1[select]
  
  
  # Calculate lambda_7
  # Case 6 
  # The planet's diameter equals the star's radius
  #   and the edge of the planet's disk touches both the stellar center and the limb of the star
  
  select = case_6
  
  lambda_7_array_arg_1 = (1.0/3.0 - 4.0/(9.0*pi)) .* ones(nz)
  lambda_7_array = zeros(nz)
  lambda_7_array[select] .= lambda_7_array_arg_1[select]

  
  # Case 11
  # The planet completely eclipses the star

  select = case_11

  lambda_8_array_arg_1 = ones(nz)
  lambda_8_array = zeros(nz)
  lambda_8_array[select] .= lambda_8_array_arg_1[select]
  
  lambda_8_array = zeros(nz)
  lambda_8_array[select] .= ones(nz)[select]


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

  # Star properties
  # Planet properties
  # Separation of planet from star
  # Phase at each separation  
  
# Output

  # Array of planet fluxes at each position


function planet_flux_model(parameters, apparent_separation_array, apparent_phase_array, planet_to_star_array)
  
  # This is a placeholder for the transit flux from the planet
  # It assumes zero Bond albedo and no thermal emission
  
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

function solve_kepler(mean_anom_array, orbit_ecc)
  maximum_iterations = 100
  tolerance = 1.0e-8

  mean_anom_array = rem2pi.(mean_anom_array, RoundNearest)
  last_array = mean_anom_array .+ orbit_ecc*sign.(sin.(mean_anom_array))
  
  # Iterative solution for all samples in the mean_anom_array
  for this_step in range(1, length=maximum_iterations)    
    solution_array = last_array .- orbit_ecc.*sin.(last_array) .- mean_anom_array
    derivative_array = 1.0 .- orbit_ecc.*cos.(last_array)    
    new_array = last_array .- solution_array./derivative_array
    
    # Test for convergence when all the array elements have converged
    test_array = isapprox.(new_array, last_array, atol=tolerance)    
    if all(test_array) 
      return new_array
    end
    
    # Not yet converged, so repeat again
    last_array = new_array
  end  
  println("The Kepler inversion did not converge.")
    
  return last_array
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
#     omg: omega, the argument of the periastron of the orbit (units of radians)
#     tpa: time of periastron (units of BJD)
#     lan_flag: Boolean to use the longitude of the ascending node
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
  #   omg is the argument of periastron of the star's orbit in radians
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
      
  # Karen: meananom = (2.0*PI*(1.0 + (bjd[i] - tp)/P)) % (2.0*PI)
  # mean_anom_array = np.mod( 2.0*np.pi*(1.0 + (time_array - orbit_tpa)/orbit_period), 2.0*np.pi)
  # np.mod is an alias for np.remainder

  # Fix local orbit parameters from the parameters dictionary

  orbit_tpa = parameters["orbit_tpa"]
  orbit_per = parameters["orbit_per"]
  orbit_ecc  = parameters["orbit_ecc"]
  orbit_omg = parameters["orbit_omg"]
  orbit_sax = parameters["orbit_sax"]
  orbit_inc = parameters["orbit_inc"]
  orbit_lan = parameters["orbit_lan"]
  orbit_lan_flag = parameters["orbit_lan_flag"]

  # Find the anomalies for the time series treating zero eccentricity as a special case
  mean_anom_array = 2.0.*pi.*mod.( (1.0 .+ (time_array .- orbit_tpa)./orbit_per), 1.0)

  # Put them in a -pi to +pi range
  mean_anom_array = rem2pi.(mean_anom_array, RoundNearest)

  if isapprox(orbit_ecc, 0.0, atol=1.0e-3)  
    true_anom_array = mean_anom_array    
  else
    ecc_anom_array = solve_kepler(mean_anom_array, orbit_ecc) 
    true_anom_array = 2.0 .* atan.(sqrt.((1.0 + orbit_ecc) ./ (1.0 - orbit_ecc)) .* atan.(0.5 .* ecc_anom_array))
  end
  
  # Find the position of the planet in its orbit in km
  planet_r_array = orbit_sax*(1.0 - orbit_ecc*orbit_ecc) ./ (1.0 .+ orbit_ecc .* cos.(true_anom_array))
  planet_x_array = -planet_r_array .* cos.(true_anom_array .+ orbit_omg)
  planet_y_array = -planet_r_array .* sin.(true_anom_array .+ orbit_omg) .* cos(orbit_inc)
  
  # Rotate by the longitude of the ascending node measured in the sky plane if known
  # This will be the orientation as seen by the observer
  #   observed_x is parallel to the line of apsides
  #   observed_y is perpendicular to x and positive to the north 
  #   observed phase is derived from the eccentric anomaly at each instance 
  
  if orbit_lan_flag
    observed_x_array = -planet_x_array.*cos(orbit_lan) .+ planet_y_array.*sin(orbit_lan)
    observed_y_array = -planet_x_array.*sin(orbit_lan) .- planet_y_array*cos(orbit_lan)
    observed_r_array = sqrt.(observed_x_array.*observed_x_array .+ observed_y_array.*observed_y_array)
  else
    observed_r_array = sqrt.(planet_x_array.*planet_x_array .+ planet_y_array.*planet_y_array)  
  end
      
  # Observed separations are given in (km)
  # Phases of the planetary positions are given in (2 pi)
  # Retain the full phase so that multiple epochs may be treated in one array
  observed_phase_array = 1.0 .+ (time_array .- orbit_tpa)./orbit_per
  
  return observed_r_array, observed_phase_array, planet_r_array

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

# Model of relative limb-darkened flux versus time for a star and planet system

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
#     omg: orbital omega, the argument of the periastron of the orbit (units of radians)
#       assumed to be PI/2 if e is 0.0
#       omega_* is typically quoted from RV where it is omega_planet + PI
#     tpa: time of periastron (units of BJD)
#     lan_flag: Boolean to use the longitude of the ascending node
#     lan: longitude of the ascending node (units of radians)
#       default value is pi

# Outputs

#   system_flux_array: np array with total flux at each time (units of stellar flux)
#   separation_array: separation of planet and star seen by the observer at each time (units of stellar sax)
#   phase_array: phase of the orbit at each time (units of 2 pi)

function transit_flux(parameters, time_array)
     
  # For times in the array find the apparent separation and transit phase
  apparent_separation_array, apparent_phase_array, planet_to_star_array  = planet_center(parameters, time_array)
  
  # Fractional flux with limb darkening and the undarkened flux as a benefit 
  star_flux_array, star_flux_uniform_array  = star_flux_limb_darkened_model(parameters, apparent_separation_array, apparent_phase_array)
          
  # Contribution to the flux from the planet itself
  planet_flux_array = planet_flux_model(parameters, apparent_separation_array, apparent_phase_array, planet_to_star_array)
  
  # Add star and planet
  system_flux_array = star_flux_array .+ planet_flux_array
              
  return system_flux_array, apparent_separation_array, apparent_phase_array

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

# The dictionaries are used to hold values for the models
# Each dictionary refers to a class of objects
# In this version there is only one member of each class
# Future versions may contain dictionaries for each named item or be replaced by database storage

# Scaling Units

solar_flux = 1.0
solar_mass = 1.0
solar_radius = 1.0
solar_temperature = 1.0
earth_mass = 1.0
earth_radius = 1.0
earth_temperature = 1.0
earth_orbit_sax = 1.0
earth_orbit_per = 1.0

# star:  stellar parameters
#   name: any text name
#   flux: (surface power/area solar units)
#   radius: (solar units)
#   mass: (solar units)
#   temperature: (solar units)
#   ld1: linear limb darkening
#   ld2: quadratic limb darkening

# planet: planet parameters
#   name: any text name
#   radius: (earth)
#   mass: (earth)
#   temperature: (earth)

# orbit:  system orbit parameters
#   name: should match the planet name for futureproof use
#   sax:  semi-major axis (units of host star radius)
#   per:  period (days)
#   inc:  inclination (units of radians)
#   ecc:  eccentricity defaults to 0
#   omg:  omega, the argument of the periastron of the orbit (units of radians)
#   tpa:  time of periastron (units of BJD)
#   lan_flag: flag to use the longitude of the ascending node if > 0
#   lan:  longitude of the ascending node (units of radians)
#     default value is pi

# transit_model: transit events for this model of star, planet, and orbit
#   name: should match the planet name for futureproof use
#   t1:  first contact for the ingress of the primary event
#   t2:  second contact for transit
#   tcp: center of transit for the primary (planet on star) event
#   t3:  third contact
#   t4:  fourth contact for the egress of the primary event
#   t5:  first contact for the secondary event
#   t6:  second contact for the secondary event
#   tcs: center of occulation for the secondary (star on planet) event
#   t7:  third contact for the secondary event
#   t8:  fourth contact for the egress of the secondary event
#   dcp: depth of the primary transit as a fraction of total separated star and planet flux 
#   dcs: depth of the secondary transit as a fraction of the total separated star and planet flux

# transit_observed: transit events observed for the flux being tested
#   name: should match the planet name for futureproof use
#   t1:  first contact for the ingress of the primary event
#   t2:  second contact for transit
#   tcp: center of transit for the primary (planet on star) event
#   t3:  third contact
#   t4:  fourth contact for the egress of the primary event
#   t5:  first contact for the secondary event
#   t6:  second contact for the secondary event
#   tcs: center of occulation for the secondary (star on planet) event
#   t7:  third contact for the secondary event
#   t8:  fourth contact for the egress of the secondary event
#   dcp: depth of the primary transit as a fraction of total separated star and planet flux 
#   dcs: depth of the secondary transit as a fraction of the total separated star and planet flux

# Create one dictionary as a database of any type for all the parameters
# Do not use it in  function call when the execution time is critical

parameters = Dict()

# Add defaults to the dictionary

star = Dict("star_name" => "TIC", "star_flux" => 1.0 , "star_radius" => 1.0, "star_mass" => 1.0, "star_temperature" => 1.0, "star_ld1" => 0.3, "star_ld2" => 0.3)

planet = Dict("planet_name" => "a", "planet_radius" => 0.1, "planet_mass" => 0.001, "planet_temperature" => 1000.0)

orbit = Dict("orbit_name"=> "a", "orbit_sax" =>100.0,  "orbit_per" =>10.0,  "orbit_inc" =>0.1,  "orbit_ecc" =>0.01,  "orbit_omg" =>0.5,  
  "orbit_tpa" =>2459000.0,  "orbit_lan_flag" => true, "orbit_lan" => 3.14159)

transit_model = Dict("transit_model_name"=> "a", "transit_model_t1" => 0.0, "transit_model_t2" => 0.0, 
  "transit_model_tcp" => 0.0, "transit_model_t3" => 0.0, "transit_model_t4" => 0.0, 
  "transit_model_t5" => 0.0, "transit_model_t6" => 0.0,  
  "transit_model_tcs" => 0.0, "transit_model_t7" => 0.0, "transit_model_t8" => 0.0, 
  "transit_model_dcp" => 0.0, "transit_model_dcs" => 0.0) 

transit_observed = Dict("transit_observed_name"=> "a", "transit_observed_t1" => 0.0, "transit_observed_t2" => 0.0, 
  "transit_observed_tcp" => 0.0, "transit_observed_t3" => 0.0, "transit_observed_t4" => 0.0, 
  "transit_observed_t5" => 0.0, "transit_observed_t6" => 0.0,  
  "transit_observed_tcs" => 0.0, "transit_observed_t7" => 0.0, "transit_observed_t8" => 0.0, 
  "transit_observed_dcp" => 0.0, "transit_observed_dcs" => 0.0) 

parameters = merge(parameters, star, planet, orbit, transit_model, transit_observed)

# Read the model parameters file and update the dictionary

println("Reading the parameter file ", parmfile)

parameters = read_parameter_file(parmfile, parameters)

# Read the observed or sampling flux array

println("Reading the observed flux array ", fluxfile)

time_array, observed_flux_array = read_data_file(fluxfile)  

# Run the model

model_system_flux_array, model_separation_array, model_phase_array = transit_flux(parameters, time_array)

# observed_transit_events = find_transit_events(parameters, time_array, 
#   model_system_flux_array, model_separation_array, model_phase_array) 

# Save the model flux

parmfile_base = split(parmfile, ".")[1]
outfile = parmfile_base*"_model_flux.dat"

time_zero = trunc(time_array[1])
reduced_time_array = time_array .- time_zero
time_zero_str = string(Int(time_zero))

write_data_file(outfile, reduced_time_array, model_system_flux_array)
println("Done for now")
println("Preparing plots")

# Plot the observed flux and model

# Set the backend
#gr()
plotly()

plot(reduced_time_array, model_system_flux_array, title = "Model Flux",
label = "Model")
plot!(reduced_time_array, observed_flux_array, label = "Observed")
xlabel!("Time (BJD) - "*time_zero_str)
ylabel!("Flux")
gui()
savefig(parmfile_base*"_model_flux.png")

exit()

  



