#!/usr/local/bin/julia

"""

   ephemeris_from_jpl.jl

   This version uses DE440t in the current working directory.
   
   Given a solar system object return its position and velocity in the solar system barycenter.
   
   Input time is to be expressed by clocks at the SSB (ie, in TDB). (Park 2020)
   To millisecond precision the input time can be TT = TAI + 32.184s
   This version with DE440t will return TT-TDB as an option.
  
   
       Requires selected ASCII DE files from JPL
       Find them by ftp from ssd.jpl.nasa.gov
       Download the file and its header that spans the times of your interest
       Tested for DE405 and DE440t
   
   John Kielkopf
   
   Copywrite 2022
   MIT License
   
   A component of the Clearly package of Julia astrophysics code
   
   Version 1.02
   March 17, 2022
   
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

"""


using Printf


# The path with trailing / to the DE files 
# Maintain these separately with ftp from ssd.jpl.nasa.gov

data_path = "./"


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

# Functions have been defined
# Now run the code for an application

# Assign test values

object = "mercury"
jd = 2458850.5

# Read the command line for actual values

if length(ARGS) != 2
  println("Compute the JPL emphemeris for an object at a JD_TT")
  println("Use object and jd  on the command line.")
  exit()
end
   
object = ARGS[1] 
jd = parse(Float64, ARGS[2])

println(" ")
println("Running for ", object, " at ", jd)

if (object == "earth")   
   jpl_header = read_ascii_header(header_file)
   jpl_data = read_ascii_data(data_file, jpl_header)
   earth_position, earth_velocity = jpl_object_state(jpl_data, jpl_header, jd, "emb")
   moon_position, moon_velocity = jpl_object_state(jpl_data, jpl_header, jd, "moon")
   earth_moon_ratio = jpl_header["emrat"]
   for i = 1:3
     earth_position[i] = earth_position[i] - moon_position[i]/(1.0 + earth_moon_ratio)
     earth_velocity[i] = earth_velocity[i] - moon_velocity[i]/(1.0 + earth_moon_ratio)
   end

   println(" ")
   println("Earth's barycenter relative to solar system barycenter on ", jd, " TT\n")
   print("Position (km) ", earth_position,"\n")
   print("Velocity (km/d)",earth_velocity,"\n")
   println(" ")
   
   exit()   
end   

if (object == "libration")
    jpl_header = read_ascii_header(header_file)
    jpl_data = read_ascii_data(data_file, jpl_header)
    jpl_state = jpl_object_state(jpl_data, jpl_header, jd, object)
    println(" ")
    print("Angle (rad) ", jpl_state[1],"\n")
    print("Rate of change (rad/d)", jpl_state[2],"\n")
    println(" ")
    exit()
end
    
if (object == "nutation")
    jpl_header = read_ascii_header(header_file)
    jpl_data = read_ascii_data(data_file, jpl_header)
    jpl_state = jpl_object_state(jpl_data, jpl_header, jd, object)
    println(" ")
    print("Angle (rad) ", jpl_state[1],"\n")
    print("Rate of change (rad/d)", jpl_state[2],"\n")
    println(" ")
    exit()
end

if (object == "omega")
    println("The lunar mantel angular velocity omega is not available in DE405")
    println(" ")
    exit()
    jpl_header = read_ascii_header(header_file)
    jpl_data = read_ascii_data(data_file, jpl_header)
    jpl_state = jpl_object_state(jpl_data, jpl_header, jd, object)
    println(" ")
    print("Angle (rad) ", jpl_state[1],"\n")
    print("Rate of change (rad/d)", jpl_state[2],"\n")
    println(" ")
    exit()
end


if (object == "tt_tdb")
    # Uncomment the following if using DE405
    # println("(tt - tdb) is not available in DE405"
    # println(" ")
    # exit()
    jpl_header = read_ascii_header(header_file)
    jpl_data = read_ascii_data(data_file, jpl_header)
    jpl_state = jpl_object_state(jpl_data, jpl_header, jd, object)
    println(" ")
    print("tt-tdb (s)", jpl_state[1],"\n")
    print("Rate of change (s/d)", jpl_state[2],"\n")
    println(" ")
    exit()
end


jpl_header = read_ascii_header(header_file)
jpl_data = read_ascii_data(data_file, jpl_header)
jpl_state = jpl_object_state(jpl_data, jpl_header, jd, object)

println(" ")
print("Position (km) ", jpl_state[1],"\n")
print("Velocity (km/d)", jpl_state[2],"\n")
println(" ")


exit()


