#!/usr/local/bin/python3

# John Kielkopf 
# kielkopf@louisville.edu
# Copyright 2021
# Licensed under terms of the MIT license


# Version: 2021-05-12
#   
#  Use
#  ./query_mast_tic_crossmatch.py 06:32:09.3 +04:49:24.7
#

"""

  Send a request to MAST for a json table of TIC stars matching RA and Dec
  
    Input:
      
      ra_str 
      dec_str
      
    Output:
      Console list of nearest neighbor properties
      New line in tic_stars.csv  
  
  Return the nearest TIC ID and selected catalog information

"""  

import os            # for system environment
import sys	     # for system connections
import numpy as np   # managing the data
import time          # used by MAST API 
from time import gmtime, strftime, time  # for utc
import re            # for manipulating strings

import json          # MAST API uses json data
import requests      # used to get data from MAST
from urllib.parse import quote as urlencode  

global ra_str
global dec_str
global ra_center
global dec_center


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
         

# Check for validitiy of RA and Dec strings
# Parse coordinate strings into degrees for center of search
# Accepts hh:mm:ss dd:mm:ss  or ddd.ddd ddd.ddd formats
# Set global ra_center and dec_center

def parse_coordinates():
  
  global ra_center
  global dec_center
  
  rahr = 0.
  ramin = 0.
  rasec = 0.
  decdeg = 0.
  decmin = 0.
  decsec = 0.

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


# Requests a TIC ID for a given RA and Dec

def tic_crossmatch(query_ra, query_dec):

  # This is a json object
  crossmatch_input = {"fields":[{"name":"ra","type":"float"},
    {"name":"dec","type":"float"}],
    "data":[{"ra":query_ra,"dec":query_dec}]}
  
  request =  {
    "service":"Mast.Tic.Crossmatch",
    "data":crossmatch_input,
    "params":{
      "raColumn":"ra",
      "decColumn":"dec",
      "radius":0.001
    },
    "format":"json"
    }

  headers,out_string = mast_query(request)

  out_data = json.loads(out_string)

  return out_data


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


# Find TIC stars

def find_tics():

  # Create a sky objects counter and an empty sky list  buffer (for sorting)

  nsky = 0
  sky = []

  # Send the request
  # This is contained in a separate routine to localize the dependency and error handling
  
  tic_json = tic_crossmatch(ra_center, dec_center)

  # Uncomment for diagnostic
  # print(tic_json)

  # Uncomment to see the fields in the data
  
  #import pprint
  #pprint.pprint(tic_json['fields'])

  ntics =  tic_json['paging']['rowsTotal']
  
  if ntics < 1:
    sys.exit('No stars were found near  %s  %s ' % (ra_str,dec_str,))
  elif ntics == 1:
    print('MAST found %d star in TIC near %s  %s ' % (ntics, ra_str, dec_str,))  
  else:
    print('MAST found %d stars in TIC near %s  %s ' % (ntics, ra_str, dec_str,))
  
  print("")

  sky.append(("Delta Theta",
    "RA hhmmss",
    "Dec ddmmss",
    "RA",
    "Dec",
    "PM RA",
    "PM DEC",
    "Parallax",   
    "TIC",
    "TYC",
    "HIP",
    "Gaia",
    "TWOMASS",
    "T Mag",
    "B Mag",
    "V Mag",
    "u Mag",
    "g Mag",
    "r Mag",
    "i Mag",
    "z Mag",
    "J Mag",
    "H Mag",
    "K Mag"    
    ))
                           
  # Add the nearest star to the list

  tic_stars = tic_json['data']
  tic_star = tic_stars[0]
  ra = tic_star['ra']
  dec = tic_star['dec']
  ra_hhmmss = ra_to_hms_str(ra)
  dec_ddmmss = dec_to_dms_str(dec)
  delta_theta = tic_star['dstArcSec']
  pm_ra = tic_star['pmRA']
  pm_dec = tic_star['pmDEC']
  parallax = tic_star['plx']
  tic_id = tic_star['MatchID']
  tyc_id = tic_star['TYC']
  hip_id = tic_star['HIP']
  gaia_id = 'DR2 ' + tic_star['GAIA']
  twomass_id = tic_star['TWOMASS']
  t_mag = tic_star['Tmag']
  B_mag = tic_star['Bmag']
  V_mag = tic_star['Vmag']
  u_mag = tic_star['umag']
  g_mag = tic_star['gmag']
  r_mag = tic_star['rmag']
  i_mag = tic_star['imag']
  z_mag = tic_star['zmag']
  j_mag = tic_star['Jmag']
  h_mag = tic_star['Hmag']
  k_mag = tic_star['Kmag']
                         
  sky.append((delta_theta,
    ra_hhmmss,
    dec_ddmmss,
    ra,
    dec,
    pm_ra,
    pm_dec,
    parallax,
    tic_id,
    tyc_id,
    hip_id,
    gaia_id,
    twomass_id,
    t_mag,
    B_mag,
    V_mag,
    u_mag,
    g_mag,
    r_mag,
    i_mag,
    z_mag,
    j_mag,
    h_mag,
    k_mag    
    ))

  # Return the TIC list
  
  return sky



# Parse the  command line

if len(sys.argv) == 3:
  ra_str = sys.argv[1]
  dec_str = sys.argv[2]
else:
  print(" ")
  print("Usage: query_mast_tic_crossmatch.py ra dec")
  print(" ")
  sys.exit("Crossmatch coordinates to TIC ID\n")


# Remove non-numeric characters excepting delimiters from coordinate strings 

ra_str = re.sub(r'([^-+\.\:0-9])+', '', ra_str).strip()
dec_str = re.sub(r'([^-+\.\:0-9])+', '', dec_str).strip()


# Now acknowledge the request

print ("")
print ("Request to be sent for TIC match to:")
print ("RA = ", ra_str)
print ("Dec = ", dec_str)
print ("")
print ("Processing ... ")
print ("")

# Parse coordinates based on the style of the input

parse_coordinates()

# Query MAST and generate the TIC list
# The first one should be the nearest neighbor ID

stars = find_tics()
nrows = len(stars)
ncols = len(stars[0])

tic_stars_file_exist_flag = os.path.isfile("tic_stars.csv")

stars_fp = open("tic_stars.csv", 'a')

# First row will be column labels for a new file

if not tic_stars_file_exist_flag:
  starline =""
  for i in range(ncols):
    entry = str(stars[0][i])
    if i < ncols - 1 :
      starline = starline + str(stars[0][i]) + "\t"
    else:
      starline = starline + str(stars[0][i]) + "\n"
  stars_fp.write(starline)

# Subsquent rows will be the stars returned from the crossmatch

for j in range(1, nrows, 1):
  starline =""
  for i in range(ncols):
    entry = str(stars[j][i])
    if i < ncols - 1 :
      starline = starline + str(stars[j][i]) + "\t"
    else:
      starline = starline + str(stars[j][i]) + "\n"
  stars_fp.write(starline)


stars_fp.close()

# Write out the first star in human readable style

for i in range(ncols):
 label = str(stars[0][i])
 entry = str(stars[1][i])
 print(label, ": ", entry)

print("")  

exit()


