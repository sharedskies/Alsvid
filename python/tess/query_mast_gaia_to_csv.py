#!/usr/local/bin/python3

# John Kielkopf 
# kielkopf@louisville.edu
# Copyright 2021
# Licensed under terms of the MIT license


# 2021-05-10: Version 1.0 accessing EDR3 from MAST
# 2021-06-30: Version 1.1 updated from tk_query_mast_edr3_to_aij_radec

#   
#  For a Rosette region probe use
#  ./query_mast_gaia_to_csv.py 06:32:09.3 +04:49:24.7 0.5 18.0 0.5 1.1
#

"""

  Send a request to MAST for a json table of Gaia stars
  Constrain the search by a direction vector (ra, dec)
  Further constrain by distance and a radius around that 3D point
  Based on the TESS search tool for Gaia stars near a target
  
    Input:
      
      ra_str (hh:mm:ss)
      dec_str (dd:mm:ss)
      search_radius_str (in degrees, typically 0.5 or less)
      limiting_magnitude_str (stars brighter than)
      search_parallax_lower_str  limit (in milliarcseconds) 1 kpc is 1.0 
      search_parallax_upper_str  limit (in milliarcseconds) 1 kpc is 1.0 
      
  
  Export the culled list as a tab-separated csv text format data table
  Also save all the data as a json file

"""  

# Code support

import os            # for system environment
import sys	     # for system connections
import numpy as np   # managing the data
import time          # used by MAST API 
from time import gmtime, strftime, time  # for utc
import re            # for manipulating strings

import json          # MAST API uses json data
import requests      # used to get data from MAST
from urllib.parse import quote as urlencode      #used for request parsing

# Global variables

global ra_str
global dec_str
global limiting_magnitude_str
global search_radius_str
global search_parallax_lower_str
global search_parallax_upper_str

global ra_center
global dec_center
global limiting_magnitude
global search_radius
global search_parallax_lower
global search_parallax_upper



ra_str =  ""
dec_str = ""
limiting_magnitude_str = ""
search_radius_str = ""
search_parallax_lower_str = ""
search_parallax_upper_str = ""

# RA and Dec are in degrees in the Gaia catalog

ra_center = 0.0
dec_center = 0.0

# Radius is in degrees

search_radius = 1.0

# Limiting magnitude should be fainter than 8. to get at least the brightest stars  in Gaia

limiting_magnitude = 18.0

# Parallax is in milliarcseconds

search_parallax_lower = 0.1
search_parallax_upper = 1.5


# Set true for verbose reporting

diagnostics_flag = False



# Convert the ra and dec fields into decimal degrees for query
# Input ra and dec in decimal degrees or hh:mm::ss.ss dd:mm:ss.ss

def parse_coordinates():
  
  global ra_center
  global dec_center
  
  rahr = 0.0
  ramin = 0.0
  rasec = 0.0
  decdeg = 0.0
  decmin = 0.0
  decsec = 0.0

  if ':' in ra_str:
    rahrstr, raminstr, rasecstr = ra_str.split(":")
    rahr = abs(float(rahrstr))
    ramin = abs(float(raminstr))
    rasec = abs(float(rasecstr))
    if float(rahrstr) < 0:
      rasign = -1.
    else:
      rasign = +1.
    ra_center = rasign*(rahr + ramin/60. + rasec/3600.)*15.
  else:  
    try:
      ra_center = float(ra_str)
    except:
      print ("")
      print ("Cannot parse right ascension entry.")
      exit()    
       

  if ':' in dec_str:
    decdegstr, decminstr, decsecstr = dec_str.split(":")
    decdeg = abs(float(decdegstr))
    decmin = abs(float(decminstr))
    decsec = abs(float(decsecstr))
    if float(decdegstr) < 0:
      decsign = -1.
    elif decdegstr[0] == "-":
      decsign = -1.  
    else:
      decsign = +1.
    dec_center = decsign*(decdeg + decmin/60. + decsec/3600.)
  else:  
    try:
      dec_center = float(dec_str) 
    except:
      print ("")
      print ("Cannot parse declination entry.")
      exit()
  return()          


# Format floating point Dec in degrees into a +/-dd:mm:ss.sss Dec string
# Included for reference but not used

def dec_to_dms_str(degrees):
  if degrees > 0:
    dsign = '+'
  elif degrees == 0.0:
    dsign = ' '
  else:
    dsign = '-'
  least_count = (1.0/3600.0)/10000.0
  degrees = abs(degrees) + least_count   
  dd = int(degrees)
  subdegrees = abs( degrees - float(dd) )
  minutes = subdegrees * 60.0
  mm = int(minutes)
  subminutes = abs( minutes - float(mm))
  seconds = subminutes * 60.0
  ss = int(seconds)
  subseconds = abs( seconds - float(ss) )
  milliseconds = subseconds*1000.0
  ms = int(milliseconds)

  anglestr = "%s%02d:%02d:%02d.%03d" % (dsign, dd, mm, ss, ms) 
  return anglestr


# Format floating point RA in degrees into a +/-hh:mm:ss.sss RA string
# Included for reference but not used

def ra_to_hms_str(degrees):
  hours = degrees/15.0
  if hours > 0:
    hsign = '+'
  elif hours == 0.0:
    hsign = ' '
  else:
    hsign = '-'
  least_count = (1.0/3600.0)/10000.0
  hours = abs(hours) + least_count   
  hh = int(hours)
  subhours = abs( hours - float(hh) )
  minutes = subhours * 60.0
  mm = int(minutes)
  subminutes = abs( minutes - float(mm))
  seconds = subminutes * 60.0
  ss = int(seconds)
  subseconds = abs( seconds - float(ss) )
  milliseconds = subseconds*1000.0
  ms = int(milliseconds)

  hourstr = "%s%02d:%02d:%02d.%03d" % (hsign, hh, mm, ss, ms) 
  return hourstr


# Parse limiting magnitude
# Set global limiting_magnitude

def parse_limiting_magnitude():

  global limiting_magnitude
  
  # Parse and clip the limiting magnitude of the search
  limiting_magnitude = np.clip(float(limiting_magnitude_str), 0., 20.)
      
  return()
  

# Parse the search radius
# Set global search_radius

def parse_search_radius():

  global search_radius
  
  # Parse and clip the radius in degrees of the search
  search_radius = np.clip(float(search_radius_str), 0.01, 5.)
      
  return()
 

# Parse the parallax
# Set global search_parallax

def parse_search_parallax():

  global search_parallax_lower
  global search_parallax_upper
  
  # Parse and clip the parallax in milliarcseconds of the search
  search_parallax_lower = np.clip(float(search_parallax_lower_str), 0.1, 2000.0)
  search_parallax_upper = np.clip(float(search_parallax_upper_str), 0.1, 2000.0)
      
  return()

  
# Sends a request to the MAST server and returns the response

def mast_query(request):
  """
    Perform a MAST query.
  
    Parameters
    ----------
    request (dictionary): The MAST request json object
    
    Returns head,content where head is the response HTTP headers, 
    and content is the returned data
  """
  
  # Base API url
  request_url='https://mast.stsci.edu/api/v0/invoke'    
  
  # Grab Python Version 
  version = ".".join(map(str, sys.version_info[:3]))
  
  # Create Http Header Variables
  headers = {"Content-type": "application/x-www-form-urlencoded",
    "Accept": "text/plain",
    "User-agent":"python-requests/"+version}
  
  # Encoding the request as a json string
  req_string = json.dumps(request)
  req_string = urlencode(req_string)
  
  # Perform the HTTP request
  resp = requests.post(request_url, data="request="+req_string, headers=headers)
  
  # Pull out the headers and response content
  head = resp.headers
  content = resp.content.decode('utf-8')
  
  return head, content



# Performs a get request to download a specified file from the MAST server

def download_request(payload, filename, download_type="file"):
  request_url='https://mast.stsci.edu/api/v0.1/Download/' + download_type
  resp = requests.post(request_url, data=payload)

  with open(filename,'wb') as FLE:
    FLE.write(resp.content)

  return filename


# Query the Gaia catalog through MAST

def query_mast_api_gaia(query_ra, query_dec, query_radius):

  # Use MAST tools for the inquiry 
  # We search around the input coordinates assuming ICRS frame
  # Search is without reqard to proper motion since we do not know it yet
  # Choosing a pagesize large enough to accommodate all of the results
  #   or choose a smaller pagesize and 
  #   page through them using the page property
  # Return the search results as a json object
   
  request = {
    'service':'Mast.Catalogs.GaiaDR3.Cone',
    'params':{'ra':query_ra, 'dec':query_dec, 'radius':query_radius},
    'format':'json',
    'pagesize':30000,
    'page':1}   
   
  headers, out_string = mast_query(request)
  gaia_json = json.loads(out_string)

  return gaia_json


# Query the TIC through MAST
# Function retained here for reference

def query_mast_api_tic(query_ra, query_dec, query_radius):

  # Use MAST tools for the inquiry 
  # We search around the input coordinates assuming ICRS frame
  # Search is without reqard to proper motion since we do not know it yet
  # Choosing a pagesize large enough to accommodate all of the results
  #   or choose a smaller pagesize and 
  #   page through them using the page property
  # Return the search results as a json object
   
  request = {
    'service':'Mast.Catalogs.TIC.Cone',
    'params':{'ra':query_ra, 'dec':query_dec, 'radius':query_radius},
    'format':'json',
    'pagesize':30000,
    'page':1}   
   
  headers, out_string = mast_query(request)
  tic_json = json.loads(out_string)

  return tic_json
 
  
# Procedure to query Gaia using MAST
# Save the search as a jason file
# Return a list of stars 

def make_star_array():
     
  # Create a sky objects counter and an empty sky list  buffer (for sorting)

  nsky = 0
  sky = []
  
  gaia_json = query_mast_api_gaia(ra_center, dec_center, search_radius)

  nstars =  gaia_json['paging']['rowsTotal']
  
  if nstars < 1:
    sys.exit('No objects found at  %s  %s ' % (ra_str,dec_str,))
  elif nstars > 30000:
    print(" ")
    print("The pagesize buffer is smaller than the database.")
    print("The results will be truncated.")
    print(" ")
  else:
    print('MAST found %d stars  in Gaia EDR3 near %s  %s ' % (nstars, ra_str, dec_str,))

  # Uncomment these lines to see the fields in the data
  # import pprint
  # pprint.pprint(gaia_json['fields'][:5]) or gaia_json['fields'][:] for all

  # Enter column labels sky[0] of the list
  
  sky.append(("Delta Theta (arcsec)", "ID", 
    "RA (hh:mm:ss)",
    "Dec (dd:mm:ss)",
    "Epoch", 
    "RA (deg)", "RA Error", 
    "Dec (deg)", "Dec Error", 
    "Parallax (mas)", "Parallax Error",
    "PM RA (mas/y)", "PM RA Error",
    "PM Dec (mas/y)", "PM Dec Error",  
    "g Mean Flux", "g Mean Flux Error", "g Mean Magnitude",
    "bp Mean Flux", "bp Mean Flux Error", "bp Mean Magnitude",
    "rp Mean Flux", "rp Mean Flux Error", "rp Mean Magnitude",
    "bp-rp", "bp-g", "g-rp"))                       


  # Add gaia stars to the sky list one by one

  textmark = '\''
  for gaia_star in gaia_json['data']:

    # These are the values from the Gaia EDR3
    # Coordinates are ICRS epoch 2000.0 with proper motion to ref_epoch
    
    source_id                  = textmark+str('EDR3 ')+str(gaia_star['source_id'])+textmark                             
    ref_epoch                  = gaia_star['ref_epoch']
    ra_gaia                    = gaia_star['ra']
    ra_error                   = gaia_star['ra_error']
    dec_gaia                   = gaia_star['dec']
    dec_error                  = gaia_star['dec_error']
    parallax                   = gaia_star['parallax']
    parallax_error             = gaia_star['parallax_error']
    pmra                       = gaia_star['pmra']
    pmra_error                 = gaia_star['pmra_error']
    pmdec                      = gaia_star['pmdec']
    pmdec_error                = gaia_star['pmdec_error']
    phot_g_mean_flux           = gaia_star['phot_g_mean_flux']
    phot_g_mean_flux_error     = gaia_star['phot_g_mean_flux_error']
    phot_g_mean_mag            = gaia_star['phot_g_mean_mag']
    phot_bp_mean_flux          = gaia_star['phot_bp_mean_flux']
    phot_bp_mean_flux_error    = gaia_star['phot_bp_mean_flux_error']
    phot_bp_mean_mag           = gaia_star['phot_bp_mean_mag']
    phot_rp_mean_flux          = gaia_star['phot_rp_mean_flux']
    phot_rp_mean_flux_error    = gaia_star['phot_rp_mean_flux_error']
    phot_rp_mean_mag           = gaia_star['phot_rp_mean_mag']
    bp_rp                      = gaia_star['bp_rp']
    bp_g                       = gaia_star['bp_g']
    g_rp                       = gaia_star['g_rp']

    # These entries are in DR2 but not in EDR3 yet
    
    # radial_velocity            = gaia_star['radial_velocity']
    # radial_velocity_error      = gaia_star['radial_velocity_error']
    # phot_variable_flag         = gaia_star['phot_variable_flag']
          
    # Invalid entries are None
    # Valid entries are numbers
                  
    # ra and dec are in degrees at Gaia epoch
    # Make adjustments for PM here if needed before assignment to table
       
    ra = ra_gaia
    dec = dec_gaia 


    # Use first star found as the field center reference
    
    if nsky == 0:
      ra_reference = ra
      dec_reference = dec
      
                        
    # Trap missing magnitudes with unrealistically faint numbers
    
    if phot_g_mean_mag is None:
      phot_g_mean_mag = 99.
    if phot_bp_mean_mag is None:
      phot_bp_mean_mag = 99.
    if phot_rp_mean_mag is None:
      phot_rp_mean_mag = 99.

    # Select based on phot_rp_mean_mag, phot_g_mean_mag, phot_bp_mean_mag in priority sequence
           
    if (phot_rp_mean_mag < limiting_magnitude):    
      selected_flag = True
    elif (phot_g_mean_mag < limiting_magnitude):
      selected_flag = True
    elif (phot_bp_mean_mag < limiting_magnitude):
      selected_flag = True
    else:
      selected_flag = False

    # Trap missing parallax with a zero to place target at infinity
      
    if parallax is None:
      parallax = 0.  

    # If the magnitude criteria are met then deselect based on parallax out of range
    
    if selected_flag:
    
      if ((parallax < search_parallax_lower) or (parallax > search_parallax_upper)):
        selected_flag = False
    
    # Insert additional selection criteria  here

    if selected_flag:
      delta_theta_rad = np.arccos(np.sin(np.radians(dec))*np.sin(np.radians(dec_reference)) + np.cos(np.radians(dec))*np.cos(np.radians(dec_reference))*np.cos(np.radians(ra - ra_reference)))              
      delta_theta_arcsec = abs(3600.*np.degrees(delta_theta_rad))

        
    # If selected then add star to the list
                   
    if selected_flag: 
                            
      sky.append((delta_theta_arcsec, source_id, 
        ra_to_hms_str(ra), dec_to_dms_str(dec),
        ref_epoch, 
        ra, ra_error, 
        dec, dec_error, 
        parallax, parallax_error,
        pmra, pmra_error,
        pmdec, pmdec_error,  
        phot_g_mean_flux, phot_g_mean_flux_error, phot_g_mean_mag,
        phot_bp_mean_flux, phot_bp_mean_flux_error, phot_bp_mean_mag,
        phot_rp_mean_flux, phot_rp_mean_flux_error, phot_rp_mean_mag, 
        bp_rp, bp_g, g_rp))                       
      
      nsky = nsky + 1
      

  print("")
  print("Found ", nsky, " out of ",  nstars,  " after culling the Gaia field.")
  print("")


  # Save the json file
  with open('gaia_stars.json', 'w') as file:
    json.dump(gaia_json, file)

  # Return the Gaia list
  return sky


# Parse the  command line


if len(sys.argv) == 7:
  ra_str = sys.argv[1]
  dec_str = sys.argv[2]
  search_radius_str = sys.argv[3]
  limiting_magnitude_str = sys.argv[4]
  search_parallax_lower_str = sys.argv[5]
  search_parallax_upper_str = sys.argv[6]
else:
  print(" ")
  print("Usage: query_mast_gaia_to_csv.py ra dec search_radius limiting_magnitude search_parallax_lower search_parallax_upper")
  print(" ")
  sys.exit("Search a field for Gaia stars and generate a database\n")

# Remove non-numeric characters and spaces from parameter strings 

search_radius_str = float(re.sub(r'([^-+\.0-9])+', '', search_radius_str))
limiting_magnitude_str = float(re.sub(r'([^-+\.0-9])+', '', limiting_magnitude_str))
search_parallax_lower_str = float(re.sub(r'([^-+\.0-9])+', '', search_parallax_lower_str))
search_parallax_upper_str = float(re.sub(r'([^-+\.0-9])+', '', search_parallax_upper_str))

# Remove non-numeric characters excepting delimiters from coordinate strings 

ra_str = re.sub(r'([^-+\.\:0-9])+', '', ra_str).strip()
dec_str = re.sub(r'([^-+\.\:0-9])+', '', dec_str).strip()


# Now acknowledge the request

print ("")
print ("Request to be sent for Gaia stars in the field:")
print ("RA = ", ra_str)
print ("Dec = ", dec_str)
print ("Radius = ", search_radius_str)
print ("Limiting magnitude = ", limiting_magnitude_str)
print ("Parallax lower limit = ", search_parallax_lower_str)
print ("Parallax upper limit = ", search_parallax_upper_str)
print ("")
print ("Processing ... ")
print ("")

# Parse coordinates based on the style of the input

parse_coordinates()

# Parse magnitude from input

parse_limiting_magnitude()

# Parse parallax from input

parse_search_parallax()

# Parse  from input

parse_search_radius()

# Query Gaia and generate the list

stars = make_star_array()

nrows = len(stars)
ncols = len(stars[0])
stars_fp = open("gaia_stars.csv", 'w')

for j in range(nrows):
  starline =""
  for i in range(ncols):
    entry = str(stars[j][i])
    if i < ncols - 1 :
      starline = starline + str(stars[j][i]) + "\t"
    else:
      starline = starline + str(stars[j][i]) + "\n"

  stars_fp.write(starline)

stars_fp.close()

exit()


