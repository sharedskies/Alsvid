#!/usr/local/bin/python3

# Query the TIC database on MAST for sky coordinates 
# Convert to AstroImageJ radec format

# J. Kielkopf and K. Collins 
# https://www.astro.louisville.edu://software/tess/
# MIT License

# 2021-05-19: Version 2.0

"""

  tk_query_mast_tic_to_aij_radec.py
  
  Find stars in the MAST TIC near a target meeting magnitude constraints
  Tk graphical interface
  
  Input:
  
    RA:  Right ascension observed for target
    Dec: Declination observed for target
    Date: Date of observation
    
  Output:
  
    Apertures file for AstroImageJ in radec format
     

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

global centroid_flag
global reference_flag
global diagnostics_flag
global rastr
global decstr
global depthstr
global datestr
global reference_file
global aperture_file
global ra_center
global dec_center
global tess_magnitude
global tess_depth
global search_radius_degrees
global status
global center_src


# Set this True to centroid the first aperture
centroid_flag = True

# Set this True for default target/calibrator assignments
reference_flag = True

# Set this True for diagnostics
diagnostics_flag = False

# Allow user to set aperture file name
allow_aperture_file_reset = True

# Aperture file up one level from image by default
aperture_file_in_image_directory = False 


# These parameters are global
rastr = " "
decstr = " "
datestr = " "
aperture_file = "mast_tic_stars.radec"
magstr = "10."
depthstr = "1.0"
ra_center = 0.
dec_center = 0.
tess_magnitude = 10.
tess_depth = 1.0
search_radius_degrees = 2.5/60
status = "Ready"

# Source of coordinates may be tic or eod

center_src = "tic"


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


# Return the Julian date for a given year, month, day, and UTC

def jd(y0,m0,d0,u0):
  k = int(y0)
  m = int(m0)
  i = int(d0)
  utc = u0
  j1 = float(367*k)
  j2 = -1.*float( int( ( 7*(k + int((m+9)/12) ) )/4 ) )
  j3 = float(i + int(275*m/9))
  j4 = 1721013.5 + (utc/24.)
  julian = j1 + j2 + j3 +j4
  return(julian)


# Return the Julian date for a given floating point epoch

def jd_for_epoch(epoch):  
  int_year = int(epoch)
  month  = epoch - float(int_year)
  int_month = int(month)
  day = int_month - float(int_month)
  int_day = int(day)
  julian = jd(int_year, int_month, int_day, 0.)
  return(julian)


# Return a string formatted in dd:mm:ss.sss from degrees or hours 

def float_to_dms_str(invalue):

  negative = False
  if invalue < 0:
    negative = True
    invalue = abs(invalue)
  degrees = invalue
  d = int(degrees)
  minutes  = (degrees - float(d))*60. + 1.e-9
  m = int(minutes)
  seconds = (minutes -float(m))*60. + 1.e-9
  
  
  if negative:
    dms_str = "-%02d:%02d:%06.3f" % (d,m,seconds)
  else:
    dms_str ="%02d:%02d:%06.3f" % (d,m,seconds)
    
  return(dms_str)


# Format floating point degrees into a +/-dd:mm:ss.sss string

def dec_to_dms_str(degrees):
    
  dg = int(abs(degrees))
  subdegrees = abs( abs(degrees) - float(dg) )
  minutes = subdegrees * 60.
  mn = int(minutes)
  subminutes = abs( minutes - float(mn))
  seconds = subminutes * 60.
  ss = int(seconds)
  subseconds = abs( seconds - float(ss) )
  subsecstr = ("%.3f" % (subseconds,)).lstrip('0')
  if degrees > 0:
    dsign = '+'
  elif degrees == 0.0:
    dsign = ' '
  else:
    dsign = '-'
  anglestr = "%s%02d:%02d:%02d%s" % (dsign, dg, mn, ss, subsecstr) 
  return anglestr


# Format floating point right ascension into a +/-dd:mm:ss.sss string

def ra_to_hms_str(invalue):
  
  negative = False
  if invalue < 0:
    negative = True
    invalue = abs(invalue)
  degrees = invalue
  hours = degrees/15.
  hh = int(hours)
  minutes  = (hours - float(hh) + 1.e-9)*60.
  mm = int(minutes)
  seconds = (minutes - float(mm) + 1.e-9)*60.
    
  if negative:
    hms_str = "-%02d:%02d:%06.3f" % (hh,mm,seconds)
  else:
    hms_str ="%02d:%02d:%06.3f" % (hh,mm,seconds)
    
  return(hms_str)
         


# Tk management  


def query_exit():
  # clean up and exit

  if diagnostics_flag:
    print("Closed user interface")
  
  root.destroy()
  exit(1)


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


def query_run():
  global rastr
  global decstr
  global magstr
  global depthstr
  global status
  global reference_file
  global aperture_file

  status ="Running"
  tk_status.set(status)
  rastr = tk_rastr.get()
  decstr = tk_decstr.get()
  magstr = tk_magstr.get()
  depthstr = tk_depthstr.get()
  aperture_file = tk_aperture_file.get()

  make_apertures()
  status ="Done"
  tk_status.set(status)

      
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


def browse_aperture_file():
  global aperture_file
  
  # Open a file menu
  aperture_file = filedialog.asksaveasfilename(filetypes = [("Aperture files", ".apertures"), ("all files",".*")])
  tk_aperture_file.set(aperture_file)


def show_help():
  text = "TIC Stars to AstroImageJ\n\n"
  text = text + "Selects those TIC stars that could "
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
  
 
# Manage the processing with updates

def monitor_process():
  global status
  tk_status.set(status)
  if status == "Running" or status == "Starting":
    query_start()
  root.after(2000, monitor_process)

  
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

# Query the TESS Input Catalog through MAST

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



# Find TIC stars

def find_tics():

  # Create a sky objects counter and an empty sky list  buffer (for sorting)


  # Send the request
  # This is contained in a separate routine to localize the dependency and error handling
  
  tic_json = query_mast_api_tic(ra_center, dec_center, search_radius_degrees)

  # Uncomment for diagnostic
  # print(tic_json)

  # Uncomment to see the fields and data types in the data
  
  # import pprint
  # pprint.pprint(tic_json['fields'])

  nstars =  tic_json['paging']['rowsTotal']
  labels = tic_json['fields']
  
  if nstars < 1:
    sys.exit('No stars were found near  %s  %s ' % (rastr,decstr,))
  elif nstars == 1:
    print(" ")
    print('Found %d star in TIC near %s  %s ' % (nstars, rastr, decstr,))  
    print(" ")
  else:
    print(" ")
    print('Found %d stars in TIC near %s  %s ' % (nstars, rastr, decstr,))
    print(" ")
  
  labels = tic_json['fields']
  stars = tic_json['data']

  # Return the number of stars, column labels and star data as json objects
  
  return nstars, labels, stars
  


# Make the radec file of apertures

# Procedure to query the TIC and generate the star list
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
  # To converting millimag to ppt use 2.51188643150958*np.log10
  tess_dmag = -2.51188643150958*np.log10(tess_depth)

  # Parse date from input
  date_parts = datestr.split('-')
  if len(date_parts) == 3:  
    yr = date_parts[0]
    mo = date_parts[1]
    da = date_parts[2]
    jd_obs = jd(yr, mo, da, 0.)
  else:
    datestr = "2019-01-01"
    jd_obs = 2458486.5
     
  if diagnostics_flag:
    print("Request inputs -- \n")
    print("Target coordinates: ", rastr,  "  ", decstr)
    print("Magnitude requested: ", tess_magnitude)
    print("Transit depth requested: ", tess_depth)
    print("Reference date: ", datestr, "  ", jd_obs)


  # Create a sky objects counter and buffer
  
  nsky = 0
  sky = []

  # Send the request and return a list of star with string elements
  # Use if isinstance(x, type(None)) to test for missing entries
  # Convert to float as needed
  
  nstars, labels, stars  = find_tics()
  
  # Check again that there are stars in these data
  
  if nstars < 1:
    sys.exit('No objects found at  %s  %s ' % (rastr,decstr,))
  
  # Set up proper motion corrections in milli-arcseconds per year
  
  pm_scale = 1. / (1000.)

  # Add stars to the sky list
  #
  # Do this star by star to make a new list that will be sorted after all stars are processed
  # Stars in the list have proper motion set to date of observation
  
  for i in range(nstars):

     
    # Coordinates are ICRS epoch 2000.0

    if isinstance(stars[i]['ra'], type(None)):
      ra_tic = 0.0
    else:
      ra_tic = float(stars[i]['ra'])

    if isinstance(stars[i]['dec'], type(None)):
      dec_tic = 0.0
    else:
      dec_tic = float(stars[i]['dec'])

    if isinstance(stars[i]['ID'], type(None)):
      src_id = ' '
    else:
      src_id = stars[i]['ID']  
       
    if isinstance(stars[i]['Tmag'], type(None)):
      mag_t = 99.0
    else:
      mag_t = float(stars[i]['Tmag'])

    if isinstance(stars[i]['gmag'], type(None)):
      mag_g = 99.0
    else:
      mag_g = float(stars[i]['gmag'])

    if isinstance(stars[i]['rmag'], type(None)):
      mag_r = 99.0
    else:
      mag_r = float(stars[i]['rmag'])
            
    if isinstance(stars[i]['pmRA'], type(None)):
      pm_ra = 0.0
    else:
      pm_ra = float(stars[i]['pmRA'])

    if isinstance(stars[i]['pmDEC'], type(None)):
      pm_dec = 0.0
    else:
      pm_dec = float(stars[i]['pmDEC'])
      
    if isinstance(stars[i]['plx'], type(None)):
      parallax = 0.0
    else:
      pm_dec = float(stars[i]['plx'])
      
    if isinstance(stars[i]['dstArcSec'], type(None)):
      distance = 0.0
    else:
      distance = float(stars[i]['dstArcSec'])


    ref_epoch = 2000.0

    # Update coordinates for proper motion to epoch of observation
    # Proper motion is in mas/yr
    # Parallax is in mas
    # jd_obs is in Julian days
    # ref_epoch is in calendar years
    # ra and dec are in degrees
    
    # Find the jd for the epoch of TIC data from the information returned by the search
    jd_ref = jd_for_epoch(ref_epoch)
    
    # Find the appropriate delta_t for PM of the center based on the source of coordinates 
    
    # Assume coordinates provided for the center are TIC entries for J2000.0 by default
    
    delta_t_center = (jd(2000,1,1,0.5) - jd_ref) / 365.25 
    
    # Check inputs and set delta_t_center so that center coordinates will be on the EOD
    # Comparisons, sorting, and cataloging are all done for the EOD
    
    # A TIC entry is for 2000.0 or JD 2451544
    # Table output is for EOD

    # All calculations are in the same coordinate reference system apart from proper motion
    # Parallax is neglected
    
    if center_src == "tic":
      delta_t_center = (jd_obs - jd(2000,1,1,0.5)) / 365.25    
        
    if center_src == "eod":  
      delta_t_center = 0.

    # Set delta_t so that catalog entries will be advanced in PM to the date of observation (EOD)
    
    delta_t = (jd_obs - jd_ref) / 365.25 
        
    # Add proper motion in degrees to the TIC coordinates and to the center coordinates so they match the date of observation
    # Add delta_ra_center and delta_dec_center to the T1 coordinates to compare to TIC list
    # delta_ra and delta_dec have pm to the date of observation  for return in the radec file


    delta_ra_center = pm_ra * pm_scale * delta_t_center
    delta_dec_center = pm_dec * pm_scale * delta_t_center
    delta_ra = pm_ra * pm_scale * delta_t
    delta_dec = pm_dec * pm_scale * delta_t
    
    # Adjust the TIC catalog entry to have proper motion for the date of observation
    
    ra = ra_tic + (delta_ra/3600.)
    dec = dec_tic + (delta_dec/3600.)
    
    # Test a new center with proper motion of this star
    
    ra_center_test = ra_center + (delta_ra_center/3600.)
    dec_center_test = dec_center + (delta_dec_center/3600.)
    
                
    # Entries are already selected for  separation from target based on TIC coodinates
    # Only include those within this distance that can affect the TESS photometry

    # Use the TIC entry for calculated TESS magnitude
    star_magnitude = mag_t
    
    # Set the selection flag 
    selected_flag = (star_magnitude < (tess_magnitude + tess_dmag + 0.5))
 
    # Build the ordered output database for selected stars       
    if selected_flag: 
                
      # Find how much fainter this star is in magnitudes than the target
      # The bigger these number the more unlikely it is to be the target
      # Use abs because these are for selection criteria
      
      delta_mag_tic = abs(star_magnitude - tess_magnitude)
      
      # Find how far this star is from the target position now
      # This may be different from the entry in the catalog
      # Use abs just in case something goes negative here
      
      delta_theta_rad = np.arccos(np.sin(np.radians(dec))*np.sin(np.radians(dec_center_test)) + np.cos(np.radians(dec))*np.cos(np.radians(dec_center_test))*np.cos(np.radians(ra - ra_center_test)))              
      delta_theta = abs(3600.*np.degrees(delta_theta_rad))
         
      
      # Create a selection ranking for ordering the aperture list from 0.
      uncertainty_theta = 8.
      uncertainty_mag_tic = 1.
      if delta_theta > uncertainty_theta:
        rank = delta_theta   
      elif delta_mag_tic <= uncertainty_mag_tic:
        rank  = delta_mag_tic/100.
      elif (delta_mag_tic > uncertainty_mag_tic):
        rank = delta_mag_tic/100.
      else:
        rank = delta_theta
            
           
      # Add this selected star to the sky list with ra, dec, magnitude,  delta mag_tic,  delta_theta, and rank
      
      sky.append((ra, dec, star_magnitude, delta_theta, delta_mag_tic, rank))
      nsky = nsky + 1
      
  # Create a numpy array to make sorting easier
  
  sky_star_array = np.array(sky, dtype=np.float32)
  
  if diagnostics_flag:
    print("Selected: ", nsky, "  |  Sky list length: ", len(sky), "  |  Star array size: ", sky_star_array.size, "  |  Star array shape: ", sky_star_array.shape)
        
  # Sort by rank to make the  target star first
  
  sky_star_array = sky_star_array[sky_star_array[:,5].argsort()]
  
  # Alert the user to the content of new apertures file
  
  print("Identified ", nsky, " out of ",  nstars,  " after culling the TIC field.")
  print(" ")

  if diagnostics_flag:
    print(" ")
    print("   #     del_theta (arcsec)    del_mag_tic    rank\n")
    print(" ")

    # List the stars in rank order from which the AIJ apertures will be made
    for i in range(nsky):  
      print("%4d  %8.1f              %8.3f        %8.3f" % (i, sky_star_array[i,3], sky_star_array[i,4], sky_star_array[i,5]) )

    print(" ")
  
  # Copy the first two columns with ra and dec from columns "0" and "1" of the sorted array
  # Create a new array for the ra, dec, and magnitude list
  
  sky_coord_array = sky_star_array[:,0:3]  
  
    
  # Open the file
  aperture_fp = open(aperture_file, 'w')
  
  # Write data line by line
  # RA in sexagesimal hours
  # Dec in sexagesimal degrees
  # TESS magnitude based on selection 
  
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
    if i == 0:
      skyline = "%s,  %s, 0, 1, %6.3f  \n" % (ra_star_str, dec_star_str, mag_star) 
    else:
      skyline = "%s,  %s, 0, 0, %6.3f  \n" % (ra_star_str, dec_star_str, mag_star) 
    aperture_fp.write(skyline)

  # Close the output file
  aperture_fp.close()
  print("Saved apertures in ", aperture_file)
  print(" ")





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
ttk.Label(mainframe, text="Query MAST TIC for AstroimageJ").grid(column=1, row=0, sticky=tk.W, columnspan=3)


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




