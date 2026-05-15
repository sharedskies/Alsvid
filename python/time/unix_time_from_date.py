#!/usr/local/bin/python3

# Find the Unix time stamp from a date and time string input

import time
import datetime
import sys


if len(sys.argv) != 2:
  print(" ")
  print("Usage: unix_time_from_date.py ")
  print(" ")
  sys.exit("Calculate the Unix time from a UTC date string yyyy-mm-ddThh:mm:ss.sZ \n")

utcdate = sys.argv[1]

timestamp = datetime.datetime.strptime(utcdate, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()

print("")
print("Unix timestamp for ", utcdate, " is ", timestamp)
print("")

exit()
