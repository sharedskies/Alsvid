#!/usr/local/bin/python3

"""

  Convert degrees or hours as  dd::mm::ss to decimal degrees or hours
    
    Prepends minus sign for negative input

"""  
import sys

if len(sys.argv) == 1:
  print(" ")
  print("Usage: dms_to_decimal.py")
  print(" ")
  sys.exit("Convert degrees or hours  in  dd::mm::ss to decimal or hours degrees\n")
elif len(sys.argv) == 2:
  angle_str = sys.argv[1]
else:
  print(" ")
  print("Usage: dms_to_decimal.py")
  print(" ")
  sys.exit("Convert degrees or hours in  dd::mm::ss to decimal degrees or hours\n")


def degrees(degree_str):
  
  degree_parts = degree_str.split(":")  
  if len(degree_parts) == 3:
    dd = float(degree_parts[0])
    mm = float(degree_parts[1])
    ss = float(degree_parts[2])
  elif len(degree_parts) == 2:
    dd = float(degree_parts[0])
    mm = float(degree_parts[1])
    ss = 0.
  elif len(degree_parts) == 1:
    dd = float(degree_parts[0])
    mm = 0.
    ss = 0.
  else:
    print("Cannot recognize the input ", degree_str, "\n")
    exit()
  
  if dd < 0:
    angle = -1.*(abs(dd) + mm/60. + ss/3600.)
  else:
    angle = dd + mm/60. + ss/3600.

    
  return(angle)      


print(degrees(angle_str))

exit()      
