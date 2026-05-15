#!/usr/local/bin/python3

import sys
import numpy as np

from plotly.offline import plot 
import plotly.express as px

matlab_flag = True
plotly_flag = True

if len(sys.argv) != 2:
  sys.exit("Usage: stellar_colors_3d.py  infile.dat")
else:
  infile = sys.argv[1]
  
stars_fp = open(infile, 'r')
stars_text = stars_fp.readlines()
i=0

# Initial arrays for data and parameters

tag = []         # Text id
mag = []         # Magnitude
gmr = []         # g-r
rmi = []         # r-i
imz = []         # i-z
tag_color = []   # Color for plotly 3D


i=0

# Read the data file and load arrays

print("  ")
print("Reading the table ", infile)
for line in stars_text:
  entry = line.strip().split()
  if len(entry) == 5:
    tag.append(entry[0])
    mag.append(float(entry[1]))
    gmr.append(float(entry[2]))
    rmi.append(float(entry[3]))
    imz.append(float(entry[4]))
  else:
    print("Short entry: ", entry)


# Database index counter

i = 0

# Number of measurements in the database

n_data = len(tag)

# Assign different colors

for star_mag in mag:
  #(20.0 - star_mag)/15.        
  tag_color.append(star_mag)
  i=i+1

n_stars = i-1

print(" ")
print("Found ", n_stars , "objects in ", infile )


# Normalize the data

for i in range(n_stars+1):
  mag[i] = mag[i]
  gmr[i] = gmr[i]
  rmi[i] = rmi[i]
  imz[i] = imz[i]  
   
print("Plotting the data")


if plotly_flag:

  print("Using plotly -- check your browser for the plot \n")
  
  
  fig = px.scatter_3d(x=gmr, y=rmi, z=imz, 
    text=tag, color=tag_color, opacity=0.8,
    title="Satellite Color-Color Relationship",
    range_x=[-2.5,2.5], range_y=[-2.5,2.5], range_z=[-2.5,2.5],
    labels={"x":"g-r","y":"r-i","z":"i-z","text":"satellite",
    "color":"magnitude"})

  fig.show()
  plot(fig, filename="geo_colors.html", auto_open=False) 

exit()
