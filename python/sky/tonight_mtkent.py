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

site_lat = -(27.0 + 47.0/60.0 + 52.0/3600.0)
site_long = -(151.0 + 51.0/60.0 + 19.0/3600.0)
zone = timezone('Australia/Brisbane')

# Figure out local midnight and run 2 days for Australia 
now = zone.localize(dt.datetime.now())
midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
next_midnight = midnight + dt.timedelta(days=2)

ts = load.timescale()
t0 = ts.from_datetime(midnight)
t1 = ts.from_datetime(next_midnight)
eph = load('de421.bsp')
bluffton = wgs84.latlon(site_lat * N, site_long * W)
f = almanac.dark_twilight_day(eph, bluffton)
times, events = almanac.find_discrete(t0, t1, f)

print("")
print("Twilight for Mount Kent Observatory today")
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
