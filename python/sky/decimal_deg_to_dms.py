#!/usr/local/bin/python3

"""

  Convert decimal degrees to dd::mm::ss
    
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
  print("Usage: decimal_deg_to_dms.py angle")
  print(" ")
  sys.exit("Convert angle in decimal degrees to in dd::mm::ss.sss\n")

def float_to_dms(degrees):
  
  # Format floating point degrees into a +/-dd:mm:ss.sss string
  
  dg = int(abs(degrees))
  subdegrees = abs( abs(degrees) - float(dg) )
  minutes = subdegrees * 60.
  mn = int(minutes)
  subminutes = abs( minutes - float(mn))
  seconds = subminutes * 60.
  ss = int(seconds)
  subseconds = abs( seconds - float(ss) )
  subsecstr = ("%.3f" % (subseconds,)).lstrip('0')
  if degrees > 0:
    dsign = '+'
  elif degrees == 0.0:
    dsign = ' '
  else:
    dsign = '-'
  anglestr = "%s%02d:%02d:%02d%s" % (dsign, dg, mn, ss, subsecstr) 
  return anglestr

def float_ra_to_hms_str(invalue):

  # Format floating point right ascension into a +/-dd:mm:ss.sss string
  
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


degree_str = float_to_dms(angle)
print(degree_str)
exit()      
