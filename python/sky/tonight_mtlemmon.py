#!/usr/local/bin/python3

"""

  Display times of twilight for a local site
  
  Input:
    Geographic coordinates and timezone are preset
    
  Output:
    Listing of times

"""      

import datetime as dt
from pytz import timezone
from skyfield import almanac
from skyfield.api import N, W, wgs84, load

# Location

site_lat = 32.0 + 26.0/60.0 + 33.0/3600.0
site_long = 110.0 + 47.0/60.0 + 20.0/3600.0
zone = timezone('America/Phoenix')

# Figure out local midnight
now = zone.localize(dt.datetime.now())
midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
next_midnight = midnight + dt.timedelta(days=1)

ts = load.timescale()
t0 = ts.from_datetime(midnight)
t1 = ts.from_datetime(next_midnight)
eph = load('de421.bsp')
bluffton = wgs84.latlon(site_lat * N, site_long * W)
f = almanac.dark_twilight_day(eph, bluffton)
times, events = almanac.find_discrete(t0, t1, f)

print("")
print("Twilight for Mount Lemmon Observatory today")
print("")

previous_e = f(t0).item()
for t, e in zip(times, events):
  tstr = str(t.astimezone(zone))[:16]
  if previous_e < e:
    print(tstr, ' ', almanac.TWILIGHTS[e], 'starts')
  else:
    print(tstr, ' ', almanac.TWILIGHTS[previous_e], 'starts')
    previous_e = e
exit()    

print("")
