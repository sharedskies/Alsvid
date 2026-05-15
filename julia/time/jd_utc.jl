#!/usr/local/bin/julia

# Return the current jd_utc in TAI and TT time systems

using Dates
using Printf

# UTC reported by Dates is UT1 -> TAI with leapsecond already included

function jd_now()
  jd = datetime2julian(now(Dates.UTC))
  return jd
end

jd_tai = jd_now()
jd_tai_str = @sprintf "%.8f" jd_tai
jd_tt = jd_tai + BigFloat(32.184)/BigFloat(86400.0)
jd_tt_str = @sprintf "%.8f" jd_tt
println("TAI: ", jd_tai_str)
println("TT:  ", jd_tt_str)
exit()
