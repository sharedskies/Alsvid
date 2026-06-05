#!/usr/local/bin/python3

"""

  transit_model
  
    Lightcurve for a limb-darkened star and transiting planet
    
    Explicit inputs:
    
      Stellar parameters file with radius, temperature, and limb darkening 
      Planet parameters file with radius and temperature
      Orbit parameters file
      Transit file of sampling times and comparison fluxes
    
    Explicit outputs:
           
      Transit file of sampling times and model fluxes
      Transit plot (plotly) of comparison and model fluxes at sampling times
      
    Notes:

      Based AstroImageJ 2020-03-31 by Karen Collins
      Based on EXOFAST exofast_occultquad_cel (Eastman et al. 2018)
      Based on (Mandel and Agol 2002)
      
      John Kielkopf (kielkopf@louisville.edu)
      MIT License
      Copyright 2020
      
      Version 1.0 beta

"""

import os
import sys
import numpy as np
#import plotly.graph_objects as go
#from   plotly.offline import plot 
import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.use('GTK3Agg')


# Define global parameters and flags

verbose = False
diagnostics = False   


# ###

# Define the read_data_file function to read a named datafile and 
#   return x_data  and y_data np arrays
 
def read_data_file(infile):
  
  data_fp = open(infile, 'r')
  if not data_fp:
    print("The data file was not found.")
    exit(1)


  data_text = data_fp.readlines()
  data_fp.close()

  # How many lines were there?

  i = 0
  for line in data_text:
    i = i + 1

  nlines = i

  # Fill  the arrays for fixed size is much faster than appending on the fly

  x_data = np.zeros((nlines))
  y_data = np.zeros((nlines))

  # Parse the lines into the data

  i = 0
  for line in data_text:
    
    # Test for a comment line
    
    if ((line[0] == "#") or (line[0] == "!") ):

      continue
       
    # Treat the case of a plain text comma separated entries    
    
    try:
            
      entry = line.strip().split(",")  
      x_data[i] = float(entry[0])
      y_data[i] = float(entry[1])

      i = i + 1    
    except:      
    
      # Treat the case of space separated entries
    
      try:
        entry = line.strip().split()
        x_data[i] = float(entry[0])
        y_data[i] = float(entry[1])
        i = i + 1
      except:
        pass

  # Remove the unused trailing 0's if there were comments
  
  x_data = np.trim_zeros(x_data)
  y_data = np.trim_zeros(y_data)
  
  return (x_data, y_data)


# ###

# Define the read_parameter_file function to read a named parameter file and 
#   return the conditioned star, planet, and orbit parameters

def read_parameter_file(infile):

  star = star_class(flux=1.0, radius=1.0, temperature=5000.0, ld1=0.3, ld2=0.3, name="")
  planet = planet_class(radius=0.1, temperature=1000.0)
  orbit = orbit_class(sax=100.0, per=10.0, inc=0.1, ecc=0.01, omg = 0.5, 
    tpa=2459000.0, lan_flag=0, lan=3.14159 ) 
  
  parm_fp = open(infile,"r")
  if not parm_fp:
    print("The parameter file was not found.")
    exit(1)

  for newline in parm_fp:
    items = newline.split("=")

    if items[0].strip() == "star_name" :      
      star.name = str(items[1].strip())    
    if items[0].strip() == "star_flux" :      
      star.flux = float(str(items[1].strip()))
    if items[0].strip() == "star_radius" :      
      star.radius = float(str(items[1].strip()))
    if items[0].strip() == "star_temperature" :      
      star.temperature = float(str(items[1].strip()))
    if items[0].strip() == "star_ld1" :      
      star.ld1 = float(str(items[1].strip()))
    if items[0].strip() == "star_ld2" :      
      star.ld2 = float(str(items[1].strip()))
    if items[0].strip() == "planet_radius" :      
      planet.radius = float(str(items[1].strip()))
    if items[0].strip() == "planet_temperature" :      
      planet.temperature = float(str(items[1].strip()))
    if items[0].strip() == "orbit_sax" :      
      orbit.sax = float(str(items[1].strip()))
    if items[0].strip() == "orbit_per" :      
      orbit.per = float(str(items[1].strip()))
    if items[0].strip() == "orbit_inc" :      
      orbit.inc = float(str(items[1].strip()))
    if items[0].strip() == "orbit_ecc" :      
      orbit.ecc = float(str(items[1].strip()))           
    if items[0].strip() == "orbit_omg" :      
      orbit.omg = float(str(items[1].strip()))
    if items[0].strip() == "orbit_tpa" :      
      orbit.tpa = float(str(items[1].strip()))
    if items[0].strip() == "orbit_lan_flag" :      
      orbit.lan_flag = int(str(items[1].strip()))
    if items[0].strip() == "orbit_lan" :      
      orbit.lan = float(str(items[1].strip()))

  # Condition parameters as needed for subsequent processing
  
  if np.isclose(orbit.ecc, 0.0):
    orbit.lan = np.pi/2.0

  parm_fp.close()
  return star, planet, orbit



# ###

# Use physical units for the star, planet, and orbit
# The units should be the same for each class and
#   the code will apply a relative scale as needed

# Stellar parameters defined as a class
# For usage examples of variables as classes see
#   https://docs.python.org/3/tutorial/classes.html

class star_class:

 def __init__(self, flux, radius, temperature, ld1, ld2, name):
   self.name = name
   self.flux = flux
   self.radius = radius
   self.temperature = temperature
   self.ld1 = ld1
   self.ld2 = ld2


# ###

# Planet parameters defined as a class

class planet_class:

 def __init__(self, radius, temperature):
   self.radius = radius
   self.temperature = temperature


# ###

# Orbit parameters defined as a class

class orbit_class:

 def __init__(self, sax, per, inc, ecc, omg, tpa, lan_flag, lan):
   self.sax = sax 
   self.per = per
   self.inc = inc 
   self.ecc = ecc 
   self.omg = omg 
   self.tpa = tpa 
   self.lan_flag = lan_flag
   self.lan = lan


# ###

# Transit parameters defined as a class

class transit_class:

 def __init__(self, t1, t2, tcp, t3, t4, t5, t6, tcs, t7, t8, dcp, dcs):
   self.t1  = t1    
   self.t2  = t2  
   self.tcp = tcp 
   self.t3  = t3  
   self.t4  = t4  
   self.t5  = t5  
   self.t6  = t6  
   self.tcs = tcs 
   self.t7  = t7  
   self.t8  = t8  
   self.dcp = dcp 
   self.dcs = dcs 


 

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

def transit_flux(star, planet, orbit, time_array):
     
  # For times in the array find the apparent separation and transit phase
  apparent_separation_array, apparent_phase_array, planet_to_star_array  = planet_center(orbit, time_array)
  
  # Fractional flux with limb darkening and the undarkened flux as a benefit 
  star_flux_array, star_flux_uniform_array  = star_flux_limb_darkened_model(star, planet, orbit, apparent_separation_array, apparent_phase_array)
          
  # Contribution to the flux from the planet itself
  planet_flux_array = planet_flux_model(star, planet, orbit, apparent_separation_array, apparent_phase_array, planet_to_star_array)
  
  system_flux_array = np.add(star_flux_array,planet_flux_array)
              
  return system_flux_array, apparent_separation_array, apparent_phase_array


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

def star_flux_uniform_model(star, planet, orbit, apparent_separation_array, apparent_phase_array):

  # For transit modeling in this routine
  #   separations are in scaled to units of star.radius
  #   phases are reduced to 0.0 to 1.0 where
  #   0.0 to 1.0 covers a full orbit
  #   0.0 and 1.0 are equivalent
  #   0.0 to 0.5 are the centers of the secondary event
  #   0.5 to 1.0 are the centers of the primary event

  # Remove the epoch and put phases on a 0 to 1 interval
  phase_remainder_array = np.remainder( phase_array, 1.0 )


  # Mandel and Agol (2002) with corrections for logic
  # Claret (2000) for quadratic limb darkening
  # Collins (2018) for Java scalar version
  # Exofast2 occultquad_cel.pro (2018) for vector version
  
  # Scale the apparent separation array in km to the stellar radius
  z_array = apparent_separation_array/star.radius
  
  # Scale the planet radius to the stellar radius
  # Take the absolute value just in case a negative value is called (allowed by Exofast) 
  p  = np.abs(planet.radius/star.radius)
  p2 = p*p
          
  # Condition elements of z_array at the critical junctures
  z_array[ np.isclose(z_array, p) ] = p
  z_array[ np.isclose(z_array, p - 1.0) ] = p - 1.0
  z_array[ np.isclose(z_array, 1.0 - p) ] = 1.0 - p
  z_array[ np.isclose(z_array, 0.0) ] = 0.0
  
  # Helper arrays
  z2_array = np.multiply(z_array, z_array)
  
  # Identify the stellar flux
  flux_star = star.flux

  # Mandel and Agol uniform source cases:
  # p = 0           z_array = [0,   inf)
  case_0a = np.isclose(p, 0.0) & (z_array >= 0.0)
  # p = (0, inf)    z_array = [1 + p, inf)
  case_0b = (p > 0.0) &  (z_array > (1.0 + p))
  # p = (0, inf)    z_array = (|1 - p|, 1 + p] 
  case_0c = (p > 0.0) &  (z_array > np.abs(1.0 - p)) &  (z_array <= (1.0 + p))
  # p = (0, inf)    z_array = [0, 1 - p]
  case_0d = (p > 0.0) &  (z_array >= 0.0) & (z_array <= (1.0 - p))  
  # p = (0, inf)    z_array = [0, p - 1]
  case_0e = (p > 0.0) &  (z_array >= 0.0) & (z_array <= (p - 1.0))  


  # Evaluate cases for a uniform source
  
  # Case 0a 
  # Star is unocculted
  # No action is needed since the arrays are zero by default

  # Case 0b
  # Planet is ingressing or egressing and partly on the disk
  kappa_0_array = np.arccos(np.divide( (p2 - z2_array), (2.0*p*z_array) ))
  kappa_1_array = np.arccos(np.divide( (1.0 - p2 + z2_array), (2.0*z_array) ))
  lambda_0_array = p2*kappa_0_array + kappa_1_array - np.sqrt(z2_array - 0.25*(1.0 + z2_array - p2)*(1.0 + z2_array - p2))
  lambda_0_array = lambda_0_array/np.pi
  lambda_e_array[np.where(case_0b)] = np.copy(lambda_0_array)

  # Case 0c
  # Planet is fully on the disk 
  lambda_e_array[np.where(case_0c)] = p2
  
  # Case 0d
  # Planet covers the star completely
  lambda_e_array[np.where(case_0d)] = 1.0

  star_flux_uniform_array = (1.0 - lambda_e_array)*flux_star
  

  return star_flux_uniform_array


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
  


def star_flux_limb_darkened_model(star, planet, orbit, apparent_separation_array, apparent_phase_array):

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

  # Remove the epoch and put phases on a 0 to 1 interval
  phase_remainder_array = np.remainder( apparent_phase_array, 1.0 )


  # Mandel and Agol (2002) with corrections for logic
  # Claret (2000) for quadratic limb darkening
  # Collins (2018) for Java scalar version
  # Exofast2 occultquad_cel.pro (2018) for vector version
  
  # Scale the unsigned apparent separation array in km to the stellar radius
  z_array = apparent_separation_array/star.radius
  
  # Scale the planet radius to the stellar radius
  # Take the absolute value just in case a negative value is called (allowed by Exofast) 
  p  = np.abs(planet.radius/star.radius)
  
  #p = 0.1
  #print("Testing with Jupiter!! p=",p, "\n")
  
  p2 = p*p
          
  # Condition elements of z_array at the critical junctures
  z_array[ np.isclose(z_array, p) ] = p
  z_array[ np.isclose(z_array, p - 1.0) ] = p - 1.0
  z_array[ np.isclose(z_array, 1.0 - p) ] = 1.0 - p
  z_array[ np.isclose(z_array, 0.0) ] = 0.0
  
  # Helper arrays
  # Mandel and Agol and Exofast use a, b
  # Shporer in the Matlab version uses a, b, q, k0, and k1
  # Collins and Exofast use x1, x2 for similar quantities
      
  a_array = np.multiply(z_array - p, z_array - p)
  b_array = np.multiply(z_array + p, z_array + p)
  z2_array = np.multiply(z_array, z_array)
  q_array = p2 - z2_array
  q2_array = np.multiply(q_array, q_array)
  n_array = 1.0 - np.divide(1.0, a_array)
  nb_array = 1.0 - np.divide(b_array, a_array)
  k_array = np.sqrt(np.divide(1.0 - a_array, 4.0*p*z_array)) 
  k2_array = np.multiply(k_array, k_array)
  k2_inverse_array = np.divide(1.0, k2_array)
  kappa_0_array = np.arccos(np.divide( -1.0 + p2 + z2_array ,  2.0*p*z_array ))
  kappa_1_array = np.arccos(np.divide( 1.0 - p2 + z2_array ,  2.0*z_array ))  
  
  # Identify the stellar flux
  flux_star = star.flux
  
  # Identify the Claret quadratic limb darkening coefficients with Mandel and Agol notation
  gamma1 = star.ld1
  gamma2 = star.ld2

  # Compute the Mandel and Agol limb darkening terms
  c1 = 0.0
  c2 = gamma1 + 2.0*gamma2
  c3 = 0.0
  c4 = -gamma2
  c0 = 1.0 - c1 - c2 - c3 - c4

  
  # Evaluate the Mandel and Agol normalization factor (their 1.0/(4.0*Omega) )
  omega =  c0/4.0 + c1/5.0 + c2/6.0 + c3/7.0 + c4/8.0
  
  # Find the normalizing factor for the transit terms in the transit model
  flux_norm_ld = 1.0/(4.0*omega)
    
  # Initialize the arrays that determine the flux at each element of the z_array
  lambda_e_array = np.zeros(z_array.size)
  lambda_d_array = np.zeros(z_array.size)
  eta_d_array = np.zeros(z_array.size)
  
  # Define and initialize the Theta (step) function of Mandel and Agol as an array
  theta_array = np.zeros(z_array.size)
  theta_array[ np.where(p > z_array) ]  = 1.0

  # Mandel and Agol (2002) cases
  # The eleven conditions from Mandel and Agol Table 1 
  #  select elements of the array to be redefined
  #  for a transit on a limb-darkened star

  # In Mandel and Agol the [ or ] means the value is allowed at the limit
  #   and the ( or ) means the value is not allowed at the limit
  
  # The numpy arrays case_## are of the size of z_array and a sequence of
  #   true/false values indicating whether that z_array or time_array element
  #   is to be included.  It may be broadcast onto a numpy array
  #   using [np.where(case)] 
 
  # Mandel and Agol uniform source cases:
  
  # No planet no effect
  # p = 0           z_array = [0,   inf)
  case_0a = np.isclose(p, 0.0)

  # Before ingress exclusive of contact
  # p = (0, inf)    z_array = (inf, -1 - p)
  case_0a = (p > 0.0) &  (z_array <= (-1.0 - p))  

  # After egress exclusive of contact
  # p = (0, inf)    z_array = (1 + p, inf)
  case_0b = (p > 0.0) &  (z_array > (1.0 + p))
  
  # Fully on disk exclusive of contacts
  # p = (0, inf)    z_array = (-1 + p, 1 - p)
  case_0c = (p > 0.0) &  (z_array > (-1 + p)) &  (z_array <  (1.0 - p))  

  # During  ingress inclusive of contacts
  # p = (0, inf)    z_array = [-1 - p, -1 + p]
  case_0d = (p > 0.0) &  (z_array >= (-1.0 - p)) &  (z_array <=  (-1.0 + p)) 
  
  # During egress inclusive of contacts (Why absolute value here?)
  # p = (0, inf)    z_array = [ 1 - p, 1 + p ]
  case_0e = (p > 0.0) &  (z_array >= np.abs(1.0 - p)) &  (z_array <= (1.0 + p))

  # Either ingress or egress
  case_0f = case_0d | case_0e

  # Large planet covering smaller star 
  # p = (1, inf)    z_array = [1 - p, p - 1]
  case_0g =  (p > 1.0) & (z_array >= 1.0 - p) & (z_array <= (p - 1.0)) 
    
  # Mandel and Agol case 1: There is no planet or the star is unocculted
  # p = 0           z_array = [0,   inf)
  # p = (0, inf)    z_array = [1 + p, inf)  
  case_1 = np.isclose(p, 0.0) | ((p > 0.0) & (z_array >= (1.0 + p)))
    
  # Mandel and Agol case 2: Planet on limb of star
  # p = (0, inf)    z_array = (1/2 + |p - 1/2|, 1 + p)  
  case_2 = (p > 0.0) &  (z_array > 0.5 + np.abs(p - 0.5)) & (z_array < (1.0 + p))

  # Mandel and Agol case 3: Inside disk not over center
  # p = (0, 1/2)    z_array = (p, 1 - p) 
  case_3 = (p > 0.0) & (p < 0.5) & (z_array > p) & (z_array < (1.0 - p))
  
  # Mandel and Agol case 4: Inside disk not over center
  # p = (0, 1/2)    z_array = 1 - p  
  case_4 = (p > 0.0) & (p < 0.5) & np.isclose(z_array, (1.0 - p))
    
  # Mandel and Agol case 5: Inside disk touching center
  # p = (0, 1/2)    z_array = p
  case_5 = (p > 0.0) & (p < 0.5) & np.isclose(z_array, p)
  
  # Mandel and Agol case 6: Planet diameter is star's radius and edge of planet on star's senter
  # p = 1/2         z_array = 1/2
  case_6 = np.isclose(p, 0.5) & np.isclose(z_array, 0.5)
    
  # Mandel and Agol case 7: Edge of planet's disk touches stellar center and planet not entirely inside star
  # p = (1/2, inf)  z_array = p
  case_7 = (p > 0.5) & np.isclose(z_array, p)
  
  # Mandel and Agol case 8: Planet covers center and limb
  # p = (1/2, inf)  z_array = [|1 - p|, p)
  case_8 = (p > 0.5) & (z_array >= np.abs(1.0 - p)) & (z_array < p)
  
  # Mandel and Agol case 9: Planet inside stellar disk and covers center
  # p = (0, 1)      z_array = (0, 1/2 - |p - 1/2|)
  case_9 = (p > 0.0) & (p < 1.0) & (z_array > 0.0) & (z_array < (0.5 - np.abs(p - 0.5)))
  
  # Mandel and Agol case 10: Planet concentric with star and entirely within stellar disk
  # p = (0, 1)      z_array = 0
  case_10 = (p > 0.0) & (p < 1.0) & np.isclose(z_array, 0.0)

  # Mandel and Agol case 11: Planet completely eclipses the star
  # p = (1, inf)    z_array = [0, p - 1)  
  case_11 = (p > 1.0) & (z_array >= 0.0) & (z_array < (p - 1.0))

  # Apply these cases to set flux parameter arrays for quadratic limb darkening
  # Note corrections to Mandel and Agol from Exofast and AstroImageJ code are incorporated here

  # Evaluate cases for a uniform source
  
  # Case 0a 
  # Star is unocculted
  # No action is needed since the arrays are zero by default

  # Cases 0d, 0e, 0f
  # Planet is ingressing or egressing and partly on the disk

  lambda_0_array_arg_1 = np.multiply((1.0 + z2_array - p2), (1.0 + z2_array - p2))
  lambda_0_array_arg_2 = np.subtract(z2_array, 0.25*lambda_0_array_arg_1)
  lambda_0_array_arg_3 =  np.subtract(kappa_1_array, np.sqrt(lambda_0_array_arg_2))
  lambda_0_array = np.add(p2*kappa_0_array, lambda_0_array_arg_3)
  lambda_0_array = lambda_0_array/np.pi
  
  # Assign values without limb darkening in the ingress and egress regions and set to zero otherwse
  lambda_e_array[np.where(case_0f)] = np.copy(lambda_0_array[np.where(case_0f)])

  # Case 0c
  # Planet is fully on the disk 
  
  # Assign values where the transit is ongoing without limbdarkening
  lambda_e_array[np.where(case_0c)] = p2
  
  # Case 0g
  # Planet covers the star completely
  lambda_e_array[np.where(case_0g)] = 1.0
   

  # Calculate eta_5
  # For case 1
  eta_5_array = np.zeros(z_array.size)
  
  # Calculate eta_4
  # For case 11
  # Corrected typographical error in paper per Karen Collins in AIJ source
  eta_4_array = 0.5*np.ones(z_array.size)

  # Calculate eta_3
  # For case 6
  eta_3_array = (3.0/32.0)*np.ones(z_array.size)

  # Calculate eta_2
  # For cases 3, 4, 5, 9, 10
  eta_2_array = 0.5*p2*(p2 + 2.0*z2_array)
  
  # Calculate eta_1
  # For cases 2, 7, 8 
  eta_1_array_arg_1 = np.add(kappa_1_array, 2.0*np.multiply(eta_2_array, kappa_0_array))
  eta_1_array_arg_2 = np.multiply((1.0 - a_array), (b_array - 1.0))
  eta_1_array_arg_3 = np.sqrt(eta_1_array_arg_2)
  eta_1_array_arg_4 = 0.25*np.multiply((1.0 + 5.0*p2 + z2_array), eta_1_array_arg_3)
  eta_1_array_arg_5 =  np.subtract(eta_1_array_arg_1, eta_1_array_arg_4)
  eta_1_array = (1./(2.0*np.pi))*eta_1_array_arg_5
     
  # Calculate the elliptic integrals for lambda_1
  ellint1_array_1, ellint2_array_1 = ellint( k2_array )
  ellint3_array_1 = ellint3(n_array, k2_array)
  
   
  # Calculate lambda_1
  # For case 2  the planet disk lies on the limb of the star but does not cover the center of the stellar disk
  
  # Matlab version works 
  # lam = 1/9/pi./sqrt(rr*z) .* ( ((1-b).*(2*b+a-3)-3*q.*(b-2)).*ellipticK(k.^2) + 4*rr*z.*(z.^2+7*rr^2-4).*ellipticE(k.^2)-3*q./a.*ellipticPi((a-1)./a,k.^2) );

  lambda_1_array_arg_1 = np.multiply( 1.0 - b_array, np.add( 2.0 * b_array, a_array - 3.0 ) )  
  lambda_1_array_arg_2 = -3.0*np.multiply(q_array, b_array - 2.0)  
  lambda_1_array_arg_3 = np.add(lambda_1_array_arg_1, lambda_1_array_arg_2)
  lambda_1_array_arg_4 = np.multiply(lambda_1_array_arg_3, ellint1_array_1)
  
  lambda_1_array_arg_5 = np.multiply( 4.0*p*z_array, z2_array + 7.0*p2 - 4.0 )
  lambda_1_array_arg_6 = np.multiply( lambda_1_array_arg_5, ellint2_array_1 )
  
  lambda_1_array_arg_7 = -3.0*np.divide( q_array, a_array )
  lambda_1_array_arg_8 = np.multiply( lambda_1_array_arg_7, ellint3_array_1 )
    
  lambda_1_array_arg_9 = np.add( lambda_1_array_arg_4, lambda_1_array_arg_6)
  lambda_1_array_arg_10 = np.add(lambda_1_array_arg_9, lambda_1_array_arg_8)
  lambda_1_array_arg_11 = (1.0/(9.0*np.pi))*np.divide( 1.0, np.sqrt(p*z_array) )
  lambda_1_array = np.multiply( lambda_1_array_arg_11, lambda_1_array_arg_10) 
  #print(lambda_1_array)
  #print(z_array)
  #print(z_array[63], lambda_1_array[63])
  #myk, mye =ellint( k2_array )
  #mypi =ellint3(n_array, k2_array)
  #print(k2_array[63], myk[63], mye[63])
  #print(n_array[63], k2_array[63],mypi[63])
  #print(lambda_1_array_arg_4[63])
  #print(lambda_1_array_arg_6[63])
  #print(lambda_1_array_arg_8[63])
  #print(lambda_1_array_arg_11[63])
  #print(lambda_1_array[63])
  #print(lambda_1_array)

  # Calculate the elliptic integrals for lambda_2
  ellint1_array_2, ellint2_array_2 = ellint(k2_inverse_array)
  ellint3_array_2 = ellint3(nb_array, k2_inverse_array)
      
  # Calculate lambda_2
  # For case 3, 9 where the transiting planet is fully on the stellar disk

  #  ;; Case 3, Case 9 - anywhere in between
  #  ;; lambda_2
  #  x1=(p-z)^2 our a
  #  x2=(p+z)^2 our b
  #  x3=p^2-z^2
  #  q=sqrt((x2[ndxuse]-x1[ndxuse])/(1.d0-x1[ndxuse]))
  #  n=x2[ndxuse]/x1[ndxuse]-1.d0
  #  ellke, q, Ek, Kk

  #  lambdad[ndxuse] = 2.d0/9.d0/!dpi/sqrt(1.d0-x1[ndxuse])*$
  #    ((1.d0-5.d0*z[ndxuse]^2+p^2+x3[ndxuse]^2)*Kk+(1.d0-x1[ndxuse])*$
  #     (z[ndxuse]^2+7.d0*p^2-4.d0)*Ek-3.d0*x3[ndxuse]/x1[ndxuse]*$
  #     ellpic_bulirsch(n,q))
  
  # Matlab version
  # lam = 2/9/pi./sqrt(1-a) .* ( (1-5*z.^2+rr^2+q.^2).*ellipticK(1./k.^2) + (1-a).*(z.^2+7*rr^2-4).*ellipticE(1./k.^2)-3.*q./a.*ellipticPi((a-b)./a,1./k.^2) );


  #  First kind is K
  #  Second kind is E

    
  lambda_2_array_arg_1 = np.add(1.0 - 5.0*z2_array + p2, q2_array)
  lambda_2_array_arg_2 = np.multiply(lambda_2_array_arg_1 , ellint1_array_2)
  
  lambda_2_array_arg_3 = np.multiply( (1.0 - a_array), (z2_array + 7.0*p2 - 4.0) )
  lambda_2_array_arg_4 = np.multiply( lambda_2_array_arg_3, ellint2_array_2 )  

  lambda_2_array_arg_5 = -3.0*np.divide( q_array , a_array )
  lambda_2_array_arg_6 = np.multiply( lambda_2_array_arg_5, ellint3_array_2 )
      
  lambda_2_array_arg_7 = np.add(lambda_2_array_arg_2, lambda_2_array_arg_4)  
  lambda_2_array_arg_8 = np.add(lambda_2_array_arg_6, lambda_2_array_arg_7)
  lambda_2_array_arg_9 = np.divide( lambda_2_array_arg_8, np.sqrt(1.0 - a_array) )
  
  lambda_2_array = (2.0/(9.0*np.pi))*lambda_2_array_arg_9 

  #print(lambda_2_array)
  #print(z_array)
  #print(z_array[73], lambda_2_array[73])
  #myk, mye =ellint( k2_inverse_array )
  #mypi =ellint3(nb_array, k2_inverse_array)
  #print(k2_inverse_array[73], myk[73], mye[73])
  #print(nb_array[73], k2_inverse_array[73],mypi[73])
  #print(lambda_2_array_arg_2[73])
  #print(lambda_2_array_arg_4[73])
  #print(lambda_2_array_arg_6[73])
  #print(lambda_2_array_arg_9[73])
  #print(lambda_2_array[73])
  #print(lambda_2_array)

 
  # Calculate the elliptic integrals for lambda_3 
  # Corrected typographical error in paper by  1/2k -> 1/2p  
  q_array_3 = (0.5/p)*np.ones(z_array.size) 
  ellint1_array_3, ellint2_array_3 = ellint(q_array_3)

  # Calculate lambda_3
  # For case 7 where the edge of the planet's disk touches the stellar center
  # Note in Mandel and Agol K is elliptical integral of the first kind, here ellint1
  # E is the elliptic integral of the second kind, here ellint2
  lambda_3_array_arg_1 = 1.0/3.0 + (16.0*p/(9.0*np.pi))*(2.0*p2 - 1.0)*ellint2_array_3
  lambda_3_array_arg_2 = (1.0/(9.0*p*np.pi))*(1.0 - 4.0*p2)*(3.0 - 8*p2)*ellint1_array_3
  lambda_3_array = np.subtract(lambda_3_array_arg_1, lambda_3_array_arg_2)

  # Calculate the elliptic integrals for lambda_4
  # Corrected typographical error in Mandel and Agol by 2k -> 2p
  q_array_4 = 2.0*p*np.ones(z_array.size)
  ellint1_array_4, ellint2_array_4 = ellint(q_array_4)

  # Calculate lambda_4
  # For case 5 where the edge of the planet touches the center of the stellar disk
  lambda_4_array_arg_1 =  4.0*(2.0*p2 - 1.0)*ellint2_array_4
  lambda_4_array_arg_2 = (1.0 - 4.0*p2)*ellint1_array_4 
  lambda_4_array_arg_3 = np.add(lambda_4_array_arg_1, lambda_4_array_arg_2)
  lambda_4_array = 1.0/3.0 + (2.0/(9.0*np.pi))*lambda_4_array_arg_3

  # Calculate lambda_5
  # For case 4 where the planet's disk is entirely inside the stellar disk
  lambda_5_array_arg_1 = (2.0/(3.0*np.pi))*np.arccos((1.0 - 2.0*p))*np.ones(z_array.size) 
  lambda_5_array_arg_2 = (4.0/(9.0*np.pi))*(3.0 + 2.0*p - 8.0*p2)*np.ones(z_array.size)
  lambda_5_array = np.subtract(lambda_5_array_arg_1, lambda_5_array_arg_2)
    
  # Calculate lambda_6
  # For case 10 where planet is concentric with the disk of the star
  #   and at the precise bottom of the transit flux minimum
  lambda_6_array = -(2.0/3.0)*(1.0 - p2)*np.sqrt(1.0 - p2)*np.ones(z_array.size)

  # Calculate lambda_7
  # For case 6 where the planet's diameter equals the star's radius
  #   and the edge of the planet's disk touches both the stellar center and the limb of the star
  lambda_7_array = (1.0/3.0 - 4.0/(9.0*np.pi))*np.ones(z_array.size)

  # Calculate lambda_8
  # For case 11 where the planet completely eclipses the star
  lambda_8_array = np.ones(z_array.size)


  # Evaluate the cases using these lambda and eta values

  # Case 1
  # Star is unocculted
  # No action is needed since the arrays are zero by default
     
  # Case 2
  # Planet disk on limb of star but not on center of disk
  # Light curve is steepest here 
  lambda_d_array[np.where(case_2)] = np.copy(lambda_1_array[np.where(case_2)])  
  eta_d_array[np.where(case_2)] = np.copy(eta_1_array[np.where(case_2)])  

  # Case 3
  # Planet disk inside stellar disk
  lambda_d_array[np.where(case_3)] = np.copy(lambda_2_array[np.where(case_3)])  
  eta_d_array[np.where(case_3)] = np.copy(eta_2_array[np.where(case_3)])

  # Case 4
  # Planet disk inside stellar disk touching edge of disk
  lambda_d_array[np.where(case_4)] = np.copy(lambda_5_array[np.where(case_4)])  
  eta_d_array[np.where(case_4)] = np.copy(eta_2_array[np.where(case_4)])
 
  # Case 5
  # Planet disk inside stellar disk and touches center
  lambda_d_array[np.where(case_5)] = np.copy(lambda_4_array[np.where(case_5)])  
  eta_d_array[np.where(case_5)] = np.copy(eta_2_array[np.where(case_5)])
 
  # Case 6
  # Planet diameter equals the stellar radius and it touches both the stellar center and limb
  lambda_d_array[np.where(case_6)] = np.copy(lambda_7_array[np.where(case_6)])  
  eta_d_array[np.where(case_6)] = np.copy(eta_3_array[np.where(case_6)])
  
  # Case 7
  # Planet edge touches the stellar center, but the planet extends beyond the stellar disk
  lambda_d_array[np.where(case_7)] = np.copy(lambda_3_array[np.where(case_7)])  
  eta_d_array[np.where(case_7)] = np.copy(eta_1_array[np.where(case_7)])

  # Case 8
  # Planet over the center and the limb of the stellar disk
  lambda_d_array[np.where(case_8)] = np.copy(lambda_1_array[np.where(case_8)])  
  eta_d_array[np.where(case_8)] = np.copy(eta_1_array[np.where(case_8)])
  
  # Case 9
  # Planet entirely inside the stellar disk and over the stellar center
  lambda_d_array[np.where(case_9)] = np.copy(lambda_2_array[np.where(case_9)])  
  eta_d_array[np.where(case_9)] = np.copy(eta_2_array[np.where(case_9)])
  
  # Case 10
  # Planet is concentric with the disk of the star precisely at Tc
  lambda_d_array[np.where(case_10)] = np.copy(lambda_6_array[np.where(case_10)])  
  eta_d_array[np.where(case_10)] = np.copy(eta_2_array[np.where(case_10)])
  
  # Case 11
  # Planet completely eclipses the star
  lambda_d_array[np.where(case_11)] = np.copy(lambda_8_array[np.where(case_11)])  
  eta_d_array[np.where(case_11)] = np.copy(eta_4_array[np.where(case_11)])
     
  # Evaluate the flux array
  
  # Mandel and Agol quadratic limb darkening in Section 4
  # F = 1 - (4\Omega}^{-1} \times ( (1 - c_2)\lambda_e + c_2( \lambda_d + (2/3)\Theta(p-z) ) - c_4\eta_d )
  #  where c2 = ld1 + 2 ld_2 and c4 = - ld2
      
  star_flux_limb_darkened_array_arg_1 = (1.0 - c2)*lambda_e_array 
  star_flux_limb_darkened_array_arg_2 = c2*np.add(lambda_d_array, (2.0/3.0)*theta_array)
  star_flux_limb_darkened_array_arg_3 = -c4*eta_d_array
  star_flux_limb_darkened_array_arg_4 = np.add(star_flux_limb_darkened_array_arg_1, star_flux_limb_darkened_array_arg_2)
  star_flux_limb_darkened_array_arg_5 = np.add(star_flux_limb_darkened_array_arg_4, star_flux_limb_darkened_array_arg_3)
  star_flux_limb_darkened_array_arg_6 = flux_norm_ld*star_flux_limb_darkened_array_arg_5
  
  star_flux_limb_darkened_array = flux_star*(1.0 - star_flux_limb_darkened_array_arg_6)  
  star_flux_uniform_array = flux_star*(1.0 - lambda_e_array)


  return star_flux_limb_darkened_array, star_flux_uniform_array
  
  
# ###

# Planet flux model

# Inputs

  # Star properties
  # Planet properties
  # Separation of planet from star
  # Phase at each separation  
  
# Output

  # Array of planet fluxes at each position


def planet_flux_model(star, planet, orbit, apparent_separation_array, apparent_phase_array, planet_to_star_array):
  
  # This is a placeholder for the transit flux from the planet
  # It assumes zero Bond albedo and no thermal emission
  
  planet_flux_array = np.zeros(apparent_separation_array.size)
  
  return planet_flux_array
  

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
 

def planet_center(orbit, time_array):
   
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
  
  # Find the anomalies for the time series treating zero eccentricity as a special case
  mean_anom_array = 2.0*np.pi*np.remainder( (1.0 + (time_array - orbit.tpa)/orbit.per), 1.0)
  if np.isclose(orbit.ecc, 0):  
    true_anom_array = mean_anom_array
  else:
    ecc_anom_array = solve_kepler(mean_anom_array, orbit.ecc)
    true_anom_array = 2.0*np.arctan(np.sqrt((1.0 + orbit.ecc)/(1.0 - orbit.ecc))*np.arctan(0.5*ecc_anom_array))
  
  # Find the position of the planet in its orbit in km
  planet_r_array = orbit.sax*(1.0 - orbit.ecc*orbit.ecc)/(1.0 + orbit.ecc*np.cos(true_anom_array))
  planet_x_array = -planet_r_array*np.cos(true_anom_array + orbit.omg)
  planet_y_array = -planet_r_array*np.sin(true_anom_array + orbit.omg)*np.cos(orbit.inc)
  
  # Rotate by the longitude of the ascending node measured in the sky plane if known
  # This will be the orientation as seen by the observer
  #   observed_x is parallel to the line of apsides
  #   observed_y is perpendicular to x and positive to the north 
  #   observed phase is derived from the eccentric anomaly at each instance 
  
  if orbit.lan_flag:
    observed_x_array = -planet_x_array*np.cos(orbit.lan) + planet_y_array*np.sin(orbit.lan)
    observed_y_array = -planet_x_array*np.sin(orbit.lan) - planet_y_array*np.cos(orbit.lan)
    observed_r_array = np.sqrt(observed_x_array*observed_x_array + observed_y_array*observed_y_array)
  else:
    observed_r_array = np.sqrt(planet_x_array*planet_x_array + planet_y_array*planet_y_array)  
      
  # Observed separations are given in (km)
  # Phases of the planetary positions are given in (2 pi)
  # Retain the full phase so that multiple epochs may be treated in one array
  observed_phase_array = 1.0 + (time_array - orbit.tpa)/orbit.per
  
  return (observed_r_array, observed_phase_array, planet_r_array)
  



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

def solve_kepler(mean_anom_array, orbit_ecc):
  maximum_iterations = 50
  tolerance = 1.0e-8
  last_array = mean_anom_array

  # Iterative solution for all samples in the mean_anom_array
  for this_step in range(maximum_iterations):    
    solution_array = last_array - orbit_ecc*np.sin(last_array) - mean_anom_array
    derivative_array = 1.0 - orbit_ecc*np.cos(last_array)    
    new_array = last_array - solution_array/derivative_array
    
    # Test if all the array elements have converged
    if np.all(np.isclose(new_array, last_array, tolerance)):
      return new_array
    
    # Not yet converged, so repeat again
    last_array = new_array
  print ("The Kepler inversion did not converge.")
  #raise RuntimeError("The Kepler inversion did not converge.")
  return last_array


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


def ellint3(n_array, k_array):
    
  # Find the elliptic integral of the third kind 
  # Use the Burlirsch algorithm adapted from Jason Eastman's Exofast2
  # Bulirsch 1965, Numerische Mathematik, 7, 78
  # Bulirsch 1965, Numerische Mathematik, 7, 353

  # Tests for acceptable inputs would go here
  # [-1 < n < inf) [0 < k < 1]
  
  # This version set to match matlab's 
  
  p_array = np.sqrt(1.0 - n_array)
  d_array = np.divide( 1.0, p_array)
  kc_array = np.sqrt(1.0 - np.abs(k_array))

  m0_array = np.ones(n_array.size)
  c_array = np.ones(n_array.size)
  e_array = kc_array
  
  tolerance = 1.0e-9
  tolerance_flag = True
  n_iter = 0
  max_iter = 1000
  while tolerance_flag and (n_iter < max_iter):
    f_array = np.copy(c_array)
    c_array = np.add(np.divide(d_array, p_array), f_array)
    g_array = np.divide(e_array,p_array)
    d_array = 2.0 * np.add(np.multiply(f_array, g_array), d_array)
    p_array = np.add(g_array, p_array) 
    g_array = np.copy(m0_array)
    m0_array = np.add(kc_array, m0_array)
    tol_array = np.abs(1.0 - np.divide(kc_array, g_array))
    if ( np.any(np.greater( tol_array, tolerance )) ) :
      kc_array = 2.0 * np.sqrt(e_array)
      e_array = np.multiply(kc_array, m0_array)
      n_iter = n_iter + 1
    else:
      tolerance_flag = False

  ell_arg_1_array = np.multiply(c_array, m0_array) + d_array
  ell_arg_2_array = np.add(m0_array, p_array)
  ell_arg_3_array = np.multiply(m0_array, ell_arg_2_array)
  ellint3_array = 0.5 * np.pi * np.divide(ell_arg_1_array, ell_arg_3_array)
   
  # Use this to extract test values and run ellint3_burlirsch.py for comparison
  
  #print("ellint3 ", ellint3_array)
  #test_index = np.where(ellint3_array < 1.62)
  #print(n_array[test_index], k_array[test_index], ellint3_array[test_index])
  
  return (ellint3_array)  

# ###

# Complete elliptic integral of the first and second kind
#   Hasting's Pade approximation solution

#  Inputs:
#    k:  array of floating point parameters

#  Outputs:
#    ellint1: array of corresponding elliptic  integrals of the first kind 
#    ellint2: array of corresponding ellilptic integrals of the second kind



def ellint(m_array):
  
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
  eta_array = 1.0 - m_array

  # Test and modify out of bounds in k_array
  
  eta_array[ np.where(eta_array < 0.0) ] = 0.0
  eta_array[ np.where(eta_array > 1.0) ] = 1.0 

  log_eta_array = np.log(eta_array)

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
  
  eta_array_p2 = np.multiply(eta_array, eta_array)
  eta_array_p3 = np.multiply(eta_array_p2, eta_array)
  eta_array_p4 = np.multiply(eta_array_p3, eta_array)
  
  ellint1_array_asum = a1*eta_array + a0
  ellint1_array_asum = np.add(ellint1_array_asum, a2*eta_array_p2)  
  ellint1_array_asum = np.add(ellint1_array_asum, a3*eta_array_p3)
  ellint1_array_asum = np.add(ellint1_array_asum, a4*eta_array_p4)
  ellint1_array_bsum = b1*eta_array + b0
  ellint1_array_bsum = np.add(ellint1_array_bsum, b2*eta_array_p2)  
  ellint1_array_bsum = np.add(ellint1_array_bsum, b3*eta_array_p3)
  ellint1_array_bsum = np.add(ellint1_array_bsum, b4*eta_array_p4)
  ellint1_array_bsum_logeta = np.multiply(ellint1_array_bsum, log_eta_array)
  
  ellint1_array = np.subtract(ellint1_array_asum, ellint1_array_bsum_logeta) 
             
  ellint2_array_csum = c1*eta_array + 1.0
  ellint2_array_csum = np.add(ellint2_array_csum, c2*eta_array_p2)  
  ellint2_array_csum = np.add(ellint2_array_csum, c3*eta_array_p3)
  ellint2_array_csum = np.add(ellint2_array_csum, c4*eta_array_p4)
  ellint2_array_dsum = d1*eta_array
  ellint2_array_dsum = np.add(ellint2_array_dsum, d2*eta_array_p2)  
  ellint2_array_dsum = np.add(ellint2_array_dsum, d3*eta_array_p3)
  ellint2_array_dsum = np.add(ellint2_array_dsum, d4*eta_array_p4)
  ellint2_array_dsum_logeta = np.multiply(ellint2_array_dsum, log_eta_array)
  
  ellint2_array = np.subtract(ellint2_array_csum, ellint2_array_dsum_logeta) 
    
  return (ellint1_array, ellint2_array)


# ###

# Find the observed transit events in the time array

# Inputs

#   star parameters
#   planet parameters
#   time_array: sampling times for the orbit (bjd)
#   separation_array: star to planet separations (km)
#   phase_array: phases (units of 2 pi) for each time

# Output

#   parameters of the first transit in the time series

def find_transit_events(star, planet, orbit, time_array, flux_array, separation_array, phase_array):

  observed_events = transit_class(t1=0.0, t2=0.0, tcp=0.0,t3=0.0, 
    t4=0.0, t5=0.0, t6=0.0, tcs=0.0, t7=0.0, t8=0.0, dcp=0.0, dcs=0.0 )

  observed_events.t1  = 0.0 
  observed_events.t2  = 0.0  
  observed_events.tcp = 0.0  
  observed_events.t3  = 0.0  
  observed_events.t4  = 0.0  
  observed_events.t5  = 0.0  
  observed_events.t6  = 0.0  
  observed_events.tcs = 0.0  
  observed_events.t7  = 0.0  
  observed_events.t8  = 0.0  
  observed_events.dcp = 0.0  
  observed_events.dcs = 0.0      
  return observed_events



# ###

# Read the command line

if len(sys.argv) > 3:
  print (" ")
  print ("Usage: transit_model parameters.dat flux.dat  ")
  print (" ")
  sys.exit("Model parameters and time/flux 2-column data for comparison\n")

if len(sys.argv) == 1: 

  print (" ")
  print ("Using default parameters.dat and flux.dat  ")
  print (" ")
   
  # Use default names
  parmfile = "parameters.dat"
  fluxfile = "flux.dat"

else:

  # Use command line names
  parmfile = sys.argv[1]
  fluxfile = sys.argv[2]

# star:  stellar parameters
#   flux: (units of radiant power/area)
#   radius: (km)
#   temperature: (K)
#   ld1: linear limb darkening
#   ld2: quadratic limb darkening

star = star_class(flux=1.0, radius=1.0, temperature=5000.0, ld1=0.3, ld2=0.3, name="")

# planet: planet parameters
#   radius: (units of host star radius)
#   temperature: (K)

planet = planet_class(radius=0.1, temperature=1000.0)

# orbit: system orbit parameters
#   sax: semi-major axis (units of host star radius)
#   per: period (days)
#   inc: inclination (units of radians)
#   ecc: eccentricity defaults to 0
#   omg: omega, the argument of the periastron of the orbit (units of radians)
#   tpa: time of periastron (units of BJD)
#   lan_flag: Boolean to use the longitude of the ascending node
#   lan: longitude of the ascending node (units of radians)
#     default value is pi

orbit = orbit_class(sax=100.0, per=10.0, inc=0.1, ecc=0.01, omg = 0.5, 
tpa=2459000.0, lan_flag=0, lan=3.14159 ) 

# transit: transit events for this star, planet, and orbit
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

observed_transit_events = transit_class(t1=0.0, t2=0.0, tcp=0.0,t3=0.0, 
t4=0.0, t5=0.0, t6=0.0, tcs=0.0, t7=0.0, t8=0.0, dcp=0.0, dcs=0.0 )

# Read the input files  
star, planet, orbit = read_parameter_file(parmfile)
time_array, observed_flux_array = read_data_file(fluxfile)  

# Run the model
model_system_flux_array, model_separation_array, model_phase_array = transit_flux(star, planet, orbit, time_array)
observed_transit_events = find_transit_events(star, planet, orbit, time_array, 
   model_system_flux_array, model_separation_array, model_phase_array) 

# debug
print("time_array", time_array)
print("separation_array", model_separation_array)
print("model_flux_array", model_system_flux_array)




# Save the results
parmfile_base = parmfile.split(".")[0]

# Format and save the model flux
outfile = parmfile_base+"_model_flux.dat"
dataout = np.column_stack((time_array, model_system_flux_array))  
np.savetxt(outfile, dataout)

# Plot the lightcurves with matplotlib and GTK3

plt.figure("Transit Model", figsize=(11,8.5))
plt.plot(time_array, model_system_flux_array, lw=3, color="red")
plt.plot(time_array, observed_flux_array, marker="o", linestyle="None", markersize="3", color="blue")
plt.title(star.name+" from "+parmfile)
plt.xlabel("Time (BJD)")
plt.ylabel("Flux")
plt.show()


exit(0)






