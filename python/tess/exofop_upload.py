#!/usr/local/bin/python3

#  Author: Karen Collins
#    Version 20191013
#      Script to upload files to ExoFOP TESS
#
#  Modified by: John Kielkopf
#    Version: 20191117
#      Fixed skip of camera_filter in config file reader
#      Changed duration_hrs to duration_min
#      Addted TOI prefix to uploaded toi number
#    Version: 20191116
#      Executable script using local Python 3
#      Lower case file names
#      Variable names with underscore rather than camelCase
#      Removed bell
#      Indentation 2 spaces
#      Use a preferences file in the current directory
#    Version: 20191205
#      Improved management of TOI entry
#    Version: 20200711
#      Searched for hidden tabs
#    Version: 20221208
#      Added 'tid' : tic to the payload as recommend by Mike Lund 2022-09-30
        

"""

  Upload a directory of files to ExoFOP TESS

  Usage: exofop_upload.py  in the directory to upload
  
  Requirements: 
  
    exofop.config  in the current directory
    
    Configuration file contains lines for the upload parameters
    

    upload_files_flag = True
    add_new_series_flag = True
    username = ********
    password = ********
    observation_date = 
    observation_tag = 
    tic = 
    toi = 
    fwhm_arcsec = 2.0
    photap_px = 15
    duration_min = 
    n_images = 
    delta_mag = 
    transit_coverage = Full
    public_note = Transit and NEB check
    telescope_id =  Moore CDK20N
    telap_m = 0.5
    scale_arcsec = 0.536
    camera_id = STX 16803
    camera_filter = rp

    Lines in the configuration file may be commented out with a #
    User will be asked for missing items before upload
  
"""

import os
import sys
import fnmatch
import string
import re
import requests

if len(sys.argv) > 2:

  # Provide instructions
  
  print(" ")
  sys.exit("Usage: exofop_upload.py [data_directory]\n")
  exit()

elif len(sys.argv) == 2:

  # Use a command line data directory

  data_dir = sys.argv[1]

else:

  # Use the current directory for data

  data_dir = sys.argv[-1]    

# Two different ways of finding the cwd

# current_working_dir = sys.argv[-1]
# current_working_dir = os.path.expanduser('~')     

config_file_name = "exofop.config"
config_fp = open(config_file_name,"r")
if not config_fp:
  print("Edit an exofop.config file for this directory.")
  exit(1)

# All entries are strings keyed in the config file

# Set to True to upload 
# Set to False to suppress actual upload (good for testing file names and code)
# This flag defaults to False when the configuration file is read

upload_files_flag = False
  

# Set to True  to create a new time series summary on ExoFOP TESS
# Must do this for the first upload of a data set
# Set to False to use an existing time series
# This flag defaults to False when the configuration file is read

add_new_series_flag = False

# Fill in entries here you do not want to update in a configuration file
#  or be prompted for when the program runs

# For example, you could insert the user and password  to be used here
#  or put them in the configuration file
#  or leave blank to be asked for them when the program runs

username = "kielkopf"
password = "bSifU6rS"
observation_date = ""
observation_tag = ""
tic = ""
toi = ""
fwhm_arcsec = "2.0"
photoap_px = "15"
duration_min = ""
n_images = ""
delta_mag = ""
transit_coverage = "Full"
public_note = "Transit and NEB check"
telescope_id = " Moore CDK20N"
telap_m = "0.5"
scale_arcsec = "0.536"
camera_id = "STX 16803"
camera_filter = "rp"


def number_str(entry):
  # Use re to find only the number 
  # Works with or without a decimal
  # This would also include a + or -
  #   re.findall(r"[-+]?\d*\.\d+|\d+",str(entry.strip()))
  # Returns the number as a string
  
  filtered_entry = re.findall(r"\d*\.\d+|\d+",str(entry.strip()))
  
  # The list must have only 1 entry to be unambiguous

  if len(filtered_entry) == 1:
    return(filtered_entry[0])
  else:
    return("")
      
   
  return(filtered_entry)


def check_entries():
  global username, password, tic, toi, fwhm_arcsec
  global duration_min, n_images, delta_mag
  global photoap_px, camera_filter
  global transit_coverage, public_note, telescope_id, telap_m
  global scale_arcsec, scale_arcsec, camera_id 
  global observation_tag, observation_date

  # Test all the entries and return true if they are not empty
  # Return false if any entry needed an update
  # Rerun if false to check again

  # username: ExoFOP TESS user
  # password: ExoFOP TESS password
  # observation_tag: Required ExoFOP TESS tag for this new observation
  # tic: Input number only
  # toi: Input number only or -1 for no entry
  # observation_date: yyyy-mm-dd
  # fwhm_arcsec: Seeing profile
  # photap_px: Aperture radius in pixels
  # duration_min: Observation duration in minutes
  # n_images: Number of images in entire dataset
  # delta_mag: Difference to faintest cleared NEB
  # transit_coverage: one of "Full" "Ingress" "Egress" "Out of Transit"
  # public_note: On ExoFOP can be seen without login
  # telescope_id: Descriptive unique identification
  # telap_m: Diameter in meters
  # scale_arcsec:  Single pixel on sky in arcseconds
  # camera_id: Descriptive detector or manufacturer code
  # camera_filter: Filter identifier such as gp, rp, ip, zp, U, B, V, R, I

  
  return_flag = True

  if username == "":
    return_flag = False
    entry = input("Enter ExoFOP TESS username: ")
    username = str(entry.strip())

  if password == "":
    return_flag = False
    entry = input("Enter ExoFOP TESS password: ")
    password = str(entry.strip())

  if observation_tag == "":
    return_flag = False
    entry = input("Enter observation tag yyyymmdd_user_description_n: ")
    entry_fields = entry.split("_")
    if len(entry_fields) != 3:
      print("")
      print("Skipping observation tag  because it must be yyyymmdd_user_description_n: ")
      observation_tag = ""
    else:
      # Now check components for sensible content 
      observation_tag = str(entry.strip())

  if observation_date == "":
    return_flag = False
    entry = input("Enter observation date yyyy-mm-dd: ")
    entry_fields = entry.split("_")
    if len(entry_fields) != 3:
      print("")
      print("Skipping date because it must be yyyy-mm-dd: ")
      observation_date = ""
    else:
      # Now check yyyy mm dd for sensible numbers 
      observation_date = str(entry.strip())

  if tic == "":
    return_flag = False
    entry = input("Enter TIC number only: ")
    tic = str(entry.strip()) 
    
    # For uploading the tic entry is only the number
    tic = number_str(tic)   
     
  if toi == "":
    return_flag = False
    entry = input("Enter TOI number nnnn.nn  or space for no entry: ")
    
    # For uploading the toi entry is TOInnnn.nn
    # Regardless of the entry take the number part only
    toi = str(entry.strip())
    toi = number_str(toi)            
    if toi == "": 
      # User selected no entry     
      toi = "TOI"      
    elif "." in toi:
      # If there is the required dot format, treat appropriately
      toi = "TOI"+toi
    else:
      # We do not have it right yet so clear it and try again
      toi = ""    
            
  if fwhm_arcsec == "":
    return_flag = False
    entry = input("Enter seeing profile FWHM (arcsec): ")
    fwhm_arcsec = str(entry.strip())
    fwhm_arcsec = number_str(fwhm_arcsec)
    
  if photoap_px == "":
    return_flag = False
    entry = input("Enter photometric aperture radius (px): ")
    photoap_px = str(entry.strip())
    photoap_px = number_str(photoap_px)
    
  if duration_min == "":
    return_flag = False
    entry = input("Enter observation duration (minutes): ")
    duration_min = str(entry.strip())
    duration_min = number_str(duration_min)
    
  if n_images == "":
    return_flag = False
    entry = input("Enter number of images: ")
    n_images = str(entry.strip())
    n_images = number_str(n_images)
    
  if delta_mag == "":
    return_flag = False
    entry = input("Enter delta mag for NEB search: ")
    delta_mag = str(entry.strip())
    delta_mag = number_str(delta_mag)
    
  if transit_coverage == "":
    return_flag = False
    print ('Use one of  "Full"  "Ingress"  "Egress"  "Out of Transit" ')
    entry = input("Enter transit coverage: ")
    entry_str = str(entry.strip())

    # Use one of the allowed entries
    
    if "Full" in entry_str:
      transit_coverage = "Full"
    elif "full" in entry_str:
      transit_coverage = "Full"
    elif "Ingress" in entry_str:
      transit_coverage = "Ingress"
    elif "ingress" in entry_str:
      transit_coverage = "Ingress"
    elif "Out" in entry_str:
      transit_coverage = "Out of Transit"
    elif "out" in entry_str:
      transit_coverage = "Out of Transit"
                
  if public_note == "":
    return_flag = False
    print("Add a public note.  Enter a space to have no visible note.")
    entry = input("Enter public note: ")
    public_note = str(entry.strip())

  if telescope_id == "":
    return_flag = False
    entry = input("Enter telescope ID text: ")
    telescope_id = str(entry.strip())

  if telap_m == "":
    return_flag = False
    entry = input("Enter telescope aperture (m): ")
    telap_m = str(entry.strip())
    telap_m = number_str(telap_m)
        
  if scale_arcsec == "":
    return_flag = False
    entry = input("Enter images scale arcsecond/pixel): ")
    scale_arcsec = str(entry.strip())
    scale_arcsec = number_str(scale_arcsec)

  if camera_id == "":
    return_flag = False
    entry = input("Enter camera ID text: ")
    camera_id = str(entry.strip())

  if camera_filter == "":
    return_flag = False
    entry = input("Enter camera filter text: ")
    camera_filter = str(entry.strip())
  
  return(return_flag)


# Parse the config file and update defaults
# Treat all file entries as strings
# Strip leading and trailing blanks
# Check for validity later 

for newline in config_fp:
  items = newline.split("=")
  if items[0].strip() == "add_new_series_flag" :
    if ("true" in items[1].strip()):
      add_new_series_flag = True
    elif ("True" in items[1].strip()): 
      add_new_series_flag = True
    else:
      add_new_series_flag = False      
  if items[0].strip() == "upload_files_flag" :
    if ("true" in items[1].strip()):
      upload_files_flag = True
    elif ("True" in items[1].strip()): 
      upload_files_flag = True
    else:
      upload_files_flag = False       
  if items[0].strip() == "upload_data_flag" :
    upload_dat_flag = True    
  if items[0].strip() == "username" :    
    username = str(items[1].strip())
  if items[0].strip() == "password" :    
    password = str(items[1].strip())    
  if items[0].strip() == "observation_tag" :    
    observation_tag = str(items[1].strip())    
  if items[0].strip() == "observation_date" :    
    observation_date = str(items[1].strip())    
  if items[0].strip() == "tic" :    
    tic = str(items[1].strip())     
  if items[0].strip() == "toi" :    
    toi = str(items[1].strip())
    toi = number_str(toi)
    toi = "TOI"+toi      
  if items[0].strip() == "fwhm_arcsec" :    
    fwhm_arcsec = str(items[1].strip())
  if items[0].strip() == "photap_px" :    
    photap_px = str(items[1].strip())
  if items[0].strip() == "duration_min" :    
    duration_min = str(items[1].strip())   
  if items[0].strip() == "n_images" :    
    n_images = str(items[1].strip())    
  if items[0].strip() == "delta_mag" :    
    delta_mag = str(items[1].strip())
  if items[0].strip() == "coverage" :    
    transit_coverage = str(items[1])
  if items[0].strip() == "public_note" :    
    public_note = str(items[1].strip())
  if items[0].strip() == "telescope_id" :    
    telescope_id = str(items[1].strip())    
  if items[0].strip() == "telap_m" :    
    telap_m = str(items[1].strip())
  if items[0].strip() == "scale_arcsec" :    
    scale_arcsec = str(items[1].strip())
  if items[0].strip() == "camera_id" :    
    camera_id = str(items[1].strip())
  if items[0].strip() == "camera_filter" :    
    camera_filter = str(items[1].strip())    
  if items[0].strip() == "public_note" :    
    public_note = str(items[1].strip())
    # Use an underscore in the config file in leave the note field blank
    if public_note == "_":
      public_note = " "
          

# Test that we have the parameters needed to upload

print("\nChecking your entries ... \n")

entries_ok_flag = check_entries()

while not entries_ok_flag:
  entries_ok_flag = check_entries()
  
# Print the ExoFOP TESS uploading entries
# Fix the TOI case for no entry to make the field empty

print("\nReady to upload files.\n")
print("")
print("  User: ", username)           
print("  Password: ", password) 
print("  Observation tag: ", observation_tag) 
print("  Observation date: ", observation_date) 
print("  TIC: ", tic)
 
if toi == "TOI":
  print("  TOI: no entry")
  toi = ""
else:                 
  print("  TOI: ", toi)
  
print("  FWHM (arcsec): ", fwhm_arcsec)        
print("  Aperture radius (pix): ", photap_px)          
print("  Duration (minutes): ", duration_min)       
print("  Number of images: ", n_images)           
print("  Delta mag for NEB: ", delta_mag)          
print("  Transit coverage: ", transit_coverage)   
print("  Telescope ID: ", telescope_id)
print("  Telescope aperture (m): ", telap_m)
print("  Camera ID: ", camera_id)
print("  Scale (arcsec/pix): ", scale_arcsec)
print("  Filter: ", camera_filter)
print("  Public side note: ", public_note)
print("")

answer = input("Continue [yes]?")

if len(answer) > 0:
  if "yes" not in answer.lower():
    exit()
       
    
# Scan the current working directory for files to be uploaded
# They must be in the format
#
#   tic_yyyymmdd_username_observatory_description.ext
#
# Lower case enforced for Linux ease of use and no spaces
# Date in UTC not local date and keep 4-digit year first so it sorts properly on Unix systems
# Username should match ExoFOP tess upload user
# Observatory should be a recognizable and unique but short code
# Description will key how the file treated and should include:
#
#
    
# Get the current working directory (Linux or Windows)

path = os.getcwd()     # get current directory

# Return a list of strings with the files in this directory

file_list = os.listdir(path)
upload_list = []

# Test that they meet the upload requirements

for file_name in file_list:
  file_fields = file_name.split("_")
  if len(file_fields) != 5:
    print("")
    print("Skipping ", file_name, " which does not conform to the upload name standard.\n")
  else:
    upload_list.append(file_name)

# Inform the user

print("Found ", len(upload_list), " files to upload:\n")

for upload_name in upload_list:
  print(upload_name)

print("\n")
answer = input("Continue and upload [yes]?")

if len(answer) > 0:
  if "yes" not in answer.lower():
    exit()
  


# Create dictionaries with entries and credentials matching ExoFOP requirements
# Entries have been validated previously

upload_entries = {
  'planet': toi,
  'tel': telescope_id,
  'telsize': telap_m,
  'camera': camera_id,
  'filter': camera_filter,
  'pixscale': scale_arcsec,
  'psf': fwhm_arcsec,
  'photaprad': photap_px,
  'obsdate': observation_date,
  'obsdur': duration_min,
  'obsnum': n_images,
  'obstype': 'Continuous',
  'transcov': transit_coverage,
  'deltamag': delta_mag,
  'tag': observation_tag,
  'groupname': 'tfopwg',
  'notes': public_note,
  'id': tic
}

upload_credentials = {
  'username': username,
  'password': password,
  'ref': 'login_user',
  'ref_page': '/tess/'
}

# Connect to ExoFOP TESS
# This will always test credentials
# If flags are set a new series will be set and files will be uploaded 

if os.path.exists(path):

  with requests.Session() as session:
    response1 = session.post('https://exofop.ipac.caltech.edu/tess/password_check.php', data=upload_credentials)
    if response1:
      print("")
      print("Login to ExoFOP TESS accepted.")
    else:
      print("") 
      sys.exit("ERROR:  Login credentials were not accepted by ExoFOP TESS.")
      
    if add_new_series_flag:
      response2 = session.post("https://exofop.ipac.caltech.edu/tess/insert_tseries.php", data=upload_entries)
      if response2:
        print("")
        print("Added a new time series to ExoFOP TESS.")
      else:
        print("")
        sys.exit("ERROR: Time series add to ExoFOP TESS failed.")

    else:
      print("Did not create a new series per user request.")

    if upload_files_flag:
      file_list = os.listdir(path)
      for file_name in file_list:
        # Test for files named tic to be uploaded
        # This version requires lower case tic not uppercase TIC
        if os.path.isfile(os.path.join(path,file_name)) and file_name.startswith('tic') and not file_name.startswith('tic '):
          file_name_pieces=file_name.split("_")
 
          # Changes to the payload table could go here based on parsing the file name
          
          # Asssign a description based on the expected file name
          # Description will be blank if it does not match
          
          description=""             
          if "bjd_flux_err" in file_name:
            description = "Photometry table subset for joint fitting"
          elif "subset" in file_name:
            description = "Photometry table subset for joint fitting"         
          elif (("field" in file_name) and (".png" in file_name)):
            description = "Field with apertures"
            if "gaia" in file_name:
              description = "Field with nearby Gaia star apertures"
            elif "zoom" in file_name:
              description = "Zoomed field with apertures"
            elif "full" in file_name:
              description = "Full field with apertures"
          elif (("light_curve" in file_name) and (".png" in file_name)):
            description="Light curve plot"
          elif (("light-curve" in file_name) and (".png" in file_name)):
            description="Light curve plot"
          elif (("lightcurve" in file_name) and (".png" in file_name)):
            description="Light curve plot"
          elif ".apertures" in file_name:
            description="AstroImageJ photometry aperture coordinate file"
          elif ".radec" in file_name:
            description="AstroImageJ photometry aperture RA-Dec file"
          elif ".plotcfg" in file_name:
            description="AstroImageJ plot configuration file"
          elif ".tbl" in file_name:
            description="AstroImageJ full photometry measurements table"
          elif ".xls" in file_name:
            description="AstroImageJ full photometry measurements table"
          elif ".csv" in file_name:
            description="AstroImageJ full photometry measurements table"           
          elif (("seeing-profile" in file_name) and (".png" in file_name)):
            description="Seeing profile"
          elif ".fits" in file_name:
            description="Representative FITS Image from data stack"  
          elif "notes.txt" in file_name:
            description="Observation and analysis notes"
          elif "NEBcheck.zip" in file_name:
            description="NEB check light curve plots of nearby field stars"  
          elif "NEB-table.txt" in file_name:
            description="NEB check summary results"  
          elif "dmagRMS-plot.png" in file_name:
            description="NEB check delta_mag versus RMS plot"
          elif (("merged" in file_name) and (".png" in file_name)):
            description="Merged light curve plot"
          elif (("fitpanel" in file_name) and (".png" in file_name)):
            description="Transit fit panel image"
          elif (("fitpanel" in file_name) and (".txt" in file_name)):
            description="Transit fit panel text"
          if description == "":
            print("Unidentified ", file_name, " was not loaded.")
          else:
            #print(tic, toi, date, tag, description)
            print(file_name, toi)
            files = {'file_name': open(file_name, 'rb')}
            payload = {
              'file_type': 'Light_Curve',
              'planet': toi,
              'file_desc': description,
              'file_tag': observation_tag,
              'groupname': 'tfopwg',
              'propflag': 'on',
              'id': tic,
              'tid' : tic
              }
            response3 = session.post('https://exofop.ipac.caltech.edu/tess/insert_file.php', files=files, data=payload)
            if response3:
              print("")
              print("Uploading file: ", file_name)
            else:
              print("")
              sys.exit("ERROR: File upload failed: ",file_name)
            print(response3.text)
            print("UPLOADED: ", file_name)  
        else:
          print(">> NOT UPLOADED: ", file_name)
    else:
      print("File uploads skipped per user setting.")

exit()
