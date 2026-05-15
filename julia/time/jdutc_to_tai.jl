#!/usr/local/bin/julia

#  jdutc_to_jdtai
#
#    Apply the difference between UTC and TAI to return JD_TAI from JD_UTC
#    Uses BigFloat data type (see typeof(var)) for unlimited internal precision

#    Explanation: 
#      https://www.nist.gov/pml/time-and-frequency-division/time-realization/leap-seconds

#    Explicit input:
#      JD_UTC

#    Explicit output:
#      JD_TAI

#    Required data:
#      leap-seconds.list 

#    John Kielkopf (kielkopf@louisville.edu)
#    MIT License
#    Copyright 2021
#    
#    2021-12-31 Version 1.0

#    This code applies the difference tai-utc to utc to return tai
#    In the contemporary era tai is always ahead of utc

#    Reference data:
#      https://www.ietf.org/timezones/data/leap-seconds.list
#      Indicated instant in NTP timecode with leap seconds
#      The leap seconds apply at that instant until the next update

#    Validity after the start of 1972:
#      Accurate TAI to within the error of the atomic clocks (~1 ns)

#    Validity prior to 1972:
#      Ignores complexity and uses first entry of table

using Printf

#  Read and parse the command line arguments

function get_jd_args(args)
  nargs = length(args)
  
  if nargs < 1
    print("Enter space deliminted JD_UTCs on the command line \n")
    exit()
  end
 
  jd_utcs = zeros(BigFloat,nargs)
  for i in 1:nargs
    jd_utcs[i] = parse(BigFloat,args[i])
  end
  return jd_utcs
end


# Read a 2-column data file and return  x and y vectors

function read_data_file(infile) 
  
  data_text = readlines(infile) 

  # Pre-define empty data arrays of type Float64
  
  x_data = zeros(BigFloat,0) 
  y_data = zeros(BigFloat,0) 

  # Parse the data lines into the values

  for line in data_text 

    # Skip comment line markers by testing for marker characters
    
    if line[1] == '#'
       
      continue
    
    end 
    
    if line[1] == '!' 
       
      continue
    
    end 
                 
    # Separate entries in a data line using common delimiters
    
    # Function occursin requires two string arguments (needle, haystack)  
           
    if occursin(",", line)
            
      entry = split(line,",")       
        
    # Otherwise try separated or tabbed entries
    
    else
    
      entry = split(line)
        
    end
            
    # Test for successful splitting into two data entries
    # Skip any that do not work
    
    if length(entry) < 2
      
      continue
    
    end
        
    x = parse(BigFloat,entry[1])
    y = parse(BigFloat,entry[2])
                     
    push!(x_data, x) 
    push!(y_data, y)

  end    

  # Return two BigFloat vectors
  return x_data, y_data 

end 



#  Use the leapseconds data in IERS format to find the TAIs given UTCs
#  Uncommented file entries have an NTP timestamps for each  new leapsecond

function get_tais(jd_utcs)
  if isfile("leap-seconds.list") == false
    print("The file leap-seconds.list must be present \n")
    exit()
  end  
  ntpstamps, leapseconds = read_data_file("leap-seconds.list")  
  ntpjds = ntpstamps ./ BigFloat(86400) .+ BigFloat(15020) .+ BigFloat(2400000.5)
  jd_tais = zeros(BigFloat, length(jd_utcs))
  for i in 1:length(jd_utcs)
    leapsecond = leapseconds[1]
    for j in 1:length(ntpjds)
      if jd_utcs[i] >= ntpjds[j]
        leapsecond = leapseconds[j]
      end
    end     
    jd_tais[i] = jd_utcs[i] + leapsecond/BigFloat(86400.0) 
  end
  return jd_tais
end

# Execution begins here

jd_utcs = get_jd_args(ARGS)
jd_tais = get_tais(jd_utcs)

# Display formatted result with estimate of numerical error 

njds = length(jd_utcs)
if njds < 1
  exit()
end  
print("\n")
least_count_error = BigFloat(0.0001)*BigFloat(86400.0) 
@printf("     Accurate to %4.2f nanoseconds \n", least_count_error)
@printf("     JD_UTC                 JD_TAI \n")
for i in 1:njds
 @printf("%20.13f  %20.13f \n", jd_utcs[i], jd_tais[i])
 end
print("\n")

exit()

