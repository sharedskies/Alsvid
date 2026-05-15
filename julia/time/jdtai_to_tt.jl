#!/usr/local/bin/julia

#  jdtai_to_tt
#
#    Apply the difference between TAI and TT to return JD_TT from JD_TAI

#    TT runs at the rate of TAI (SI seconds)  on the surface of the Earth 
#      See IAU Circular  179 for a clear explanation where the older term TDT
#      is said to be obsolete, but effecively equivalent to TDT. 

#    TT = TAI + 32.184 seconds
#    We obtain TCG (at Earth's center of gravity) from TT
#    TT = TCG - LG(TCG - t0)
#    LG = 6.969290134e-10 exactly
#    t0 = JD 2443144.5003725 at whic TT, TCG, and TCB all read 
#      1977 January 1 00:00:32.184

#    JD_TT in [TAI] differs from JD_TT in [BIPM].  The 
#      BIPM variant requires a table from the International Bureau of 
#      Weights and Measures and differs from TAI time by ~27 microseconds
#      as of 2021-01-01.  

#    IAU Circular 179 (page 15) says that TT may be used as an input argument
#      to the JPL ephemerides (e.g. DE405) wih an errror < 2 millisecond.
#      Otherwise, TEPHEM is nominally TDB which is TT plus a correction
#      given in the circular, or given with greater accuracy by Fairhead.
#      See jdtt_to_tdb.jl for this code. 

#    Uses BigFloat data type for unlimited precision

#    Explanations:
#      George H. Kaplan, IAU Circular 179 
#      J. Eastman, R. Siverd, B.Scott Gaudi, PASP 122, 935 (2010)

#    Explicit input:
#      JD_TAI 

#    Explicit output:
#      JD_TT [TAI] but see code for [BIPM]

#    Required data:
#      None

#    John Kielkopf (kielkopf@louisville.edu)
#    MIT License
#    Copyright 2021
#    
#    2022-01-19 Version 1.1


using Printf

#  Read and parse the command line arguments
#  Return BigFloat array

function get_jdtai_args(args)
  nargs = length(args)
  
  if nargs < 1
    print("Enter space delimited JD_TAIs on the command line \n")
    exit()
  end
 
  jd_tais = zeros(BigFloat,nargs)
  for i in 1:nargs
    jd_tais[i] = parse(BigFloat,args[i])
  end
  return jd_tais
end


#  Apply the offset of TAI scale times to obtain TT 
#
#  For BIPM time see https://webtai.bipm.org/ftp/pub/tai/ttbipm/TTBIPM.2020
#    which recommends using
#
#    TT(BIPM20) = TAI + 32.184 s + 27665.3 ns - 0.01x(MJD-59209) ns 
#
#    based on the 2020 table.  The difference will be of the order of 
#    27 microseconds and decreasing in 2021 and 2022.

function get_tts(jd_tais)
  jd_tts = jd_tais .+ BigFloat(32.184)/BigFloat(86400.0) 

  return jd_tts
end

# Execution begins here

jd_tais =   get_jdtai_args(ARGS)
jd_tts = get_tts(jd_tais)

# Display formatted result with estimate of numerical error 

njds = length(jd_tts)
if njds < 1
  exit()
end  
print("\n")
least_count_error = BigFloat(0.0001)*BigFloat(86400.0) 
@printf("     Accurate to %4.2f nanoseconds \n", least_count_error)
@printf("     JD_TAI                 JD_TT \n")
for i in 1:njds
 @printf("%20.13f  %20.13f \n", jd_tais[i], jd_tts[i])
 end
print("\n")

exit()

