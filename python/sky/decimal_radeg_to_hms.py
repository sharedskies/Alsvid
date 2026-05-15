#!/usr/local/bin/python3

"""

  Convert decimal degrees for RA to hh::mm::ss of hh:mm::ss
    
    Returns integer portion as first pair
    Fraction portion as minutes and seconds
    Works for hours or degrees but set for RA 0 to 24 hours
    Prepends minus sign for negative input

"""  
import sys

if len(sys.argv) == 2:
  angle = float(sys.argv[1])
else:
  print(" ")
  print("Usage: decimal_radeg_to_rahms.py angle")
  print(" ")
  sys.exit("Convert RA in decimal degrees RA in hh::mm::ss\n")

def float_to_hms_str(invalue):

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

ra_str = float_to_hms_str(angle)
print(ra_str)
exit()      
