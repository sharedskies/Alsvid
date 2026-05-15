#!/usr/local/bin/python3

# Query the Gaia database on MAST for sky coordinates 
# Convert to AstroImageJ radec format

# J. Kielkopf, K. Collins, E. Jensen 
# https://www.astro.louisville.edu://software/tess/
# MIT License

# 2021-05-19: Version 2.0  Gaia EDR3 from MAST
# 2021-05-28: Version 2.1  JD errors corrected
# 2021-06-14: Version 2.2  Added sub-mas precision to radec coordinates
# 2021-06-21: Version 2.3  Comments, clarity, and cleanup tested on Proxima Cen
# 2022-08-11: Version 2.4  to use DR3 instead of EDR3
# 2022-12-03: Version 2.5  updated file name and annotations for DR3


"""

  tk_query_mast_dr3_to_aij_radec.py
  
  Find stars in the MAST Gaia DR3 near a target meeting magnitude constraints
  Tk graphical interface
  
  Input:
  
    RA:  Right ascension observed for target
    Dec: Declination observed for target
    Date: Date of observation
    
  Output:
  
    Apertures file for AstroImageJ in radec format for epoch of date
     

  Comment:
  
    The output table models the proper motion from the date
    of the catalog entry to the date of the observation.


"""




# Tk interface

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

# Code support

import os                          # for system environment
import sys                         # for system connections
import numpy as np                 # managing the data
import time                        # used by MAST API
from time import gmtime, strftime  # for utc
import re                          # for manipulating strings

import json                        # MAST API uses json data
import requests                    # used to get data from MAST
from urllib.parse import quote as urlencode    #used for request parsing

# Global variables

global diagnostics_flag
global centroid_flag
global rastr
global decstr
global depthstr
global datestr
global reference_file
global aperture_file
global ra_center
global dec_center
global ref_center
global tess_magnitude
global tess_depth
global search_radius_degrees
global status


# Set this True for diagnostics
diagnostics_flag = False

# Set this True to centroid the first aperture
centroid_flag = True

# Allow user to set aperture file name
allow_aperture_file_reset = True

# Aperture file up one level from image by default
aperture_file_in_image_directory = False 


# These parameters are global
rastr = " "
decstr = " "
datestr = " "
aperture_file = "mast_dr3_stars.radec"
magstr = "10."
depthstr = "1.0"
ra_center = 0.
dec_center = 0.
tess_magnitude = 10.
tess_depth = 1.0
search_radius_degrees = 2.5/60
status = "Ready"

# Reference for coordinates may be 
#   tic (default ICRS with proper motion to 2000.0)
#   gaia (BCRS with proper motion, to 2016.0)
#   eod (epoch of date with coordinates as observed currently)

ref_center = "tic"


# Convert the ra and dec fields into decimal degrees for query
# Input ra and dec in decimal degrees or hh:mm::ss.ss dd:mm:ss.ss

def parse_coords():
  
  global rastr
  global decstr
  global ra_center
  global dec_center
  
  rahr = 0.
  ramin = 0.
  rasec = 0.
  decdeg = 0.
  decmin = 0.
  decsec = 0.

  if ':' in rastr:
    rahrstr, raminstr, rasecstr = rastr.split(":")
    rahr = abs(float(rahrstr))
    ramin = abs(float(raminstr))
    rasec = abs(float(rasecstr))
    if float(rahrstr) < 0:
      rasign = -1.
    else:
      rasign = +1.
    ra_center = rasign*(rahr + ramin/60. + rasec/3600.)*15.
  else:  
    ra_center = float(rastr) 

  if ':' in decstr:
    decdegstr, decminstr, decsecstr = decstr.split(":")
    decdeg = abs(float(decdegstr))
    decmin = abs(float(decminstr))
    decsec = abs(float(decsecstr))
    if float(decdegstr) < 0:
      decsign = -1.
    else:
      decsign = +1.
    dec_center = decsign*(decdeg + decmin/60. + decsec/3600.)
  else:  
    dec_center = float(decstr)
    
  return   


# JD routines are in ERFA (IAU), Astropy, and Skyfield
# See for example
# https://github.com/liberfa/erfa/blob/master/src/jd2cal.c
# https://github.com/liberfa/erfa/blob/master/src/cal2jd.c
# The following is adapted from Meeus Astronomical Algorithms

# Return the Julian date for a given year, month, day, and UTC

def jd(y0,m0,d0,u0):
  k = int(y0)
  m = int(m0)
  i = int(d0)
  utc = u0
  j1 = float(367*k)
  j2 = -1.*float( int( ( 7*(k + int((m+9)/12) ) )/4 ) )
  j3 = float(i + int(275*m/9))
  j4 = 1721013.5 + (utc/24.0)
  julian = j1 + j2 + j3 + j4
  return julian


# Return the Julian date for a given floating point epoch in years
# Accuracy:
#   The routine takes the difference between two large numbers
#   Python floating point has 18 digits of precision
#   JD day count uses 7 digits
#   JD UTC differencing for 1 second would be 1 part out of 86400
#   There is a 5 digit buffer at this level of time precision
#     when calling jd() twice

def jd_for_epoch(epoch):  
  int_year = int(epoch)
  fraction_of_year = epoch - float(int_year)
  jd_start_of_year = jd(int_year, 1, 1, 0.) 
  jd_start_of_next_year = jd(int_year + 1, 1, 1, 0.) 
  days_this_year = jd_start_of_next_year - jd_start_of_year
  julian_day_for_epoch  = jd_start_of_year + fraction_of_year*days_this_year
  return julian_day_for_epoch


# Format degrees or hours into a hexagesimal  +/-dd:mm:ss.sss string
# This routine is used to format the output for both RA and Dec
# If the source is RA in degrees then divide by 15 first and the output
#   will be RA in hh:mm:ss.sss 
# Or use ra_to_hms_str(degrees) copied below

def float_to_dms_str(degrees):
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



# Tk management  


def query_exit():
  # clean up and exit

  if diagnostics_flag:
    print("Closed user interface")
  
  root.destroy()
  exit(1)
  return

def query_start():
  global status
  
  if status == "Starting":
    status = "Running"
    tk_status.set(status)
  elif status == "Running":
    query_run()
  else:    
    status = "Starting"
    tk_status.set(status)

  return

def query_run():
  global rastr
  global decstr
  global magstr
  global depthstr
  global datestr
  global status
  global reference_file
  global aperture_file

  status ="Running"
  tk_status.set(status)
  rastr = tk_rastr.get()
  decstr = tk_decstr.get()
  magstr = tk_magstr.get()
  depthstr = tk_depthstr.get()
  datestr = tk_datestr.get()
  aperture_file = tk_aperture_file.get()

  make_apertures()
  status ="Done"
  tk_status.set(status)

  return
      
def browse_reference_file():
  global reference_file
  global aperture_file

  # Open a file menu
  reference_file = filedialog.askopenfilename(filetypes = [("FITS files", ".fits .fit .fts .fits.gz .fit.gz .fts.gz .FITS .FIT .FTS"),("all files",".*")])
  tk_reference_file.set(reference_file)
  
  # Set an aperture file name based on the reference file name 
  # This can be overridden by selecting another name with the browse_aperture_file function

  if aperture_file_in_image_directory:
    # Keep aperture file with image
    aperture_file = os.path.dirname(reference_file)+"/"+os.path.splitext(os.path.basename(reference_file))[0]+'.apertures'
  else:
    # Put aperture file one level up
    aperture_file = os.path.dirname(reference_file)+"/../"+os.path.splitext(os.path.basename(reference_file))[0]+'.apertures'
  tk_aperture_file.set(aperture_file)

  return

def browse_aperture_file():
  global aperture_file
  
  # Open a file menu
  aperture_file = filedialog.asksaveasfilename(filetypes = [("Aperture files", ".apertures"), ("all files",".*")])
  tk_aperture_file.set(aperture_file)

  return
  

def show_help():
  text = "Gaia Stars to AstroImageJ\n\n"
  text = text + "Selects those Gaia stars that could "
  text = text + "effect a TESS transit signal "
  text = text + "and exports them to an AstroImageJ radec file.\n\n"
  text = text + "An aperture file will be suggested but "
  text = text + "you may select your own. "
  text = text + "Add the target location, "
  text = text + "the TESS magnitude, and transit depth.\n\n"
  text = text + "Press [Query] to run.\n\n"
  text = text + "Version 2.0 .\n\n"  
  text = text + "For updates see \n"
  text = text + "www.astro.louisville.edu/software/tess"
  messagebox.showinfo("Help", text)
  
  return

 
# Manage the processing with updates

def monitor_process():
  global status
  tk_status.set(status)
  if status == "Running" or status == "Starting":
    query_start()
  root.after(2000, monitor_process)

  return
  
  
# Send a request to the MAST server and return the response

def mast_query(request):
  """
    Perform a MAST query
  
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


# Perform a get request to download a specified file from the MAST server

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



# Find Gaia stars

def find_gaias():

  # Create a sky objects counter and an empty sky list  buffer (for sorting)


  # Send the request
  # This is contained in a separate routine to localize the dependency and error handling
  
  gaia_json = query_mast_api_gaia(ra_center, dec_center, search_radius_degrees)

  # Uncomment for diagnostic
  # print(gaia_json)

  # Uncomment to see the fields and data types in the data
  
  # import pprint
  # pprint.pprint(gaia_json['fields'])

  nstars =  gaia_json['paging']['rowsTotal']
  labels = gaia_json['fields']
  
  if nstars < 1:
    print(" ")
    sys.exit('No stars were found near  %s  %s ' % (rastr,decstr,))
  elif nstars == 1:
    print(" ")
    print('Found %d star in DR3 near %s  %s ' % (nstars, rastr, decstr,))  
    print(" ")
  else:
    print(" ")
    print('Found %d stars in DR3 near %s  %s ' % (nstars, rastr, decstr,))
    print(" ")
  
  labels = gaia_json['fields']
  stars = gaia_json['data']

  # Return the number of stars, column labels and star data as json objects
  
  return nstars, labels, stars
  


# Make the radec file of apertures

# Procedure to query Gaia and generate the star list
# Write a temporary file
# Return the file name to use in responding to the request


def make_apertures():

  global reference_file
  global rastr
  global decstr
  global depthstr
  global datestr
  global tess_magnitude
  global tess_depth

      
  # Parse coordinates based on the style of the input
  parse_coords()
  
  # Parse magnitude from input
  tess_magnitude = np.clip(float(magstr), 0., 20.)
  
  # Parse and clip the depth string in PPT to relative flux
  tess_depth = np.clip(float(depthstr)/1000., 0.0001, 0.9999)
  
  # Convert the depth in PPT to search delta magnitude
  tess_dmag = -2.5*np.log10(tess_depth)

  # Parse date from input
  date_parts = datestr.split('-')
  if len(date_parts) == 3:  
    yr = date_parts[0]
    mo = date_parts[1]
    da = date_parts[2]
    jd_obs = jd(yr, mo, da, 0.)
  else:
    datestr = "2021-01-01"
    jd_obs = 2459215.500000

  
  # Set the elapsed time in years from the epoch of the Gaia data to the epoch of observation
     
  delta_t = (jd_obs - jd(2016,1,1,0.5)) / 365.25

  # Set the elapsed time in years from the epoch of the Gaia data to the epoch of center
  # This will be negative if the center epoch is before 2016 and positive after 2016

  if ref_center  == "gaia":
    # Gaia DR3 is in BCRS at 2000.0 with proper motion included to to 2016.0
    delta_t_center = 0.0 
  elif ref_center == "tic":
    # TIC is in ICRS coordinates for 2000.0
    delta_t_center = (jd(2000,1,1,0.5) - jd(2016,1,1,0.5)) / 365.25    
  elif ref_center == "eod":  
    delta_t_center = (jd_obs - jd(2016,1,1,0.5)) / 365.25       
  else:
    delta_t_center =  (jd(2000,1,1,0.5) - jd(2016,1,1,0.5)) / 365.25
 
     
  if diagnostics_flag:
    print("Request inputs -- \n")
    print("Target coordinates: ", rastr,  "  ", decstr)
    print("Magnitude requested: ", tess_magnitude)
    print("Transit depth requested: ", tess_depth)
    print("Observation date: ", datestr, "  ", jd_obs)
    print("Time from Gaia DR3 to observation (yr): ", delta_t)
    print("Time from Gaia DR3 to center coordinate epoch (yr): ", delta_t_center)

  # Create a sky objects counter and buffer
  
  nsky = 0
  sky = []

  # Send the request and return a list of star with string elements
  
  nstars, labels, stars  = find_gaias()
  
  # Check again that there are stars in these data
  
  if nstars < 1:
    sys.exit('No objects found at  %s  %s ' % (rastr,decstr,))
  

  # Add Gaia stars to the sky list
  # Select stars based on magnitude and separation from the target
  
  # From the EDR3 early release documentation: https://www.cosmos.esa.int/web/gaia/earlydr3

  # Gaia DR3 data (both Gaia EDR3 and the full Gaia DR3) are based on data
  # collected between 25 July 2014 (10:30 UTC) and 28 May 2017 (08:44 UTC),
  # spanning a period of 34 months. As a comparison, Gaia DR2 was based on 22
  # months of data and Gaia DR1 was based on observations collected during
  # the first 14 months of Gaia's routine operational phase.

  # The reference epoch for Gaia DR3 (both Gaia EDR3 and the full Gaia DR3)
  # is 2016.0. Remember that the reference epoch is different for each Gaia
  # data release (it is J2015.5 for Gaia DR2 and J2015.0 for Gaia DR1).

  # Positions and proper motions are referred to the ICRS, to which the
  # optical reference frame defined by Gaia DR3 is aligned. The time
  # coordinate for Gaia DR3 is the barycentric coordinate time (TCB).
  
  for i in range(nstars):
     
    if isinstance(stars[i]['ra'], type(None)):
      ra_gaia = 0.0
    else:
      ra_gaia = float(stars[i]['ra'])

    if isinstance(stars[i]['dec'], type(None)):
      dec_gaia = 0.0
    else:
      dec_gaia = float(stars[i]['dec'])

    if isinstance(stars[i]['source_id'], type(None)):
      src_id = ' '
    else:
      src_id = stars[i]['source_id']  

    if isinstance(stars[i]['phot_bp_mean_mag'], type(None)):
      mag_b = 99.0
    else:
      mag_b = float(stars[i]['phot_bp_mean_mag'])
       
    if isinstance(stars[i]['phot_g_mean_mag'], type(None)):
      mag_g = 99.0
    else:
      mag_g = float(stars[i]['phot_g_mean_mag'])

    if isinstance(stars[i]['phot_rp_mean_mag'], type(None)):
      mag_r = 99.0
    else:
      mag_r = float(stars[i]['phot_rp_mean_mag'])

    if isinstance(stars[i]['bp_g'], type(None)):
      color_bmg = 99.0
    else:
      color_bmg = float(stars[i]['bp_g'])

    if isinstance(stars[i]['bp_rp'], type(None)):
      color_bmr = 99.0
    else:
      color_bmr = float(stars[i]['bp_rp'])

    if isinstance(stars[i]['g_rp'], type(None)):
      color_gmr = 99.0
    else:
      color_gmr = float(stars[i]['g_rp'])
            
    if isinstance(stars[i]['pmra'], type(None)):
      pm_ra = 0.0
    else:
      pm_ra = float(stars[i]['pmra'])

    if isinstance(stars[i]['pmdec'], type(None)):
      pm_dec = 0.0
    else:
      pm_dec = float(stars[i]['pmdec'])
      
    if isinstance(stars[i]['parallax'], type(None)):
      parallax = 0.0
    else:
      parallax = float(stars[i]['parallax'])
      
    if isinstance(stars[i]['distance'], type(None)):
      distance = 0.0
    else:
      distance = float(stars[i]['distance'])

    if isinstance(stars[i]['ref_epoch'], type(None)):
      ref_epoch = 2016.0
    else:
      ref_epoch = stars[i]['ref_epoch']  
                           
    # Assign an effective TESS magnitude based on Gaia DR2 calibration in the TIC    
    # Check if the color b-r exists first

    if (color_bmr < 99.0):
      c1 = color_bmr
      c2 = c1*c1
      c3 = c2*c1
      star_magnitude = mag_g - 0.00522555*c3 + 0.0891337*c2 - 0.633923*c1 + 0.0324473
    else:   
      star_magnitude = mag_g - 0.430          

    # Select targets based on magnitude
    # Reject stars that are too faint to create the observed transit depth

    selected_flag = (star_magnitude < (tess_magnitude + tess_dmag + 0.5))
    
    # Other selection criteria would go here
 

    # Build the ordered output database for the selected stars          

    if selected_flag: 
                  
      # Use the Gaia entry to find the coordinates at the epoch of observation.       
      # PMs are in milliarcseconds per year for 
      # the angle on the sky in the direction of Dec of RA
    
      delta_ra = pm_ra * delta_t / ( 3600.0*1000.0*np.cos(np.radians(dec_gaia)) )
      delta_dec = pm_dec * delta_t / ( 3600.0*1000.0 )
      ra = ra_gaia + delta_ra
      dec = dec_gaia + delta_dec

      # Where was this star at the epoch of the center coordinates?
      
      delta_ra_center = pm_ra * delta_t_center / ( 3600.0*1000.0*np.cos(np.radians(dec_gaia)) )
      delta_dec_center = pm_dec * delta_t_center / ( 3600.0*1000.0 )
      ra_at_center_epoch = ra_gaia + delta_ra_center
      dec_at_center_epoch = dec_gaia + delta_dec_center

      # What was the angular separation of this star from the center at the center epoch?

      delta_theta_rad = np.arccos(np.sin(np.radians(dec_center))*np.sin(np.radians(dec_at_center_epoch)) + np.cos(np.radians(dec_center))*np.cos(np.radians(dec_at_center_epoch))*np.cos(np.radians(ra_center - ra_at_center_epoch)))              
      delta_theta = abs(3600.*np.degrees(delta_theta_rad))         
      
      # Example of testing a specific star

      # if (i == 408):
      #   print("Found 408")
      #   print("T magnitude from Gaia: ", star_magnitude)
      #   print("dec_gaia: ", dec, dec_to_dms_str(dec_gaia))
      #   print("ra_gaia: ", ra, ra_to_hms_str(ra_gaia))
      #   print("dec: ", dec, dec_to_dms_str(dec))
      #   print("ra: ", ra, ra_to_hms_str(ra))
      #   print("dec_at_center_epoch: ", dec_at_center_epoch, dec_to_dms_str(dec_at_center_epoch))
      #   print("ra_at_center_epoch: ", ra_at_center_epoch, ra_to_hms_str(ra_at_center_epoch))
      #   print("dec_center: ", dec_center, dec_to_dms_str(dec_center))
      #   print("ra_center: ", ra_center, ra_to_hms_str(ra_center))
      #   print("delta_theta_rad: ", delta_theta_rad)
      #   print("delta_theta (arcsec): ", delta_theta)
      #   print(" ")
        
        
      # Find magnitude difference (flux ratio) compared to the target
      # Take smallest magnitude ratio to associate this star with the target and assign it as T1
      
      delta_mag_gaia = abs(star_magnitude - tess_magnitude)
                   
      
      # Create a selection ranking for ordering the aperture list from 0.0
      # Within uncertainty_theta it will rank most highly the stars closest to the target 
      # Outside that region it will rank by magnitude

      uncertainty_theta = 8.
      uncertainty_mag_gaia = 1.
      if delta_theta > uncertainty_theta:
        rank = delta_theta   
      else:
        rank = delta_mag_gaia/100.
                       
      # Print diagnostics if requested

      if diagnostics_flag:
        print("Entry: ", i)
        print("RA (deg BCRS): ", ra_gaia)
        print("Dec (deg BCRS): ", dec_gaia)
        print("T magnitude: ", star_magnitude)
        print("Parallax (mas): ", parallax)
        print("PM -> +RA (mas/yr): ", pm_ra)
        print("PM -> +Dec (mas/yr): ", pm_dec)
        print("Delta theta (arcsec): ", delta_theta)
        print("") 


      # Add this selected star to the sky list with ra, dec, magnitude,  delta mag_tic,  delta_theta, and rank
      
      sky.append((ra, dec, star_magnitude, delta_theta, delta_mag_gaia, rank))
      nsky = nsky + 1
      
  # Create a numpy array to make sorting easier
  
  sky_star_array = np.array(sky)
          
  # Sort by rank to make the  target star first
  
  sky_star_array = sky_star_array[sky_star_array[:,5].argsort()]

  # Alert the user to the content of new apertures file
  
  print("Identified ", nsky, " out of ",  nstars,  " after culling the Gaia field.")
  print("  ")
  
  # Copy the first two columns with ra and dec from columns "0" and "1" of the sorted array
  # Create a new array for the ra, dec, and magnitude list
  
  sky_coord_array = sky_star_array[:,0:3]  
  
    
  # Open the file
  aperture_fp = open(aperture_file, 'w')
  
  # Write data line by line
  # RA in sexagesimal hours
  # Dec in sexagesimal degrees
  # TESS approximate magnitude based on selection from Gaia DR3
  
  # Formatted for AstroImageJ
  # RA in decimal or sexagesimal HOURS
  # Dec in decimal or sexagesimal DEGREES
  # Ref Star=0,1,missing (0=target star, 1=ref star, missing->first ap=target, others=ref)
  # Centroid=0,1,missing (0=do not centroid, 1=centroid, missing=centroid)
  # Apparent Magnitude or missing (value = apparent magnitude, or value > 99 or missing = no mag info)
  # One comma separated line per aperture in the following format:
  #   RA, Dec, Ref Star, Centroid, Magnitude

  for i in range(nsky):
        
    ra_star = (sky_coord_array[i,0])/15.
    dec_star = sky_coord_array[i,1]
    mag_star = sky_coord_array[i,2]
    ra_star_str = float_to_dms_str(ra_star)
    dec_star_str = float_to_dms_str(dec_star)
    if centroid_flag and (i == 0):
      skyline = "%s,  %s, 0, 1, %6.3f\n" % (ra_star_str, dec_star_str, mag_star) 
    else:
      skyline = "%s,  %s, 0, 0, %6.3f\n" % (ra_star_str, dec_star_str, mag_star) 
    aperture_fp.write(skyline)

  # Close the output file
  aperture_fp.close()
  print("Saved apertures in ", aperture_file)
  print(" ")
  
  return
  

# Create the root window

root = tk.Tk()
root.title("AstroImageJ Apertures")

# Add a frame to the window

mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

# Create Tk strings for displayed information

tk_datestr = tk.StringVar()
tk_datestr_entry = ttk.Entry(mainframe, textvariable=tk_datestr, width=12)
tk_datestr_entry.grid(column=2, row=2, sticky=tk.W)

tk_aperture_file = tk.StringVar()
if allow_aperture_file_reset:
  tk_aperture_file_entry = ttk.Entry(mainframe, textvariable=tk_aperture_file, width=40)
  tk_aperture_file_entry.grid(column=2, row=3, sticky=tk.W)

tk_rastr = tk.StringVar()
tk_rastr_entry = ttk.Entry(mainframe, textvariable=tk_rastr, width=12)
tk_rastr_entry.grid(column=2, row=4, sticky=tk.W)

tk_decstr = tk.StringVar()
tk_decstr_entry = ttk.Entry(mainframe, textvariable=tk_decstr, width=12)
tk_decstr_entry.grid(column=2, row=5, sticky=tk.W)

tk_magstr = tk.StringVar()
tk_magstr_entry = ttk.Entry(mainframe, textvariable=tk_magstr, width=12)
tk_magstr_entry.grid(column=2, row=6, sticky=tk.W)

tk_depthstr = tk.StringVar()
tk_depthstr_entry = ttk.Entry(mainframe, textvariable=tk_depthstr, width=12)
tk_depthstr_entry.grid(column=2, row=7, sticky=tk.W)

tk_status = tk.StringVar()

# Initialize the display content strings

tk_aperture_file.set(aperture_file)
tk_rastr.set(rastr)
tk_decstr.set(decstr)
tk_magstr.set(magstr)
tk_depthstr.set(depthstr)
tk_datestr.set(datestr)
tk_status.set(status)


#Add widgets to the grid within the frame

# Row 0
ttk.Label(mainframe, text="Query MAST Gaia DR3 for AstroimageJ").grid(column=1, row=0, sticky=tk.W, columnspan=3)


# Row 1


# Row 2
ttk.Label(mainframe, text="Observation Date").grid(column=0, row=2, sticky=tk.W)
ttk.Label(mainframe, textvariable=tk_datestr).grid(column=1, row=2, sticky=(tk.W, tk.E))
ttk.Label(mainframe, text="yyyy-mm-dd").grid(column=3, row=2, sticky=tk.W)

# Row 3
ttk.Label(mainframe, text="Apertures File").grid(column=0, row=3, sticky=tk.W)
ttk.Label(mainframe, textvariable=tk_aperture_file).grid(column=1, row=3, sticky=(tk.W, tk.E))
if allow_aperture_file_reset:
  ttk.Button(mainframe, text="Select", command=browse_aperture_file).grid(column=3, row=3, sticky=tk.W)

# Row 4
ttk.Label(mainframe, text="Target RA").grid(column=0, row=4, sticky=tk.W)
ttk.Label(mainframe, textvariable=tk_rastr).grid(column=1, row=4, sticky=(tk.W, tk.E))
ttk.Label(mainframe, text="hh:mm:ss.ss").grid(column=3, row=4, sticky=tk.W)

# Row 5
ttk.Label(mainframe, text="Target Dec").grid(column=0, row=5, sticky=tk.W)
ttk.Label(mainframe, textvariable=tk_decstr).grid(column=1, row=5, sticky=(tk.W, tk.E))
ttk.Label(mainframe, text="dd:mm:ss.ss").grid(column=3, row=5, sticky=tk.W)

# Row 6
ttk.Label(mainframe, text="Target Magnitude").grid(column=0, row=6, sticky=tk.W)
ttk.Label(mainframe, textvariable=tk_magstr).grid(column=1, row=6, sticky=(tk.W, tk.E))
ttk.Label(mainframe, text="TESS").grid(column=3, row=6, sticky=tk.W)


# Row 7
ttk.Label(mainframe, text="TESS Depth").grid(column=0, row=7, sticky=tk.W)
ttk.Label(mainframe, textvariable=tk_depthstr).grid(column=1, row=7, sticky=(tk.W, tk.E))
ttk.Label(mainframe, text="PPT").grid(column=3, row=7, sticky=tk.W)


# Row 8

# Row 9
ttk.Separator(mainframe, orient=tk.HORIZONTAL).grid(row=9, column=0, columnspan=4, sticky=(tk.EW), pady=20)

#Row 10
ttk.Button(mainframe, text="Exit", command=query_exit).grid(column=0, row=10, sticky=tk.W)
ttk.Label(mainframe, textvariable=tk_status).grid(column=1, row=10, sticky=tk.W, columnspan=1)
ttk.Button(mainframe, text="Query", command=query_start).grid(column=2, row=10, sticky=tk.W)
ttk.Button(mainframe, text="Help", command=show_help).grid(column=3, row=10, sticky=tk.W)

# Pad the widgets for appearance

for child in mainframe.winfo_children(): 
  child.grid_configure(padx=5, pady=5)

#
# GUI mainloop
#

root.after(2000, monitor_process)
root.mainloop()
root.destroy()
exit()




