#!/usr/local/bin/julia

# Calculate current lst by default or optionally for another longitude
# Longitudes are +east
# Right-handed coordinate system with polar axis north +z
# For example, continental Europe is +x, +y, +z
#   while CONUS is -x, +y, +z
# This coordinate system the opposite handedness of XEphem
# It is a geodetic coordinate system that is used by Google Maps

# Reference: Explanatory Supplement to the Nautical Almanac
# Edited by P. Kenneth Seidelmann
# University Science Books 1992
# Page 50

using Dates

# Initial parameters

# Greenwich prime meridian
# site_longitude = 0.0

# Moore Observatory near Crestwood, Kentucky USA
site_longitude = -85.52850

# Mt. Kent Observatory  near Toowoomba, Queensland Australia
# site_longitude = 151.85523

# Mt. Lemmon Observatory near Tucson, Arizona USA
#site_longitude = -110.7882

  
# Floating point Julian day at this moment in days
# JD is referenced to noon
# UT day is referenced to midnight


# Local sidereal time for +east longitude

function lst_now()

  jd = datetime2julian(now(Dates.UTC))

  # Phase hours to midnight
 
  if jd - floor(jd) >= 0.5
    # Find UT for the next calendar day
    # Fractional JD is too big by 0.5
    utc = (jd - floor(jd) - 0.5)*24.0
  else
    # Find UT for this calendar day
    # Fractional JD is too small by 0.5
    utc = (jd - floor(jd) + 0.5)*24.0
  end  

  
  # Phase days to midnight UT days
 
  if jd - floor(jd) >= 0.5
    # UT day is the next day 
    # JD is from noon the previous UT day and too small
    # Increment JD by 0.5 so that tu is midnight UT day
    tu = floor(jd) + 0.5
  else
    # UT day is this day
    # JD is noon yesterday and too large
    # Decrement JD by 0.5 so that tu is midnight UT day
    tu = floor(jd) - 0.5
  end  

  # Use tu in years from J2000.0

  tu = (tu - 2451545.0)/36525.0    

  # Find the sidereal time at midnight at Greenwich

  a0 = 24110.54841 / 3600.
  a1 = 8640184.812866 / 3600.0
  a2 = 0.093104 / 3600.0
  a3 = -6.2e-6 / 3600.0
  gst0 = a0 + a1*tu + a2*tu*tu + a3*tu*tu*tu   

  # Map the time into 0:24

  gst0 = map24(gst0)  
  
  # Allow for hours since midnight and remap
  
  gst = map24(gst0 + utc * 1.002737909)
  
  # For another geodetic longitude
  
  lst = (gst + site_longitude / 15.0)
  lst = map24(lst)
  return lst
end

# Express hours in a 0-24 range

function map24(hours)
  
  while hours < 0.0
    hours = hours + 24.0
  end  
  
  while hours > 24.0
    hours = hours - 24.0 
  end
     
  return hours   
  
end


# Format float hours as hh:mm:ss.sss string
# Force 0 to 24 hour basis and truncate to milliseconds

function hms(hours)
  hours = map24(hours)
  hr = floor(hours)
  subhours = hours - hr
  minutes = subhours * 60.0
  mn = floor(minutes)
  subminutes = minutes - mn
  seconds = subminutes * 60.0
  sc = floor(seconds)
  subseconds = seconds - sc
  milliseconds = floor(subseconds*1000.0)
  hh = lpad(string(Int64(hr)),2,'0')
  mm = lpad(string(Int64(mn)),2,'0')
  ss = lpad(string(Int64(sc)),2,'0')
  ms = string(Int64(milliseconds))
  hmsstr = hh*":"*mm*":"*ss*"."*ms
  
  return hmsstr
end
  
println(hms(lst_now()))

exit()




