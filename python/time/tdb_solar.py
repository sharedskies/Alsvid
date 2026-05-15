#!/usr/local/bin/python3


"""

  Find the barycentric dynamical time TDB from JD UTC for given JD
    referenced to the center of the Sun.
    
  This version is for using the Sun as an velocity standard 

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
  
    2021-12-22
    Version 1.0
    
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

from astropy.time import Time
from barycorrpy import JDUTC_to_HJDTDB


diagnostics_flag = False

# Set environment variables to use a specific location for this code's files

# os.environ["HOME"] = "/home/user/astropy/data/"
# os.environ["XDG_CONFIG_HOME"] = "/home/user/astropy/data/"
# os.environ["XDG_CACHE_HOME"] = "/home/user/astropy/data/"

if len(sys.argv) > 2:

  # Provide instructions
  
  print(" ")
  sys.exit("Usage: tdb_solar.py request_file.txt\n")
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
  print("jd=           comma separated list of JDs to be added to TBASE") 
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
  print("jdbase=       base JD to which JDs are added where the default is 0.0") 
  print("")
  sys.exit("\n")   

# Two different ways of finding the cwd

# current_working_dir = sys.argv[-1]
# current_working_dir = os.path.expanduser('~')     

request_fp = open(request_file_name,"r")
if not request_fp:
  print("Edit a request file. Enter its name on the command line.")
  exit(1)

# All entries are strings keyed in the config file

jd_base_str = "0.0"
jd_base = 0.0
jd_list_str = ""
jd_list = []
latitude_str = "-27.798217"
latitude_deg = -27.798217
longitude_str = "151.855640"
longitude_deg = 151.855640
elevation_str = "682.0"
elevation_m = 682.0

ephemeris = "de430"
#ephemeris = "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/a_old_versions/de405.bsp"

# These are required to obtain useful output

# 'jd'           comma separated list of JDs to be added to TBASE 
# 'ra'           hh:mm:ss or float degrees   
# 'dec'          dd:mm:ss or float degrees  

# These will default to hard-coded Minerva Australis at Mt. Kent, Queensland

# 'latitude'       degrees          defaults to Minerva Australis
# 'longitude'      degrees + east   defaults to Minerva Australis
# 'elevation'      meters           defaults to Minerva Australis

# These will default to useful values if not supplied

# 'epoch'        JD where the default is 2451545.0
# 'jdbase'       base JD to which JDs are added where the default is 0.0


# Obtain the entries from the request file

for newline in request_fp:
  items = newline.split("=")
  if items[0].strip() == "jd" :
    jd_str = str(items[1].strip())
  if items[0].strip() == "latitude" :
    latitude_str = str(items[1].strip())
  if items[0].strip() == "longitude" :
    longitude_str = str(items[1].strip())
  if items[0].strip() == "elevation" :
    elevation_str = str(items[1].strip())
    rv_str = str(items[1].strip())    
  if items[0].strip() == "jdbase" :
    jd_base_str = str(items[1].strip())    

# Convert strings to values

latitude_str = re.sub(r'([^-+\.\:0-9])+', '',  latitude_str).strip()
longitude_str = re.sub(r'([^-+\.\:0-9])+', '', longitude_str).strip()
elevation_str = re.sub(r'([^-+\.\:0-9])+', '', elevation_str).strip()
jd_base_str = re.sub(r'([^-+\.\:0-9])+', '',   jd_base_str).strip()

latitude_deg = float(latitude_str)
longitude_deg = float(longitude_str)
elevation_m = float(elevation_str)
jd_base = float(jd_base_str)


# Parse date string for multiple dates

jd_str = re.sub(r'([^-+\.\:0-9\,])+', '', jd_str).strip().split(",")
jd_list = []

for jd_item in jd_str:  
  jd = float(jd_item)  
  jd = jd + jd_base
  jd_list.append(jd)


hjd_tdbs = JDUTC_to_HJDTDB(JDUTC=jd_list,
  lat = latitude_deg,
  longi = longitude_deg,
  alt = elevation_m,
  ephemeris = ephemeris)


# The input request has been parsed

if diagnostics_flag:
  print("")
  print("JDs: ", jd_str, jd_list)
  print("Latitude: ", latitude_str, latitude_deg)
  print("Longitude: ", longitude_str, longitude_deg)
  print("Elevation: ", elevation_str, elevation_m)
  print("Ephemeris: ", ephemeris)
  print("")


# Export the results

print("Barycentric dynamical time for observing the center of the Sun: ")
print ("")

if diagnostics_flag:
  print(hjd_tdbs)

for n in range(len(hjd_tdbs[0])):
  print(jd_list[n], "  ", hjd_tdbs[0][n])

print ("")
print ("")


exit()



