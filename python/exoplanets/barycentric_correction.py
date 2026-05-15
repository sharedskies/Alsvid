#!/usr/local/bin/python3


"""

  Use barycorrpy to find barycentric radial velocity corrections

  Edit these lines for your installation.  They provide for saving
  the reference data in a single location you can control.  
    
  
  By default astropy uses .astropy in the user's home dirctory for
  configuration and cache files.  This changes the location.
  
    os.environ["HOME"] = "/home/user/astropy/"

  These will define where cache and data are kept, but those can be
  temporary files even when these are set.
  
    os.environ["XDG_CONFIG_HOME"] = "/home/user/astropy/data/"
    os.environ["XDG_CACHE_HOME"] = "/home/user/astropy/data/"

  Usage:
  
    Prepare a file with the prescribed data and run
    
      barycentric_correction.py file.txt    

  Reference:
  
    Barycorrpy on github -  https://github.com/shbhuk/barycorrpy   and its sources 
    S. Kanodia and J. Wright - https://doi.org/10.3847/2515-5172/aaa4b7
    https://github.com/shbhuk/barycorrpy/wiki
  
  Author:
  
    John Kielkopf 
    kielkopf at louisville dot edu
    
  Version:
  
    2026-05-14
    Version 2.3
    
  License:
  
    MIT License (MIT) 
         

"""

import os
import sys
import fnmatch
import string
import re
import requests

import numpy as np
import datetime
import urllib
import math

from barycorrpy import get_BC_vel
from barycorrpy import JDUTC_to_BJDTDB

diagnostics_flag = False

# Set environment variables to use a specific location for this code's files

# os.environ["HOME"] = "/home/user/astropy/data/"
# os.environ["XDG_CONFIG_HOME"] = "/home/user/astropy/data/"
# os.environ["XDG_CACHE_HOME"] = "/home/user/astropy/data/"

if len(sys.argv) > 2:

  # Provide instructions
  
  print(" ")
  sys.exit("Usage: barycentric_correction.py request_file.txt\n")
  exit()

elif len(sys.argv) == 2:

  # Use a command line data directory

  request_file_name = sys.argv[1]

else:
  print("Use a file with these required entries on the command line.")
  print("")
  print("")  
  print("These are required to obtain useful output")
  print("")
  print("jd=           comma separated list of JDs (UTC) to be added to TBASE") 
  print("ra=           hh:mm:ss or float degrees")   
  print("dec=          dd:mm:ss or float degrees")  
  print("")
  print("These will default to hard-coded Minerva Australis at Mt. Kent, Queensland")
  print("")
  print("latitude=     degrees defaults to Minerva Australis")
  print("longitude=    degrees + east  defaults to Minerva Australis")
  print("")
  print("These will default to useful values if not supplied")
  print("")
  print("elevation=    meters    where the default is 0.")
  print("pmra=         milli-arcseconds per year    where the default is 0.")
  print("pmdec=        milli-arcseconds per year    where the default is 0.")
  print("parallax=     milli-arcseconds    where the default is 0.")
  print("rv=           low precision m/s where the default is 0.")
  print("zmeasure=     precision v/c  where the default is 0.")
  print("epoch=        JD where the default is 2451545.0")
  print("jdbase=       base JD to which JDs are added where the default is 0.0") 
  print("")
  sys.exit("\n")   

# Two different ways of finding the cwd

# current_working_dir = sys.argv[-1]
# current_working_dir = os.path.expanduser('~')     

request_fp = open(request_file_name,"r")
if not request_fp:
  print("Edit a request file enter its name on the command line.")
  exit(1)

# All entries are strings keyed in the config file

jd_base_str = "0.0"
jd_base = 0.0
jd_list_str = ""
jd_list = []
ra_str = "0.0"
ra_deg = 0.0
dec_str = "0.0"
dec_deg = 0.0
latitude_str = "-27.798217"
latitude_deg = -27.798217
longitude_str = "151.855640"
longitude_deg = 151.855640
elevation_str = "682.0"
elevation_m = 682.0
pmra_str = "0"
pmra_mas = 0.
pmdec_str = "0"
pmdec_mas = 0.
parallax_str = "0"
parallax_mas = 0.
rv_str = "0"
rv_mps = 0.
zmeasure_str = "0"
zmeasure = 0.
epoch_str = "2451545.0"
epoch = 2451545.0

#ephemeris = "de430"
ephemeris = "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/a_old_versions/de405.bsp"
# Check for validity of RA and Dec strings
# Parse coordinate strings into degrees for center of search

def parse_coords():
  
  global ra_deg
  global dec_deg
  
  rahr = 0.0
  ramin = 0.0
  rasec = 0.0
  decdeg = 0.0
  decmin = 0.0
  decsec = 0.0

  # Test for empty strings

  if (ra_str == ""):
    print ("Missing right ascension</b>")
    print ("")
    exit()

  if (dec_str == ""):
    print ("Missing declination")
    print ("")
    exit()

  # Treat RA based on content 
  # If RA has : then it is hexasegismal hours and otherwise it is decimal degrees
  
  if ':' in ra_str:
    rahrstr, raminstr, rasecstr = ra_str.split(":")
    rahr = abs(float(rahrstr))
    ramin = abs(float(raminstr))
    rasec = abs(float(rasecstr))
    if float(rahrstr) < 0.0:
      rasign = -1.0
    else:
      rasign = +1.0
    ra_deg = rasign*(rahr + ramin/60.0 + rasec/3600.)*15.0
  else:  
    try:
      ra_deg = float(ra_str)
    except:
      print ("Cannot parse right ascension entry.")
      print ("")
      exit()    
       

  if ':' in dec_str:
    decdegstr, decminstr, decsecstr = dec_str.split(":")
    decdeg = abs(float(decdegstr))
    decmin = abs(float(decminstr))
    decsec = abs(float(decsecstr))
    if float(decdegstr) < 0.0:
      decsign = -1.
    elif decdegstr[0] == "-":
      decsign = -1.  
    else:
      decsign = +1.
    dec_deg = decsign*(decdeg + decmin/60.0 + decsec/3600.0)
  else:  
    try:
      dec_deg = float(dec_str) 
    except:
      print ("Cannot parse declination entry.")
      print ("")      
      exit()
  return()          




# Parse the fields using these keys matching those from Jason Eastman's OSU website

# These are required to obtain useful output

# 'jd'           comma separated list of JDs (UTC) to be added to TBASE 
# 'ra'           hh:mm:ss or float degrees   
# 'dec'          dd:mm:ss or float degrees  

# These will default to hard-coded Minerva Australis at Mt. Kent, Queensland

# 'latitude'       degrees defaults to Minerva Australis
# 'longitude'      degrees + east  defaults to Minerva Australis

# These will default to useful values if not supplied

# 'elevation'    meters    where the default is 0.
# 'pmra'         milli-arcseconds per year    where the default is 0.
# 'pmdec'        milli-arcseconds per year    where the default is 0.
# 'parallax'     milli-arcseconds    where the default is 0.
# 'zmeasure'     v/c  where the default is 0.
# 'epoch'        JD where the default is 2451545.0
# 'jdbase'       base JD to which JDs are added where the default is 0.0


# Obtain the entries from the request file

for newline in request_fp:
  items = newline.split("=")
  if items[0].strip() == "jd" :
    jd_str = str(items[1].strip())
  if items[0].strip() == "ra" :
    ra_str = str(items[1].strip())
  if items[0].strip() == "dec" :
    dec_str = str(items[1].strip())
  if items[0].strip() == "latitude" :
    latitude_str = str(items[1].strip())
  if items[0].strip() == "longitude" :
    longitude_str = str(items[1].strip())
  if items[0].strip() == "elevation" :
    elevation_str = str(items[1].strip())
  if items[0].strip() == "pmra" :
    pmra_str = str(items[1].strip())
  if items[0].strip() == "pmdec" :
    pmdec_str = str(items[1].strip())
  if items[0].strip() == "parallax" :
    parallax_str = str(items[1].strip())
  if items[0].strip() == "rv" :
    rv_str = str(items[1].strip())    
  if items[0].strip() == "zmeasure" :
    zmeasure_str = str(items[1].strip())
  if items[0].strip() == "jdbase" :
    jd_base_str = str(items[1].strip())
  if items[0].strip() == "epoch" :
    epoch_str = str(items[1].strip())
    

# Convert strings to values

parse_coords()

latitude_str = re.sub(r'([^-+\.\:0-9])+', '',  latitude_str).strip()
longitude_str = re.sub(r'([^-+\.\:0-9])+', '', longitude_str).strip()
elevation_str = re.sub(r'([^-+\.\:0-9])+', '', elevation_str).strip()
pmra_str = re.sub(r'([^-+\.\:0-9])+', '',      pmra_str).strip()
pmdec_str = re.sub(r'([^-+\.\:0-9])+', '',     pmdec_str).strip()
parallax_str = re.sub(r'([^-+\.\:0-9])+', '',  parallax_str).strip()
rv_str = re.sub(r'([^-+\.\:0-9])+', '',        rv_str).strip()
zmeasure_str = re.sub(r'([^-+\.\:0-9])+', '',  zmeasure_str).strip()
jd_base_str = re.sub(r'([^-+\.\:0-9])+', '',   jd_base_str).strip()
epoch_str = re.sub(r'([^-+\.\:0-9])+', '',     epoch_str).strip()

latitude_deg = float(latitude_str)
longitude_deg = float(longitude_str)
elevation_m = float(elevation_str)
pmra_mas = float(pmra_str)
pmdec_mas = float(pmdec_str)
parallax_mas = float(parallax_str)
rv_mps = float(rv_str)
zmeasure = float(zmeasure_str)
jd_base = float(jd_base_str)
epoch = float(epoch_str)


# Parse date string for multiple dates

jd_str = re.sub(r'([^-+\.\:0-9\,])+', '', jd_str).strip().split(",")
jd_list = []

for jd_item in jd_str:  
  jd = float(jd_item)  
  jd = jd + jd_base
  jd_list.append(jd)


bc_rvs = get_BC_vel(JDUTC=jd_list,
  ra = ra_deg,
  dec = dec_deg,
  lat = latitude_deg,
  longi = longitude_deg,
  alt = elevation_m,
  pmra = pmra_mas,
  pmdec = pmdec_mas,
  px = parallax_mas,
  rv = rv_mps,
  zmeas = zmeasure,
  epoch = epoch,
  ephemeris = ephemeris)

tdbs = JDUTC_to_BJDTDB(JDUTC=jd_list,
  ra = ra_deg,
  dec = dec_deg,
  lat = latitude_deg,
  longi = longitude_deg,
  alt = elevation_m,
  pmra = pmra_mas,
  pmdec = pmdec_mas,
  px = parallax_mas,
  rv = rv_mps,
  epoch = epoch,
  ephemeris = ephemeris)


# The input request has been parsed

if diagnostics_flag:
  print("")
  print("RA = ", ra_str, ra_deg)
  print("Dec = ", dec_str, dec_deg)
  print("JDs (UTC): ", jd_str, jd_list)
  print("Latitude: ", latitude_str, latitude_deg)
  print("Longitude: ", longitude_str, longitude_deg)
  print("Elevation: ", elevation_str, elevation_m)
  print("Proper motion RA: ", pmra_str, pmra_mas)
  print("Proper motion Dec: ", pmdec_str, pmdec_mas)
  print("Parallax: ", parallax_str, parallax_mas)
  print("Radial velocity: ", rv_str, rv_mps)
  print("Z: ", zmeasure_str, zmeasure)
  print("Epoch: ", epoch_str, epoch)
  print("")


# Export the results

print("Barycentric radial velocities [m/s]: ")
print ("")

if diagnostics_flag:
  print(bc_rvs)
  print(tdbs)
print("JDUTC               BJDTDB              BCRV (m/s)")         
for n in range(len(bc_rvs[0])):
  print("{:16.8f}".format(jd_list[n]), "  ", "{:16.8f}".format(tdbs[0][n]), "  ", "{:9.3f}".format(bc_rvs[0][n]))

print ("")
print ("")


exit()



