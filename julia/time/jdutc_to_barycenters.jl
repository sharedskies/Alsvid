#!/usr/local/bin/julia

"""

   jdutc_to_bjd.jl

   Use the JPL DE440t ephemeris in the current working directory
   to find the BJD for a given UTC and observation site.
   
   BJD is the time of arrival of the signal at the solar system barycenter
   when it is seen to arrive at JDUTC at the observation site on Earth.
   
   This version is valid only for the most recent leap second update, which can
   be recoded by changing the value in the code.  It is limited by the the
   validity range of the DE440t and is intended for the precision conversion of
   contempory observation times.

   The JPL ephemeris, given a solar system object, returns its 
   position and velocity in the solar system barycenter. It also returns the
   correction from TT to TDB.  We assume an input in TT, take the correction
   given and return TDB.
   
   Input time is to be expressed by clocks at the SSB. (Park 2020)
   To millisecond precision the input time can be TT = TAI + 32.184s
     
       Requires selected ASCII DE files from JPL
       Find them by ftp from ssd.jpl.nasa.gov
       Download the file and its header that spans the times of your interest
       Tested for DE405 and DE440t
   
   John Kielkopf
   
   Copywrite 2026
   MIT License
   
   A component of the Alsvid package of Julia astrophysics code
   
   Version 1.1
   May 16, 2026
   
   History
       
       This program was intended to replace the assortment of JPL ephemerides
       programs that were available for Julia as of 2021 and that were unduly
       complex for simple uses, or had dependencies conflicting with Julia 1.7 
       at that time.
       
       It is a fresh start focused on the insightful documentaton 
       of Greg Miller (gmiller@gregmiller.net) posted in 2019 on
       
       https://www.astrogreg.com/jpl-ephemeris-format/jpl-ephemeris-format.html
       
       and placed in the public domain.  
       
       2022-03-12 : Reproduces Greg Miller's example for Mercury with DE405
       2022-03-13 : Using DE440t includes tt-tdb that is not in other versions
       2022-03-17 : Edited comment about input time which is supposed to be TDB
       2022-03-17 : Corrected output for TT-TDB to correctly indicate it is in seconds
       2022-03-27 : Adapted jpl_ephemeris to jdutc_to_jdtdb
       2022-04-06 : Included a configuration file for TOA jdutc_to_bjd
       2022-05-31 : Added LST to have Earth rotation
       2026-05-13 : Linked to data in a data subdirectory of the CWD
       2026-05-16 : Added Roemer delay for a stellar target
       2026-05-17 : Corrected TBD coding error
       2026-05-17 : Confirmed outcome is equivalent to barycorrpy

"""



#using Printf


# The path with trailing / to the DE files 
# Maintain these separately with ftp from ssd.jpl.nasa.gov

data_path = "./data/"

# Leapseconds

leapseconds = 37.0

# File in current working directory with TOA data 

toa_file = "toa.config"

# Collect DE header files 

header_files = ["header.440t"]
header_files = data_path.*header_files
header_file = header_files[1]

# Collect the DE data files

data_files = ["ascp01950.440t"]
data_files = data_path.*data_files
data_file = data_files[1]
 
# DE references

# Series order in the JPL Files
#
# Index   Properties Units            Center    Name
#
#    1        3        km               SSB     Mercury
#    2        3        km               SSB     Venus
#    3        3        km               SSB     Earth-Moon barycenter
#    4        3        km               SSB     Mars
#    5        3        km               SSB     Jupiter
#    6        3        km               SSB     Saturn
#    7        3        km               SSB     Uranus
#    8        3        km               SSB     Neptune
#    9        3        km               SSB     Pluto
#   10        3        km               Earth   Moon (geocentric)
#   11        3        km               SSB     Sun
#   12        2        radians                  Earth Nutations in longitude and obliquity (IAU 1980 model)
#   13        3        radians                  Lunar mantle libration
#   14        3        radians/day              Lunar mantle omega (angular velocity)
#   15        1        seconds                  TT-TDB at geocenter



# Read an ASCII header file and return its names and values

function read_ascii_header(header_file)
    indices = zeros(Int64,3,13)
    
    header_text = readlines(header_file)
    nlines = length(header_text)
    ncoefficients = 0
    
    # Read the header file line by line
    begin_epoch = 0.0
    end_epoch = 0.0
    days_per_block = 0.0
    clight = 0.0
    au = 0.0
    emrat = 0.0
    
    for i = 1:nlines
                
        # How many coefficients?
        if startswith(header_text[i], "KSIZE")
            ncoefficients = parse(Int, split(header_text[i])[4])
        end
        
        # Valid epochs?
        if startswith(header_text[i], "GROUP   1030")
            epochs = split(header_text[i+2])[1:3]
            begin_epoch = parse(Float64, epochs[1])
            end_epoch = parse(Float64, epochs[2])
            days_per_block = parse(Float64, epochs[3])
        end
        
        # Useful data?
        if startswith(header_text[i], "GROUP   1041")
            k = i + 2
            nvalues = parse(Int64, header_text[k])
            values = zeros(Float64,nvalues)
            for j = 1:3:(nvalues-3)
                k = k + 1
                values[j:j+2] = parse.(Float64, split(replace(header_text[k],"D"=>"e" )))
            end
            clight = values[6]
            emrat = values[8]
            au = values[7]
            
        end
    end
    
    # Each entry is indexed by series keyword from name
    # The tuple assigned to the name has 4 components
    #
    #   The start offset of the series in a block (header Group 1050)
    #   The number of properties (above)
    #   The number of coefficients for each property (header Group 1050)
    #   The number of subintervals (header Group 1050)
    # 
    # Handling the entries for omega and tdb depends on the ephemeris
    # Coded here for DE410t 

    jpl_header = Dict() 
    jpl_header["clight"] = clight
    jpl_header["au"] = au
    jpl_header["emrat"] = emrat 
    jpl_header["begin"] = begin_epoch
    jpl_header["end"] = end_epoch
    jpl_header["days"] = days_per_block
    jpl_header["ncoefficients"] = ncoefficients
    
    jpl_header["mercury"]   = (3,3,14,4)
    jpl_header["venus"]     = (171,3,10,2)
    jpl_header["emb"]       = (231,3,13,2)
    jpl_header["mars"]      = (309,3,11,1)
    jpl_header["jupiter"]   = (342,3,8,1)
    jpl_header["saturn"]    = (366,3,7,1)
    jpl_header["uranus"]    = (387,3,6,1)
    jpl_header["neptune"]   = (405,3,6,1)
    jpl_header["pluto"]     = (423,3,6,1)
    jpl_header["moon"]      = (441,3,13,8)
    jpl_header["sun"]       = (753,3,11,2)
    jpl_header["nutation"]  = (819,2,10,4)
    jpl_header["libration"] = (899,3,10,4)
    jpl_header["omega"]     = (0,3,0,0)
    jpl_header["tt_tdb"]    = (1019,1,13,8)

    # This would be the assignments from Group 1050 of DE405
    
    # jpl_header["mercury"]   = (indices[1,1]  , 3, indices[2,1]  , indices[3,1]  )
    # jpl_header["venus"]     = (indices[1,2]  , 3, indices[2,2]  , indices[3,2]  )
    # jpl_header["emb"]       = (indices[1,3]  , 3, indices[2,3]  , indices[3,3]  )
    # jpl_header["mars"]      = (indices[1,4]  , 3, indices[2,4]  , indices[3,4]  )
    # jpl_header["jupiter"]   = (indices[1,5]  , 3, indices[2,5]  , indices[3,5]  )
    # jpl_header["saturn"]    = (indices[1,6]  , 3, indices[2,6]  , indices[3,6]  )
    # jpl_header["uranus"]    = (indices[1,7]  , 3, indices[2,7]  , indices[3,7]  )
    # jpl_header["neptune"]   = (indices[1,8]  , 3, indices[2,8]  , indices[3,8]  )
    # jpl_header["pluto"]     = (indices[1,9]  , 3, indices[2,9]  , indices[3,9]  )
    # jpl_header["moon"]      = (indices[1,10] , 3, indices[2,10] , indices[3,10] )
    # jpl_header["sun"]       = (indices[1,11] , 3, indices[2,11] , indices[3,11] )
    # jpl_header["nutation"]  = (indices[1,12] , 2, indices[2,12] , indices[3,12] )
    # jpl_header["libration"] = (indices[1,13] , 3, indices[2,13] , indices[3,13] )
    # jpl_header["mantel_omega"]     = (0,3,0,0)
    # jpl_header["tt_tdb"]           = (0,1,0,0)

    
    return jpl_header

end


# Read an ASCII header file and return its names and values

function read_ascii_data(data_file, header)

    # Coefficients per block
    nc = header["ncoefficients"]

    # Lines of data per block
    nlines = round(Int,nc/3)

    # Allow for padding to fill a line
    remainder = nc/3 - nlines
    if remainder > 0.1
        nlines = nlines + 1
    end
       
            
    # Read the entire file into an array of lines
    data_text = readlines(data_file)
    
    # How many text lines are there in the file?
    ntext = length(data_text)
    
    # How many blocks of data are there in this file?
    # Allow for the extra block count line at the top of each block
    # This value should be an integer
    
    nblocks = round(Int,ntext/(nlines + 1))
    
    # Parse the text blocks into data
    # Use k to count lines in the text
    
    block_values = zeros(nblocks, nlines*3)
    
    k = 0
    
    for i = 1:nblocks
        k = k + 1
        
        # Read the block count line
        block, count  = parse.(Int, split(data_text[k]))
        if block != i
            println("Miscount at block ", i, " in ", data_file)
            exit()
        end
        if count != nc
            println("Found ", count, "elements, expecting ", nc, " at block ", i)
            exit()  
        end
        
        # Read the data in this block
        # The last values may be the zero padding of the ASCII file 
        for j = 1:3:nc           
            k = k + 1
            block_values[i,j:j+2] = parse.(Float64, split(replace(data_text[k],"D"=>"e" )))            
        end
    end

    #jpl_data = Dict() 
    
    #jpl_data["mercury"]   = (3,3,14,4)
    
    return block_values

end


# Use JPL ephemerides to find the position and velocity of an object
# Spatial units are kilometers
# Velocity units are kilometers/day
# Also return the time TDB if available in the ephemerides

function jpl_object_state(jpl_data, jpl_header, jd, object)

    # The header is a dictionary returning a tuple with
    #
    #   The start offset of the series in a block (header Group 1050)
    #   The number of properties (above)
    #   The number of coefficients for each property (header Group 1050)
    #   The number of subintervals (header Group 1050)
    
    object_offset = jpl_header[object][1]
    nproperties = jpl_header[object][2]
    ncoefficients = jpl_header[object][3]
    nsubintervals = jpl_header[object][4]
    days_per_block = jpl_header["days"]
    nblocks, blocklength = size(jpl_data)

    # Screen for date within this data file
    
    if (jd < jpl_data[1,1]) || (jpl_data[nblocks,2] < jd)
      println("Request time ", jd, " is not in the data filerange ", jpl_data[1,1],
          " to ", jpl_data[nblocks,2])
      exit()
    end
    
    # Identify the database block
    
    block = 1
    while (jd >= jpl_data[block,1])
        block = block + 1
    end
    block = block - 1       

    # Begin and end times for this block are its first two elements

    block_start = jpl_data[block,1]
    block_end = jpl_data[block,2]

    # println(object," ", nproperties, " ", ncoefficients, " ", nsubintervals, " ", nblocks)
    # println("complete jpl data spans from ", jpl_header["begin"], " to ", jpl_header["end"]) 
    # println("this jpl data file spans from ",jpl_data[1,1] , " to ", jpl_data[nblocks,2]) 
    # println("this data block ", block, " is from ", jd_begin, " to ", jd_end)
    # println("days per block ", days_per_block)
    # println("calculating for jd ", jd)

    # Data for the requested object are offset from the first element


    subinterval_days = days_per_block / nsubintervals
    subinterval_floor = floor((jd - block_start)/subinterval_days)
    data_offset = Int(subinterval_floor*ncoefficients*nproperties + object_offset)

    # println("subinterval days ", subinterval_days)
    # println("block start ", block_start)
    # println("jd ", jd)
    # println("object offset ", object_offset)
    # println("subinterval floor ", subinterval_floor)
    # println("data offset ", data_offset, "  data ", jpl_data[block,data_offset])

    # Copy of the JPL coefficients into c[property,index]  for simpler management
    
    c = zeros(Float64,nproperties,ncoefficients)
    k = data_offset   
    for i = 1:nproperties
        for j = 1:ncoefficients
            c[i,j] = jpl_data[block,k]
            k = k + 1
        end    
    end

    # Normalize the requested jd to the subinterval on a scale from -1.0 to 1.0
    # The normalized jd is x
    
    valid_start = block_start + subinterval_floor * subinterval_days
    valid_end = valid_start + subinterval_days
    djd = jd - valid_start
    x = (djd / subinterval_days) * 2.0 - 1.0
    
    # Find the requisite Chebyshev polynomials of the first kind for this x
    # See https://en.wikipedia.org/wiki/Chebyshev_polynomials
    # Use the recurrence relationship to generate and then save them
    
    chebyshev = zeros(Float64, ncoefficients)
    chebyshev[1] = 1.0
    chebyshev[2] = x
    for i =3:ncoefficients
        chebyshev[i] = 2.0 * x * chebyshev[i-1] - chebyshev[i-2]
    end
    
    # Find the position from the Chebyshev expansion with coefficients
    
    position = zeros(Float64, nproperties)
    
    for i = 1:nproperties
        for j = 1:ncoefficients
            position[i] = position[i] + c[i,j]*chebyshev[j]
        end
    end
    
    # Find the velocity (rate of change) from its derivative if required
    
    velocity = zeros(Float64, nproperties)
    v = zeros(Float64, ncoefficients)
    for i = 1:nproperties
       
       # Find the derivatve in the scaled time range
       
       v[1] = 0.0
       v[2] = 1.0
       v[3] = 4.0 * x
       for j = 4:ncoefficients
           v[j] = 2.0 * x * v[j-1] + 2.0 * chebyshev[j-1] - v[j-2]
       end    
       for j = 1:ncoefficients
           velocity[i] = velocity[i] + v[j]*c[i,j]
       end
       
       # Convert from per scaled time (-1 to + 1) to per day
       # Factors in DE405 are 1/4 for Mercury, 1/8 for  Venus, 1/16 for Jupiter       
       
       velocity[i] =  (2.0/subinterval_days) * velocity[i] 
    
    end
   
    return position[1:nproperties], velocity[1:nproperties]

end

# Convert a string in dd:mm:ss format to declination in degrees

function dec_deg_from_dms(instring)
  declination = 0.0
  decsign = +1.0
  item = split(instring,":")
  if length(item) == 0
    decdeg = parse(Float64, instring)
    decmin = 0.0
    decsec = 0.0
  elseif length(item) == 2
    decdeg = parse(Float64, item[1])
    decmin = parse(Float64, item[2])
    decsec = 0.0
  elseif length(item) == 3
    decdeg = parse(Float64, item[1])
    decmin = parse(Float64, item[2])
    decsec = parse(Float64, item[3])
  else
    println("Declination cannot be parsed \n")
    exit()  
  end
  if decdeg < 0.0
    decsign = -1.0
    decdeg = abs(decdeg)
  end   
  declination = decsign*(decdeg + decmin/60.0 + decsec/3600.0)  
  return declination
end  


# Convert a string in hh:mm:ss format to right ascension in degrees

function ra_deg_from_hms(instring)
  right_ascension = 0.0
  item = split(instring,":")
  if length(item) == 0
    rahr = parse(Float64, instring)
    ramin = 0.0
    rasec = 0.0
  elseif length(item) == 2
    rahr = parse(Float64, item[1])
    ramin = parse(Float64, item[2])
    rasec = 0.0
  elseif length(item) == 3
    rahr = parse(Float64, item[1])
    ramin = parse(Float64, item[2])
    rasec = parse(Float64, item[3])
  else
    print("Right Ascension cannot be parsed \n")
    exit()  
  end
  if (rahr < 0.0)  || (rahr > 24.0)
    println("Right Ascension must be between 0 and 24 hours")
    exit()  
  end   
  right_ascension = (rahr + ramin/60.0 + rasec/3600.0)*15.0    
  return right_ascension
end  


# Read model parameter file and create a parameter dictionary

function read_parameter_file(infile)

  dictionary = Dict()
  dictionary["latitude"] = 0.0
  dictionary["longitude"] = 0.0
  dictionary["altitude"] = 0.0
  dictionary["right_ascension"] = 0.0
  dictionary["declination"] = 0.0
  
  # Read the file
  
  parm_text = readlines(infile)
   

  # Parse the text lines into parameters

  for line in parm_text 
                    
    # Skip comments marked by first character # or !

    if line[1] == '#'
      #println(line)
      continue
    end  

    if line[1] == '!'   
      #println(line)
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
    
    # There should be only 2 items after the split

    if length(item) != 2
      println("Error in the parameter file at line ", line)
      println("Check for an ambiguous item in ", infile)
      exit   
    end
     
    # Test for entries and add to the dictionary
    
    if occursin("right_ascension", item[1])
      dictionary["right_ascension"] = ra_deg_from_hms(item[2])    
    end
    if occursin("declination", item[1])
      dictionary["declination"] = dec_deg_from_dms(item[2])
    end      
    if occursin("longitude", item[1])
      dictionary["longitude"] = parse(Float64,item[2])
    end
    if occursin("latitude", item[1])
      dictionary["latitude"] = parse(Float64,item[2])
    end
    if occursin("altitude", item[1])
      dictionary["altitude"] = parse(Float64,item[2])
    end
    if occursin("jd_utc", item[1])
      dictionary["jd_utc"] = parse(Float64,item[2])
    end

  end
  return dictionary
end
    


# Compute the jd_tdb from jd_utc

function tdb(toa_data)

  # Offset utc to tdb
  # Find TT from JD_UTC

  dt_tai = toa_data["leapseconds"]/86400.0
  dt_tt = 32.184/86400.0
  jd_tt = toa_data["jd_utc"] + dt_tai + dt_tt 

  # Find TDB

  object = "tt_tdb"
  jpl_header = read_ascii_header(toa_data["header_file"])
  jpl_data = read_ascii_data(toa_data["data_file"], jpl_header)
  jpl_state = jpl_object_state(jpl_data, jpl_header, jd_tt, object)
  dt_tdb_sec = -1.0*jpl_state[1][1]
  dt_tdb = dt_tdb_sec/86400.0
  jd_tdb = jd_tt + dt_tdb
 
  return jd_tdb

end


# Compute coordinates of Earth in space as a vector

function earth(toa_data)

  # Offset utc to tdb
  # Find TT from JD_UTC

  jd_tdb = tdb(toa_data)

  jpl_header = read_ascii_header(toa_data["header_file"])
  jpl_data = read_ascii_data(toa_data["data_file"], jpl_header)
 
  earth_position, earth_velocity = jpl_object_state(jpl_data, jpl_header, jd_tdb, "emb")
  moon_position, moon_velocity = jpl_object_state(jpl_data, jpl_header, jd_tdb, "moon")
  earth_moon_ratio = jpl_header["emrat"]
  for i = 1:3
    earth_position[i] = earth_position[i] - moon_position[i]/(1.0 + earth_moon_ratio)
    earth_velocity[i] = earth_velocity[i] - moon_velocity[i]/(1.0 + earth_moon_ratio)
  end
  
  # Position is in km and velocity is in km/d
  # Convert velocity to km/s
  
  earth_velocity = earth_velocity/86400.0
  
  return earth_position, earth_velocity


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


# Sidereal time for +east longitude

# Calculate lst for Earth-based TOA longitude
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


function lst(toa_data)

  # Use JD from the input time of arrival database

  jd = toa_data["jd_utc"]

  # Phase hours to midnight to find UT
 
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


#  static final double FLATTEN = 0.003352813;  // flattening, 1/298.257
#  static final double EQUAT_RAD = 6378137.;   // equatorial radius, meters


#  double[] Geocent(double longitin, double latitin, double height) {
#      // XYZ coordinates given geographic.
#      // input is decimal hours, decimal degrees, and meters.
#      // See 1992 Astr Almanac, p. K11.
#
#      double denom, C_geo, S_geo;
#      double geolat, coslat, sinlat, geolong, sinlong, coslong;
#      double [] retval = {0.,0.,0.};
#
# 
#      //System.out.printf("lat long %f %f\n",latitin,longitin);
#      geolat = latitin / DEG_IN_RADIAN;
#      geolong = longitin / HRS_IN_RADIAN;
#      //System.out.printf("radians %f %f \n",geolat,geolong);
#      coslat = Math.cos(geolat);  sinlat = Math.sin(geolat);
#      coslong = Math.cos(geolong); sinlong = Math.sin(geolong);
# 
#      denom = (1. - FLATTEN) * sinlat;
#      denom = coslat * coslat + denom * denom;
#      C_geo = 1./ Math.sqrt(denom);
#      S_geo = (1. - FLATTEN) * (1. - FLATTEN) * C_geo;
#      C_geo = C_geo + height / EQUAT_RAD;
#      S_geo = S_geo + height / EQUAT_RAD;
#      retval[0] = C_geo * coslat * coslong;
#      retval[1] = C_geo * coslat * sinlong;
#      retval[2] = S_geo * sinlat;
# 
#      return retval;
#  }


#  double[] topocorr(double ra, double dec, double dist, double lat, double alt, double sidereal) {
#
#      double x, y, z, x_geo, y_geo, z_geo, topodist;
#      double [] retvals;
#
#      x = Math.cos(ra/HRS_IN_RADIAN) * Math.cos(dec/DEG_IN_RADIAN) * dist;
#      y = Math.sin(ra/HRS_IN_RADIAN) * Math.cos(dec/DEG_IN_RADIAN) * dist;
#      z = Math.sin(dec/DEG_IN_RADIAN) * dist;
#
#      retvals = Geocent(sidereal, lat, alt);
#      x_geo = retvals[0] / EARTHRAD_IN_AU;
#      y_geo = retvals[1] / EARTHRAD_IN_AU;
#      z_geo = retvals[2] / EARTHRAD_IN_AU;
#
#      x = x - x_geo;
#      y = y - y_geo;
#      z = z - z_geo;
#
#      topodist = Math.sqrt(x*x + y*y + z*z);
#
#      x /= topodist;
#      y /= topodist;
#      z /= topodist;
#
#      retvals[0] = Math.atan2(y,x) * HRS_IN_RADIAN;
#      if (retvals[0]<0.0) retvals[0] += 24.0;
#      retvals[1] = Math.asin(z) * DEG_IN_RADIAN;
#
#      return retvals;
#   }




# Allow for transit time to Earth's center from the point of observation.
# Google Earth uses WGS84 geodetic coordinates, and the latitude differs
#   from the gecentric latitude, complicating the calculation of the 
#   cartesian coordinates of the spheroid.  

function geocenter(toa_data)

  # Use spheroidal Earth for now
  # See https://en.wikipedia.org/wiki/Earth_radius
  
  # Earth in the WGS-84 ellipsoid model in meters
  # Equatorial radius is a
  # Polar radius is b
  # Flattening f = 1 - b/a
  
  a = 6378137.0
  f = 1.0/298.257223563  
  b = a*(1.0 - f)
    
  
  # Read and scale dictionary parameters
  # Longitude and latitude are geodetic coordinates in degrees
  # Convert degrees to radians
  # Position and velocity are in km and km/s
  # Use m and m/s here for position and velocity

  earth_position, earth_velocity = earth(toa_data)
  earth_position = 1000.0*earth_position
  earth_velocity = 1000.0*earth_velocity
  phi = toa_data["latitude"] * pi/180.0
  lambda = toa_data["longitude"] * pi/180.0
  h = toa_data["altitude"] 
  
  # See ESA's explanation
  # https://gssc.esa.int/navipedia/index.php/Ellipsoidal_and_Cartesian_Coordinates_Conversion
  
  # Eccentricity of azimuthal cross section is  "e" 
  # Radius of curvature in the ellipsoidal vertical "r"
  
  e = sqrt(2.0*f - f^2)
  r = a / sqrt(1.0 - e^2 * sin(phi)^2)
  
  # Observer's location in geocentric cartesian coordinates
  
  x = (r + h)*cos(phi)*cos(lambda)
  y = (r + h)*cos(phi)*sin(lambda)
  z = ((1.0 - e^2)*r + h)*sin(phi)  
  
  # Target direction in celestial coordinates 

  ra = toa_data["right_ascension"] * pi/180.0
  dec = toa_data["declination"] * pi/180.0

  # Find the sidereal time

  jd_utc = toa_data["jd_utc"]
  
end

# Compute the Roemer delay

function roemer(right_ascension, declination, tdb)

# Find the difference in arrival times at Earth's center and at the 
#   solar system barycenter

end

# Compute the Roemer delay

function roemer(right_ascension, declination, earth_position)

# Find the difference in arrival times at Earth's center and at the 
#   solar system barycenter


  # Speed of light in km/s (exact constant used in IAU/JPL standards)
  c = 299792.458
  
  # Convert right ascension and declination from degrees to radians
  ra_rad = right_ascension * pi / 180.0
  dec_rad = declination * pi / 180.0
  
  # Construct the unit vector pointing toward the star
  n_star = zeros(Float64, 3)
  n_star[1] = cos(dec_rad) * cos(ra_rad)
  n_star[2] = cos(dec_rad) * sin(ra_rad)
  n_star[3] = sin(dec_rad)
  
  # Vector projection of Earth's position onto the line of sight (dot product)
  # earth_position is in km, so the result is in km
  projection = earth_position[1]*n_star[1] + earth_position[2]*n_star[2] + earth_position[3]*n_star[3]
  
  # Delay in seconds
  delay_seconds = projection / c
  
  # Convert delay to days to match the JD format
  delay_days = delay_seconds / 86400.0
  
  return delay_days

end

# Compute the Shapiro delay

function shapiro()

end


# Compute the Einstein delay

function einstein()

end

# Functions have been defined
# Now run the code for this application

toa_data = read_parameter_file(toa_file)
toa_data["header_file"] = header_file
toa_data["data_file"] = data_file
toa_data["leapseconds"] = leapseconds

# Calculate TDB from UTC
jd_tdb = tdb(toa_data)

println(" ") 

# Calculate Earth position and velocity at this TDB
earth_position, earth_velocity = earth(toa_data)

println("Earth's barycenter relative to solar system barycenter on")
println("UTC ", toa_data["jd_utc"])
println("TDB ", jd_tdb)
println(" ") 

print("Position (km) ", earth_position,"\n")
print("Velocity (km/s) ",earth_velocity,"\n")
println(" ")
 
r_earth = sqrt(earth_position[1]^2 + earth_position[2]^2 + earth_position[3]^2)
v_earth = sqrt(earth_velocity[1]^2 + earth_velocity[2]^2 + earth_velocity[3]^2)

println("Distance (km) ", r_earth)
println("Speed (km/s) ", v_earth)

# Compute Roemer Delay
roemer_delay = roemer(toa_data["right_ascension"], toa_data["declination"], earth_position)
println("Roemer Delay (days): ", roemer_delay)
println("Roemer Delay (minutes): ", roemer_delay * 1440.0)

# Calculate partial BJD (TDB + Roemer)
# Note: Full BJD will also require Shapiro and Einstein additions
bjd_partial = jd_tdb + roemer_delay
println("Partial BJD (TDB + Roemer): ", bjd_partial)
println("")
exit()
